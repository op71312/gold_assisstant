from __future__ import annotations

import argparse
import asyncio
import hmac
import json
import logging
import math
import os
import queue
import sys
import threading
import uuid
from contextlib import redirect_stdout
from datetime import date, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

ROOT = Path(os.getenv("GOLD_ASSISTANT_ROOT", Path(__file__).resolve().parents[2])).resolve()
AGENT_INFO = {
    "AI1_News_Analyst": (1, "News Analyst", "ค้นหลักฐานข่าวจาก RAG และแยกข้อเท็จจริงจากการตีความ", "#3e5f8a"),
    "AI2_Macro_Analyst": (2, "Macro Analyst", "อ่าน market snapshot และอธิบายกลไกมหภาคโดยไม่อ้างเหตุและผลเกินข้อมูล", "#3e7c5b"),
    "AI3_Quant_Regime_Analyst": (3, "Quant + Regime Analyst", "สรุปสถิติจาก feature dataset และผล Gaussian HMM", "#6d5ba6"),
    "AI4_Risk_Data_Auditor": (4, "Risk & Data Auditor", "ตรวจสอบความเสี่ยง คุณภาพข้อมูล และการกระทบยอด", "#b4690e"),
    "AI5_Lead_Researcher": (5, "Lead Researcher", "ตรวจ citation และสังเคราะห์คำตอบจากผล agent 1–4", "#0f766e"),
}
AGENT_TOOLS = {
    1: "GAIB-1 RAG evidence review",
    2: "GAIB-1 market snapshot analysis",
    3: "GAIB-1 quant + Gaussian HMM",
    4: "GAIB-1 risk and accounting audit",
    5: "GAIB-1 citation audit + synthesis",
}

_pipeline: Any | None = None
_pipeline_module: ModuleType | None = None
_initialization_lock = threading.Lock()
_active_run_lock = threading.Lock()
_event_sentinel = object()

app = FastAPI(title="Gold Assistant GAIB-1 runtime", docs_url=None, redoc_url=None)


class PipelineConfigurationError(RuntimeError):
    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__("GAIB-1 runtime configuration is incomplete")


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return _json_safe(item())
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def _sse(event: dict[str, Any]) -> str:
    payload = json.dumps(_json_safe(event), ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    return f"data: {payload}\n\n"


def _load_pipeline_module(require_remote_config: bool = True) -> ModuleType:
    os.environ["GOLD_ASSISTANT_ROOT"] = str(ROOT)
    with redirect_stdout(sys.stderr):
        from web.python import gaib_pipeline as module

    missing: list[str] = []
    if require_remote_config:
        if not module.THAILLM_API_KEYS:
            missing.append("THAILLM_API_KEY1–7")
        if not module.CF_ACCOUNT_ID:
            missing.append("CLOUDFLARE_ACCOUNT_ID")
        if not module.CF_API_TOKEN:
            missing.append("CLOUDFLARE_API_TOKEN")
        if not module.QDRANT_URL:
            missing.append("QDRANT_URL")
        if not module.QDRANT_API_KEY:
            missing.append("QDRANT_API_KEY")
        if not module.JINA_API_KEYS:
            missing.append("JINA_API_KEY, JINA_API_KEY2, JINA_API_KEY3, or JINA_API_KEY4")
    for symbol in ("FEATURE_PATH", "HMM_PATH", "CHUNKS_PATH"):
        artifact = getattr(module, symbol, None)
        if not artifact or not Path(artifact).is_file():
            missing.append(symbol)
    if missing:
        raise PipelineConfigurationError(missing)
    return module


def _get_pipeline(progress_callback=None) -> tuple[Any, ModuleType]:
    global _pipeline, _pipeline_module
    if _pipeline is not None and _pipeline_module is not None:
        if progress_callback:
            progress_callback("runtime", "success", "Python pipeline พร้อมใช้งาน; กำลังเริ่มคำถามใหม่")
        return _pipeline, _pipeline_module
    with _initialization_lock:
        if _pipeline is not None and _pipeline_module is not None:
            if progress_callback:
                progress_callback("runtime", "success", "Python pipeline พร้อมใช้งาน; กำลังเริ่มคำถามใหม่")
            return _pipeline, _pipeline_module
        if progress_callback:
            progress_callback("runtime", "running", "กำลังโหลด Python modules และตรวจสอบการตั้งค่า")
        try:
            module = _load_pipeline_module()
        except PipelineConfigurationError as error:
            if progress_callback:
                progress_callback("runtime", "error", f"ยังตั้งค่า runtime ไม่ครบ: {', '.join(error.missing)}")
            raise
        try:
            pipeline = module.GoldAssistantMultiAgent(progress_callback=progress_callback)
        except Exception as error:
            if progress_callback:
                progress_callback("runtime", "error", f"เริ่ม Python runtime ไม่สำเร็จ ({type(error).__name__})")
            logging.error("GAIB-1 initialization failed (%s)", type(error).__name__)
            raise RuntimeError("The Python pipeline could not connect to its required remote services") from error
        _pipeline_module = module
        _pipeline = pipeline
        if progress_callback:
            progress_callback("runtime", "success", "เตรียม GAIB-1 runtime และบริการ RAG สำเร็จ")
        return pipeline, module


def _first_text(data: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            for item in value.values():
                if isinstance(item, str) and item.strip():
                    return item.strip()
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
                if isinstance(item, dict):
                    for child in item.values():
                        if isinstance(child, str) and child.strip():
                            return child.strip()
    return ""


def _key_finding(agent_name: str, data: dict[str, Any], success: bool) -> str:
    if not success:
        return "Agent นี้ไม่สามารถส่งผลลัพธ์ที่ผ่านการตรวจสอบได้ในรอบนี้"
    if agent_name == "AI1_News_Analyst":
        return _first_text(data, "reported_fact", "concise_summary") or "ไม่พบข้อเท็จจริงจากข่าวที่ยืนยันได้"
    if agent_name == "AI2_Macro_Analyst":
        return _first_text(data, "non_causal_caveat", "macro_channels", "observed_market_facts") or "ไม่มีข้อสรุปมหภาคที่ยืนยันได้"
    if agent_name == "AI3_Quant_Regime_Analyst":
        return _first_text(data, "hmm_interpretation", "quantified_findings", "statistics") or "ไม่มีข้อสรุปเชิงปริมาณที่ยืนยันได้"
    if agent_name == "AI4_Risk_Data_Auditor":
        finding = _first_text(data, "accounting_assessment", "critical_risks", "synthetic_data_caveat")
        status = data.get("go_no_go")
        return f"{status}: {finding}" if status and finding else finding or "ไม่มีข้อสรุปด้านความเสี่ยงที่ยืนยันได้"
    return _first_text(data, "executive_summary") or "Lead Researcher งดสรุปข้อกล่าวอ้างที่ไม่มีหลักฐานรองรับ"


def _evidence_ids(module: ModuleType, data: dict[str, Any]) -> list[str]:
    collect = getattr(module, "_collect_evidence_ids", None)
    if not callable(collect):
        return []
    try:
        return sorted(str(item) for item in collect(data))
    except Exception:
        return []


def _agent_events(module: ModuleType, agent_name: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = AGENT_INFO.get(agent_name)
    if metadata is None:
        return []
    agent_id, name, role, color = metadata
    raw_data = result.get("data") if isinstance(result.get("data"), dict) else {}
    data = {key: value for key, value in raw_data.items() if key != "error"}
    metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
    status = str(result.get("status", "error"))
    success = status in {"success", "recovered"} and result.get("schema_valid") is True
    evidence = _evidence_ids(module, data)
    latency = metrics.get("latency_ms")
    summary = (
        f"สถานะ {status} · JSON {'ผ่าน' if result.get('json_valid') else 'ไม่ผ่าน'}"
        f" · schema {'ผ่าน' if result.get('schema_valid') else 'ไม่ผ่าน'}"
        f" · หลักฐาน {len(evidence)} รายการ"
    )
    if isinstance(latency, (int, float)):
        summary += f" · {latency:.0f} ms"
    provider_hint = metrics.get("provider_error_hint")
    provider_status = metrics.get("provider_http_status")
    if provider_status:
        summary += f" · ThaiLLM HTTP {provider_status}"
    if provider_hint:
        summary += f" · {provider_hint}"
    recovery_strategy = metrics.get("citation_recovery_strategy")
    if recovery_strategy:
        summary += f" · citation fallback: {recovery_strategy}"
    data["_gaib"] = {
        "status": status,
        "jsonValid": bool(result.get("json_valid")),
        "schemaValid": bool(result.get("schema_valid")),
        "errorType": metrics.get("error_type"),
        "latencyMs": latency,
        "attempts": metrics.get("api_attempt_count", metrics.get("attempt_count", metrics.get("attempts"))),
        "providerHttpStatus": provider_status,
        "providerErrorHint": provider_hint,
        "evidenceIds": evidence,
    }
    return [
        {"type": "tool_call", "agentId": agent_id, "tool": AGENT_TOOLS[agent_id]},
        {
            "type": "tool_result",
            "agentId": agent_id,
            "tool": AGENT_TOOLS[agent_id],
            "summary": summary,
            "data": _json_safe(data),
        },
        {
            "type": "agent_done",
            "agentId": agent_id,
            "keyFinding": _key_finding(agent_name, raw_data, success),
            "evidence": evidence,
            "narrationMode": "gaib-python",
            "status": "done" if success else "error",
        },
    ]


def _agent_start_event(agent_name: str) -> dict[str, Any]:
    agent_id, name, role, color = AGENT_INFO[agent_name]
    return {"type": "agent_start", "agentId": agent_id, "name": name, "role": role, "color": color}


def _compact_records(records: Any, limit: int = 20) -> list[dict[str, Any]]:
    if not isinstance(records, list):
        return []
    return [_json_safe(record) for record in records[:limit] if isinstance(record, dict)]


def _pipeline_summary(result: dict[str, Any]) -> dict[str, Any]:
    retrieval = result.get("retrieval") if isinstance(result.get("retrieval"), dict) else {}
    market = result.get("market") if isinstance(result.get("market"), dict) else {}
    hmm = result.get("hmm") if isinstance(result.get("hmm"), dict) else {}
    risk = result.get("risk") if isinstance(result.get("risk"), dict) else {}
    metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
    retrieval_metrics = retrieval.get("metrics") if isinstance(retrieval.get("metrics"), dict) else {}
    sources = result.get("sources") if isinstance(result.get("sources"), list) else []
    safe_sources = []
    for source in sources[:12]:
        if not isinstance(source, dict):
            continue
        safe_sources.append({
            "citation_id": source.get("citation_id") or source.get("evidence_id"),
            "title": source.get("title"),
            "source": source.get("source") or source.get("source_file"),
            "publication_date": source.get("publication_date"),
            "report_period": source.get("report_period"),
            "url": source.get("url"),
            "text_excerpt": source.get("text_excerpt"),
        })
    retrieval_keys = (
        "retrieval_status", "raw_candidate_count", "candidate_count", "reranked_count",
        "final_k", "dense_candidate_count", "bm25_candidate_count", "hybrid_candidate_count",
        "embedding_ms", "qdrant_ms", "bm25_ms", "rrf_ms", "rerank_ms", "jina_ms",
    )
    metric_keys = (
        "retrieval_backend", "total_wall_ms", "agent_count", "api_success_rate",
        "json_parse_rate", "schema_valid_rate", "total_tokens", "mean_agent_latency_ms",
        "max_agent_latency_ms", "source_count", "valid_evidence_id_count",
    )
    return _json_safe({
        "retrieval": {
            "backend": retrieval.get("backend"),
            "metrics": {key: retrieval_metrics[key] for key in retrieval_keys if key in retrieval_metrics},
            "sources": safe_sources,
        },
        "market": {
            "as_of": market.get("as_of"),
            "summary": market.get("summary"),
            "records": _compact_records(market.get("records")),
        },
        "hmm": {
            key: hmm.get(key)
            for key in (
                "status", "model_name", "as_of", "latest_state", "latest_state_confidence",
                "n_observations", "state_counts", "warnings", "retrospective_only", "records",
            )
            if key in hmm
        },
        "risk": {
            "status": risk.get("status"),
            "records": _compact_records(risk.get("records")),
        },
        "citationAudit": result.get("citation_audit"),
        "metrics": {key: metrics[key] for key in metric_keys if key in metrics},
    })


def _run_with_events(
    pipeline: Any,
    module: ModuleType,
    question: str,
    events: queue.Queue,
) -> dict[str, Any]:
    original_retrieve = pipeline.evidence.retrieve
    original_specialists = pipeline._run_specialists
    lead_agent = module.agent5
    original_lead_run = lead_agent.run

    def tracked_retrieve(*args: Any, **kwargs: Any) -> Any:
        events.put({
            "type": "analysis_notice",
            "message": "กำลังดึงหลักฐานจาก corpus ผ่าน Cloudflare embeddings, Qdrant hybrid search (BM25/RRF) และ Jina reranking",
        })
        return original_retrieve(*args, **kwargs)

    def tracked_specialists(query: str, sources: Any, market: Any, hmm: Any, risk: Any, telemetry_callback: Any = None) -> Any:
        for agent_name in list(AGENT_INFO)[:4]:
            events.put(_agent_start_event(agent_name))

        def on_result(agent_name: str, agent_result: dict[str, Any]) -> None:
            for event in _agent_events(module, agent_name, agent_result):
                events.put(event)
            if telemetry_callback:
                telemetry_callback(agent_name, agent_result)

        return original_specialists(query, sources, market, hmm, risk, on_result)

    def tracked_lead_run(*args: Any, **kwargs: Any) -> Any:
        events.put(_agent_start_event("AI5_Lead_Researcher"))
        try:
            result = original_lead_run(*args, **kwargs)
        except Exception as error:
            failed_result = {
                "status": "error",
                "schema_valid": False,
                "data": {},
                "metrics": {"error_type": type(error).__name__},
            }
            for event in _agent_events(module, "AI5_Lead_Researcher", failed_result):
                events.put(event)
            raise
        for event in _agent_events(module, "AI5_Lead_Researcher", result):
            events.put(event)
        return result

    def report_progress(step: str, status: str, message: str) -> None:
        events.put({
            "type": "pipeline_progress",
            "step": step,
            "status": status,
            "message": message,
        })

    pipeline.evidence.retrieve = tracked_retrieve
    pipeline._run_specialists = tracked_specialists
    lead_agent.run = tracked_lead_run
    try:
        return pipeline.run(question, progress_callback=report_progress)
    finally:
        pipeline.evidence.retrieve = original_retrieve
        pipeline._run_specialists = original_specialists
        lead_agent.run = original_lead_run


def _missing_runtime_config() -> list[str]:
    missing = []
    for key in ("GAIB_SERVICE_TOKEN",):
        if not os.getenv(key, "").strip():
            missing.append(key)
    return missing


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "runtime": "GAIB-1 Python",
        "serviceAuthConfigured": not _missing_runtime_config(),
        "externalRetrievalRequired": True,
    }


@app.post("/api/agents")
async def post_agents(request: Request) -> StreamingResponse:
    expected_token = os.getenv("GAIB_SERVICE_TOKEN", "").strip()
    provided_token = request.headers.get("authorization", "")
    if not expected_token:
        raise HTTPException(status_code=503, detail="GAIB_SERVICE_TOKEN is not configured on the Python runtime")
    if not hmac.compare_digest(provided_token, f"Bearer {expected_token}"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        body = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Invalid JSON request body") from None
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be an object")
    question = body.get("question")
    if not isinstance(question, str) or not question.strip():
        raise HTTPException(status_code=400, detail="กรุณาพิมพ์คำถาม")
    question = question.strip()
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="คำถามยาวเกิน 500 ตัวอักษร")
    if not _active_run_lock.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="GAIB-1 กำลังประมวลผลคำถามอื่นอยู่ กรุณารอสักครู่แล้วลองใหม่")

    run_id = str(uuid.uuid4())
    events: queue.Queue = queue.Queue()
    holder: dict[str, Any] = {"run_task": None, "lock_released": False}

    def release_run_lock() -> None:
        if not holder["lock_released"]:
            holder["lock_released"] = True
            _active_run_lock.release()

    async def stream_events():
        yield _sse({"type": "run_start", "question": question, "scenario": "GAIB-1 Python", "runId": run_id})
        yield _sse({"type": "analysis_mode", "mode": "connecting"})
        yield _sse({
            "type": "analysis_notice",
            "message": "กำลังเตรียม GAIB-1 Python modules: โหลด feature/HMM/risk artifacts และเชื่อมต่อบริการ RAG ภายนอก",
        })

        try:
            initialization = asyncio.create_task(
                asyncio.to_thread(_get_pipeline, lambda step, status, message: events.put({
                    "type": "pipeline_progress",
                    "step": step,
                    "status": status,
                    "message": message,
                }))
            )
            while not initialization.done():
                try:
                    event = await asyncio.wait_for(asyncio.to_thread(events.get, True, 1), timeout=2)
                    if event is not _event_sentinel:
                        yield _sse(event)
                except asyncio.TimeoutError:
                    if not initialization.done():
                        yield ": keep-alive\n\n"
                except queue.Empty:
                    if not initialization.done():
                        yield ": keep-alive\n\n"
            while True:
                try:
                    event = events.get_nowait()
                except queue.Empty:
                    break
                if event is not _event_sentinel:
                    yield _sse(event)
            pipeline, module = initialization.result()
            yield _sse({"type": "analysis_mode", "mode": "gaib-python"})
            yield _sse({
                "type": "analysis_notice",
                "message": "ใช้ GAIB-1 Python pipeline: RAG → market snapshot → Gaussian HMM/risk audit → agents 1–4 → citation-checked Lead Researcher. ไม่มีคำตอบ fallback",
            })

            async def run_pipeline() -> None:
                try:
                    result = await asyncio.to_thread(_run_with_events, pipeline, module, question, events)
                    events.put({"type": "pipeline_summary", "summary": _pipeline_summary(result)})
                    agents = result.get("agents") if isinstance(result.get("agents"), dict) else {}
                    lead = agents.get("AI5_Lead_Researcher") if isinstance(agents.get("AI5_Lead_Researcher"), dict) else {}
                    if lead.get("status") in {"success", "recovered"} and result.get("final_text"):
                        events.put({"type": "final_answer", "text": result["final_text"], "agentId": 5})
                    else:
                        metrics = lead.get("metrics") if isinstance(lead.get("metrics"), dict) else {}
                        hint = metrics.get("provider_error_hint")
                        message = "GAIB-1 ยังสร้างรายงานที่ผ่านการตรวจสอบไม่ได้"
                        if hint:
                            message += f": {hint}"
                        elif metrics.get("provider_http_status"):
                            message += f" (ThaiLLM HTTP {metrics['provider_http_status']})"
                        events.put({"type": "pipeline_error", "message": message})
                    events.put({"type": "done"})
                except Exception as error:
                    logging.error("GAIB-1 request failed (%s)", type(error).__name__)
                    events.put({
                        "type": "pipeline_error",
                        "message": (
                            "GAIB-1 ทำคำถามนี้ไม่สำเร็จ ตรวจสอบการเชื่อมต่อ ThaiLLM, Qdrant, Cloudflare และ Jina "
                            f"(ชนิดข้อผิดพลาด: {type(error).__name__}) ไม่มีการใช้ fallback"
                        ),
                    })
                    events.put({"type": "done"})
                finally:
                    events.put(_event_sentinel)

            run_task = asyncio.create_task(run_pipeline())
            holder["run_task"] = run_task
            while True:
                try:
                    event = await asyncio.to_thread(events.get, True, 12)
                except queue.Empty:
                    yield ": keep-alive\n\n"
                    continue
                if event is _event_sentinel:
                    break
                yield _sse(event)
            await run_task
        except PipelineConfigurationError as error:
            logging.error("GAIB-1 configuration missing: %s", ", ".join(error.missing))
            yield _sse({
                "type": "pipeline_error",
                "message": f"GAIB-1 ยังไม่พร้อม: ต้องมี {', '.join(error.missing)} และ Python modules/artifacts ที่จำเป็น",
            })
            yield _sse({"type": "done"})
        except Exception as error:
            logging.error("GAIB-1 runtime unavailable (%s)", type(error).__name__)
            yield _sse({
                "type": "pipeline_error",
                "message": (
                    "เริ่ม GAIB-1 ไม่สำเร็จ ตรวจสอบ secrets, Python modules/artifacts และการเชื่อมต่อ Qdrant/Cloudflare/Jina "
                    f"(ชนิดข้อผิดพลาด: {type(error).__name__}) ไม่มีการใช้ fallback"
                ),
            })
            yield _sse({"type": "done"})
        finally:
            task = holder["run_task"]
            if task is not None and not task.done():
                task.add_done_callback(lambda _: release_run_lock())
            else:
                release_run_lock()

    return StreamingResponse(
        stream_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )


def _self_check() -> int:
    module = _load_pipeline_module(require_remote_config=False)
    features = module.df_features
    if features is None or features.empty:
        raise RuntimeError("The feature dataset is empty")
    query = "ทดสอบสถานะทองคำ 2026-10-13"
    market = module.build_market_snapshot(query, features)
    hmm = module.run_hmm_snapshot(query, features, module.HMM_PATH)
    risk = module.get_risk_snapshot_global()
    summary = {
        "pipelineModule": "web.python.gaib_pipeline",
        "featureRows": int(len(features)),
        "featureAsOf": market.get("as_of"),
        "hmmStatus": hmm.get("status"),
        "riskRecords": len(risk.get("records", [])),
        "chunkCorpusExists": Path(module.CHUNKS_PATH).is_file(),
    }
    print(json.dumps(_json_safe(summary), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-check", action="store_true")
    arguments = parser.parse_args()
    if arguments.self_check:
        raise SystemExit(_self_check())
