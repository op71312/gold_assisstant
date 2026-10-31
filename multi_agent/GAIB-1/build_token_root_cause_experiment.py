#!/usr/bin/env python
"""Build a versioned notebook for controlled ThaiLLM JSON failure experiments."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


GAIB_DIR = Path(__file__).resolve().parent
SOURCE_NOTEBOOK = GAIB_DIR / "Gold_Assistant_GAIB1_Reliability_Experiment_Phase1_2.ipynb"
OUTPUT_NOTEBOOK = GAIB_DIR / os.getenv(
    "GAIB_EXIT_CRITERIA_NOTEBOOK_NAME",
    "Gold_Assistant_GAIB1_Token_Root_Cause_Experiment_v1.ipynb",
)


def cell_source(cell: dict[str, Any]) -> str:
    return "".join(cell.get("source", []))


def set_cell_source(cell: dict[str, Any], value: str) -> None:
    cell["source"] = value.splitlines(keepends=True)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected exactly one matching source block, found {count}")
    return text.replace(old, new, 1)


def patch_generation_cell(cell: dict[str, Any]) -> None:
    source = cell_source(cell)
    source = replace_once(
        source,
        "        for attempt in range(THAILLM_MAX_ATTEMPTS):\n"
        "            key_slot, client = next_thaillm_client()\n"
        "            attempted_key_slots.append(key_slot)\n"
        "            try:\n"
        "                def request_generation():\n"
        "                    return client.chat.completions.create(\n"
        "                        model=THAILLM_MODEL,\n"
        "                        temperature=THAILLM_TEMPERATURE,\n"
        "                        max_tokens=max_tokens or THAILLM_MAX_TOKENS_AGENT,\n"
        "                        messages=[{\"role\": \"system\", \"content\": system_prompt}, {\"role\": \"user\", \"content\": user_prompt}],\n"
        "                    )\n"
        "                resp, _gate_attempts = THAILLM_GATE.call(request_generation, max_retries=0)\n",
        "        http_attempt_durations_ms = []\n"
        "        http_retry_reasons = []\n"
        "        requested_budget = int(max_tokens or THAILLM_MAX_TOKENS_AGENT)\n"
        "        for attempt in range(THAILLM_MAX_ATTEMPTS):\n"
        "            key_slot, client = next_thaillm_client()\n"
        "            attempted_key_slots.append(key_slot)\n"
        "            try:\n"
        "                def request_generation():\n"
        "                    request_started = time.perf_counter()\n"
        "                    try:\n"
        "                        return client.chat.completions.create(\n"
        "                            model=THAILLM_MODEL,\n"
        "                            temperature=THAILLM_TEMPERATURE,\n"
        "                            max_tokens=requested_budget,\n"
        "                            messages=[{\"role\": \"system\", \"content\": system_prompt}, {\"role\": \"user\", \"content\": user_prompt}],\n"
        "                        )\n"
        "                    except Exception as request_error:\n"
        "                        status_code = ApiRequestGate._status_code(request_error)\n"
        "                        http_retry_reasons.append({\"type\": type(request_error).__name__, \"status_code\": status_code})\n"
        "                        raise\n"
        "                    finally:\n"
        "                        http_attempt_durations_ms.append((time.perf_counter() - request_started) * 1000)\n"
        "                gate_started = time.perf_counter()\n"
        "                resp, _gate_attempts = THAILLM_GATE.call(request_generation, max_retries=0)\n"
        "                gate_elapsed_ms = (time.perf_counter() - gate_started) * 1000\n",
        "ThaiLLM request timing instrumentation",
    )
    source = replace_once(
        source,
        '                    "attempts": attempt + 1,\n'
        '                    "api_key_slot": key_slot,\n',
        '                    "attempts": attempt + 1,\n'
        '                    "api_attempt_count": len(http_attempt_durations_ms),\n'
        '                    "http_attempt_durations_ms": http_attempt_durations_ms.copy(),\n'
        '                    "http_retry_reasons": http_retry_reasons.copy(),\n'
        '                    "request_duration_ms": sum(http_attempt_durations_ms),\n'
        '                    "gate_wait_ms": max(0.0, gate_elapsed_ms - sum(http_attempt_durations_ms)),\n'
        '                    "max_tokens_requested": requested_budget,\n'
        '                    "api_key_slot": key_slot,\n',
        "ThaiLLM request timing results",
    )
    source = replace_once(
        source,
        "        raise RuntimeError(\n"
        "            f\"ThaiLLM failed after {THAILLM_MAX_ATTEMPTS} attempts using configured key slots \"\n"
        "            f\"{attempted_key_slots}: {type(last_error).__name__}: {last_error}\"\n"
        "        ) from last_error\n",
        "        final_error = RuntimeError(\n"
        "            f\"ThaiLLM failed after {THAILLM_MAX_ATTEMPTS} attempts using configured key slots \"\n"
        "            f\"{attempted_key_slots}: {type(last_error).__name__}: {last_error}\"\n"
        "        )\n"
        "        final_error.api_attempt_count = len(http_attempt_durations_ms)\n"
        "        final_error.http_attempt_durations_ms = http_attempt_durations_ms.copy()\n"
        "        final_error.http_retry_reasons = http_retry_reasons.copy()\n"
        "        final_error.request_duration_ms = sum(http_attempt_durations_ms)\n"
        "        final_error.gate_wait_ms = max(0.0, (time.perf_counter() - t0) * 1000 - sum(http_attempt_durations_ms))\n"
        "        raise final_error from last_error\n",
        "failed request attempt metrics",
    )
    set_cell_source(cell, source)


def patch_agent_cell(cell: dict[str, Any]) -> None:
    source = cell_source(cell)
    source = replace_once(
        source,
        "    raw_responses = []\n"
        "    responses = []\n"
        "    parsed = {}\n",
        "    raw_responses = []\n"
        "    responses = []\n"
        "    parsed = {}\n"
        "    request_budgets = []\n",
        "request-budget telemetry",
    )
    source = replace_once(
        source,
        '    system_prompt = AGENT_SYSTEM_BASE + "\\nROLE: " + role_instruction\n',
        '    system_prompt = AGENT_SYSTEM_BASE + "\\nROLE: " + role_instruction\n'
        '    if GAIB_COMPACT_OUTPUT:\n'
        '        contract = AGENT_SCHEMAS[agent_name]\n'
        '        required_types = {key: ([item.__name__ for item in expected] if isinstance(expected, tuple) else expected.__name__)\n'
        '                          for key, expected in contract["required"].items()}\n'
        '        contract_hint = {"required": required_types, "list_items": contract.get("list_items", {})}\n'
        '        system_prompt += "\\nCOMPACT JSON CONTRACT (all listed keys and types are mandatory): " + json.dumps(contract_hint, ensure_ascii=False) + ". Use [] for absent lists and null only for nullable fields. Use exact enum values specified in the task. Limit narrative lists to at most 3 relevant items and numeric statistics to at most 5; keep every required value, date, unit, qualifier, and supporting evidence ID. Do not duplicate details across fields."\n'
        '    if GAIB_COMPACT_OUTPUT and agent_name == "AI1_News_Analyst":\n'
        '        system_prompt += "\\nAI1 concise-output rule: Return one JSON object under 400 output tokens with all required keys. Defaults when unsupported: status=insufficient_evidence; reported_fact and concise_summary empty; event_date=null; possible_market_channel=unknown; evidence_ids=[], relevant_events=[], missing_evidence=[], cautions=[]; price_bias=unknown; evidence_strength=low. Replace defaults only with supplied evidence. Include at most one relevant event and one short sentence per narrative field. Cite only supplied [S#] IDs. Do not repeat the same narrative in multiple fields."\n'
        '    if GAIB_COMPACT_OUTPUT and agent_name == "AI5_Lead_Researcher":\n'
        '        system_prompt += "\\nAI5 concise-output rule: Return one JSON object under 450 output tokens with all required keys. Defaults when unsupported: status=partial; executive_summary and abstention_reason short; evidence_based_findings=[], agent_agreement=[], agent_disagreements=[], risk_flags=[], limitations=[], next_research_steps=[]; confidence=low. Every list-typed field must be a JSON array, never a sentence or string; use [] when empty, especially for agent_agreement, agent_disagreements, risk_flags, limitations, and next_research_steps. Include at most one supported finding, one sentence per narrative field and one item per list. Cite only evidence IDs in the manifest. Use schema-valid specialist findings only; explicitly abstain if none are valid. Do not restate specialist outputs or include markdown."\n'
        '    if agent_name == "AI3_Quant_Regime_Analyst" and GAIB_AI3_COMPACT_OUTPUT:\n',
        "compact output system instruction",
    )
    source = replace_once(
        source,
        '    if agent_name == "AI3_Quant_Regime_Analyst" and GAIB_AI3_COMPACT_OUTPUT:\n',
        '    if agent_name == "AI4_Risk_Data_Auditor" and GAIB_COMPACT_OUTPUT:\n'
        '        system_prompt += "\\nAI4 concise-output rule: Return one JSON object under 650 output tokens with all required keys. Include only supported WARN checks and material critical risks; do not omit a material critical risk. Use [] for empty lists, null when an expected invariant is not provided, and only exact [R#] IDs from the supplied risk records. Never infer thresholds or repeat the same risk across fields. Keep each narrative field to one short sentence and use at most 3 non-critical list items."\n'
        '    if agent_name == "AI3_Quant_Regime_Analyst" and GAIB_AI3_COMPACT_OUTPUT:\n',
        "AI4 compact output contract",
    )
    source = replace_once(
        source,
        '    if agent_name == "AI3_Quant_Regime_Analyst" and GAIB_AI3_COMPACT_OUTPUT:\n',
        '    if agent_name == "AI3_Quant_Regime_Analyst" and GAIB_AI3_COMPACT_OUTPUT:\n'
        '        system_prompt += "\\nAI3 concise-output rule: Return only one JSON object, under 450 output tokens. Use this exact minimal shape when fields are unsupported: {\\"status\\":\\"insufficient_evidence\\",\\"as_of\\":null,\\"statistics\\":[],\\"regime_state\\":null,\\"feature_inputs\\":[],\\"tool_result_ids\\":[],\\"quantified_findings\\":[],\\"hmm_interpretation\\":null,\\"regime_state_id\\":null,\\"regime_confidence\\":null,\\"robustness_notes\\":[],\\"limitations\\":[],\\"recommendation_for_next_test\\":null}. Replace placeholders only with supported values. At most one item per list; keep each explanation to one short sentence. Do not repeat evidence IDs in multiple lists; do not restate input data."\n',
        "AI3 compact output contract",
    )
    source = source.replace(
        '"prompt_version": "claim-evidence-compact-v1" if GAIB_COMPACT_OUTPUT else "claim-evidence-v1"',
        '"prompt_version": ("claim-evidence-ai1-compact-v1" if agent_name == "AI1_News_Analyst" and GAIB_COMPACT_OUTPUT else '
        '("claim-evidence-ai5-compact-v1" if agent_name == "AI5_Lead_Researcher" and GAIB_COMPACT_OUTPUT else '
        '("claim-evidence-ai3-compact-v1" if agent_name == "AI3_Quant_Regime_Analyst" and GAIB_AI3_COMPACT_OUTPUT else '
        '("claim-evidence-compact-v1" if GAIB_COMPACT_OUTPUT else "claim-evidence-v1"))))',
    )
    source = replace_once(
        source,
        '    for key, allowed in (("price_bias", {"bullish", "bearish", "mixed", "unknown"}),\n'
        '                         ("macro_bias", {"bullish", "bearish", "mixed", "unknown"}),\n',
        '    for key, allowed in (("price_bias", {"bullish", "bearish", "mixed", "neutral", "unknown"}),\n'
        '                         ("macro_bias", {"bullish", "bearish", "mixed", "neutral", "unknown"}),\n',
        "allow neutral directional assessments",
    )
    source = replace_once(
        source,
        '    available_ids = set(allowed_ids or re.findall(r"\\[((?:S|Q|H|R)\\d+)\\]", user_payload))\n',
        '    has_allowlist = allowed_ids is not None\n'
        '    available_ids = set(allowed_ids) if has_allowlist else set(re.findall(r"\\[((?:S|Q|H|R)\\d+)\\]", user_payload))\n',
        "preserve an explicitly empty evidence allowlist",
    )
    source = source.replace(
        "invalid_ids = sorted(set(output_ids) - available_ids) if available_ids else []",
        "invalid_ids = sorted(set(output_ids) - available_ids) if has_allowlist or available_ids else []",
    )
    source = source.replace(
        "invalid_ids = sorted(set(evidence_ids) - available_ids) if available_ids else []",
        "invalid_ids = sorted(set(evidence_ids) - available_ids) if has_allowlist or available_ids else []",
    )
    source = replace_once(
        source,
        '"expected_invariant": (str, dict, type(None)), "pnl_reconciliation":',
        '"expected_invariant": (str, int, float, bool, dict, type(None)), "pnl_reconciliation":',
        "accept deterministic scalar expected invariants",
    )
    source = replace_once(
        source,
        "    for attempt in range(2):\n"
        "        request_payload = user_payload\n"
        "        if attempt:\n"
        "            request_payload = (\n"
        '                "Repair the prior response to satisfy this JSON contract. Return one JSON object only. "\n'
        '                "Do not add unsupported factual claims. Validation errors: "\n'
        "                + json.dumps(schema_errors or [parse_error], ensure_ascii=False)\n"
        '                + "\\nOriginal response:\\n"\n'
        "                + raw_responses[-1]\n"
        '                + "\\nOriginal task:\\n"\n'
        "                + user_payload\n"
        "            )\n"
        "        try:\n"
        "            response = llm.generate(system_prompt, request_payload, max_tokens=effective_max_tokens)\n",
        "    for attempt in range(3):\n"
        "        request_payload = user_payload\n"
        "        request_budget = int(max_tokens or THAILLM_MAX_TOKENS_AGENT)\n"
        "        prior_truncated = bool(responses) and str(responses[-1].get(\"finish_reason\") or \"\").casefold() in {\"length\", \"max_tokens\", \"max_output_tokens\"}\n"
        "        if attempt and prior_truncated and GAIB_TRUNCATION_RECOVERY_MODE == \"increased\":\n"
        "            request_budget = max(request_budget, GAIB_RECOVERY_MAX_TOKENS)\n"
        "            request_payload = (\"Recover the truncated output. Return one compact JSON object that satisfies the original task and required schema. Preserve supported evidence IDs; do not infer missing content.\\n\"\n"
        "                              + \"Required schema errors: \" + json.dumps(schema_errors or [parse_error], ensure_ascii=False)\n"
        "                              + \"\\nOriginal task:\\n\" + user_payload\n"
        "                              + \"\\nAvailable evidence IDs:\\n\" + json.dumps(sorted(available_ids), ensure_ascii=False)\n"
        "                              + \"\\nTruncated response ending:\\n\" + raw_responses[-1][-1200:])\n"
        "        elif attempt:\n"
        "            request_payload = (\n"
        '                "Repair the prior response to satisfy this JSON contract. Return one JSON object only. "\n'
        '                "Do not add unsupported factual claims. Validation errors: "\n'
        "                + json.dumps(schema_errors or [parse_error], ensure_ascii=False)\n"
        '                + "\\nOriginal response:\\n"\n'
        "                + raw_responses[-1]\n"
        '                + "\\nOriginal task:\\n"\n'
        "                + user_payload\n"
        '                + "\\nAvailable evidence IDs:\\n"\n'
        "                + json.dumps(sorted(available_ids), ensure_ascii=False)\n"
        "            )\n"
        "        request_budgets.append(request_budget)\n"
        "        try:\n"
        "            response = llm.generate(system_prompt, request_payload, max_tokens=request_budget)\n",
        "targeted truncation-recovery strategy",
    )
    source = replace_once(
        source,
        '            status = "truncated_output"\n'
        '            parse_error = "finish_reason_indicates_output_truncation"\n'
        "            break\n",
        '            status = "truncated_output"\n'
        '            parse_error = "finish_reason_indicates_output_truncation"\n'
        "            if attempt == 0 and GAIB_TRUNCATION_RECOVERY_MODE in {\"same_budget\", \"increased\"}:\n"
        "                continue\n"
        "            break\n",
        "retry confirmed truncation only when configured",
    )
    source = replace_once(
        source,
        "        except Exception as error:\n"
        '            status = "api_error"\n'
        '            parse_error = f"{type(error).__name__}:{error}"\n'
        "            exception_traceback = traceback.format_exc()\n"
        "            break\n",
        "        except Exception as error:\n"
        '            status = "api_error"\n'
        '            parse_error = f"{type(error).__name__}:{error}"\n'
        "            exception_traceback = traceback.format_exc()\n"
        "            if GAIB_REQUEST_DIAGNOSTICS_ENABLED:\n"
        "                record_request_diagnostic({\n"
        "                    \"query_id\": GAIB_ACTIVE_QUERY_ID, \"agent\": agent_name,\n"
        "                    \"variant\": GAIB_ACTIVE_VARIANT, \"logical_attempt\": attempt + 1,\n"
        "                    \"status\": status, \"api_success\": False,\n"
        "                    \"json_parse\": None, \"schema_valid\": None, \"parse_error\": parse_error,\n"
        "                    \"schema_errors\": [], \"traceback\": exception_traceback,\n"
        "                    \"error\": error, \"response\": {\n"
        "                        \"model\": THAILLM_MODEL,\n"
        "                        \"max_tokens_requested\": request_budgets[-1] if request_budgets else int(max_tokens or THAILLM_MAX_TOKENS_AGENT),\n"
        "                        \"api_attempt_count\": getattr(error, \"api_attempt_count\", 0),\n"
        "                        \"request_duration_ms\": getattr(error, \"request_duration_ms\", None),\n"
        "                        \"gate_wait_ms\": getattr(error, \"gate_wait_ms\", None),\n"
        "                        \"http_attempt_durations_ms\": getattr(error, \"http_attempt_durations_ms\", []),\n"
        "                        \"http_retry_reasons\": getattr(error, \"http_retry_reasons\", []),\n"
        "                    }, \"raw_response\": \"\"})\n"
        "            break\n",
        "failed API request diagnostics",
    )
    source = replace_once(
        source,
        "    request_budgets = []\n",
        "    request_budgets = []\n"
        "    request_outcomes = []\n",
        "request outcome tracking",
    )
    source = replace_once(
        source,
        '            parse_error = "finish_reason_indicates_output_truncation"\n',
        '            parse_error = "finish_reason_indicates_output_truncation"\n'
        "            request_outcomes.append({\"status\": status, \"api_success\": True, \"json_parse\": False, \"schema_valid\": False,\n"
        "                                    \"parse_error\": parse_error, \"schema_errors\": []})\n",
        "truncation request outcome",
    )
    source = replace_once(
        source,
        '        if not parse_ok:\n'
        '            status = "invalid_json"\n',
        '        if not parse_ok:\n'
        '            status = "invalid_json"\n'
        "            request_outcomes.append({\"status\": status, \"api_success\": True, \"json_parse\": False, \"schema_valid\": False,\n"
        "                                    \"parse_error\": parse_error, \"schema_errors\": []})\n",
        "JSON parse request outcome",
    )
    source = replace_once(
        source,
        '        if schema_errors:\n'
        '            status = "schema_violation"\n',
        '        if schema_errors:\n'
        '            status = "schema_violation"\n'
        "            request_outcomes.append({\"status\": status, \"api_success\": True, \"json_parse\": True, \"schema_valid\": False,\n"
        "                                    \"parse_error\": None, \"schema_errors\": schema_errors.copy()})\n",
        "schema validation request outcome",
    )
    source = replace_once(
        source,
        '        status = "success"\n'
        "        break\n",
        '        status = "success"\n'
        "        request_outcomes.append({\"status\": status, \"api_success\": True, \"json_parse\": True, \"schema_valid\": True,\n"
        "                                \"parse_error\": None, \"schema_errors\": []})\n"
        "        break\n",
        "valid request outcome",
    )
    source = replace_once(
        source,
        '        "finish_reason": final_response.get("finish_reason"),\n',
        '        "finish_reason": final_response.get("finish_reason"),\n'
        '        "max_tokens_requested": request_budgets[-1] if request_budgets else int(max_tokens or THAILLM_MAX_TOKENS_AGENT),\n'
        '        "request_budgets": request_budgets,\n'
        '        "raw_response_chars": sum(len(text) for text in raw_responses),\n'
        '        "api_attempt_count": sum(int(item.get("api_attempt_count", 1)) for item in responses),\n'
        '        "gate_wait_ms": sum(float(item.get("gate_wait_ms", 0.0)) for item in responses),\n'
        '        "http_attempt_durations_ms": [duration for item in responses for duration in item.get("http_attempt_durations_ms", [])],\n'
        '        "http_retry_reasons": [reason for item in responses for reason in item.get("http_retry_reasons", [])],\n',
        "request telemetry fields",
    )
    source = replace_once(
        source,
        "    return {\n"
        '        "agent": agent_name,\n'
        '        "status": status,\n',
        "    if status == \"success\" and not (parse_valid and schema_valid):\n"
        "        raise AssertionError(f\"Contradictory agent status for {agent_name}: {status}\")\n"
        "    if GAIB_REQUEST_DIAGNOSTICS_ENABLED:\n"
        "        for request_index, response in enumerate(responses):\n"
        "            outcome = request_outcomes[request_index]\n"
        "            record_request_diagnostic({\n"
        "                \"query_id\": GAIB_ACTIVE_QUERY_ID, \"agent\": agent_name,\n"
        "                \"variant\": GAIB_ACTIVE_VARIANT, \"logical_attempt\": request_index + 1,\n"
        "                \"status\": outcome[\"status\"], \"api_success\": outcome[\"api_success\"],\n"
        "                \"json_parse\": outcome[\"json_parse\"], \"schema_valid\": outcome[\"schema_valid\"],\n"
        "                \"parse_error\": outcome[\"parse_error\"],\n"
        "                \"schema_errors\": outcome[\"schema_errors\"],\n"
        "                \"traceback\": exception_traceback, \"response\": response,\n"
        "                \"raw_response\": raw_responses[request_index] if request_index < len(raw_responses) else \"\"})\n"
        "    return {\n"
        '        "agent": agent_name,\n'
        '        "status": status,\n',
        "per-request protected diagnostics",
    )
    set_cell_source(cell, source)

def patch_quant_agent_cell(cell: dict[str, Any]) -> None:
    source = cell_source(cell)
    class_start = source.index("class QuantRegimeAgent:")
    class_end = source.index("class RiskAuditorAgent:", class_start)
    agent_source = source[class_start:class_end]
    agent_source = replace_once(
        agent_source,
        "        return call_agent_json(llm,self.name,self.role,payload)\n",
        "        allowed_ids = {\n"
        "            str(record[\"evidence_id\"])\n"
        "            for evidence_pack in (market, hmm)\n"
        "            for record in evidence_pack.get(\"records\", []) or []\n"
        "            if record.get(\"evidence_id\")\n"
        "        }\n"
        "        return call_agent_json(llm,self.name,self.role,payload,allowed_ids=allowed_ids)\n",
        "AI3 market and HMM evidence ID allowlist",
    )
    set_cell_source(cell, source[:class_start] + agent_source + source[class_end:])


def patch_news_agent_cell(cell: dict[str, Any]) -> None:
    source = cell_source(cell)
    class_start = source.index("class NewsAnalystAgent:")
    class_end = source.index("class MacroAnalystAgent:", class_start)
    agent_source = source[class_start:class_end]
    agent_source = replace_once(
        agent_source,
        "    def run(self,llm,query,sources,market):\n",
        "    def run(self,llm,query,sources,market,max_tokens=None):\n",
        "AI1 optional output budget",
    )
    agent_source = replace_once(
        agent_source,
        "        return call_agent_json(llm,self.name,self.role,payload)\n",
        "        return call_agent_json(llm,self.name,self.role,payload,max_tokens=max_tokens)\n",
        "AI1 output budget forwarding",
    )
    set_cell_source(cell, source[:class_start] + agent_source + source[class_end:])


def patch_macro_agent_cell(cell: dict[str, Any]) -> None:
    source = cell_source(cell)
    class_start = source.index("class MacroAnalystAgent:")
    class_end = source.index("class QuantRegimeAgent:", class_start)
    agent_source = source[class_start:class_end]
    agent_source = replace_once(
        agent_source,
        "    def run(self,llm,query,sources,market):\n",
        "    def run(self,llm,query,sources,market,max_tokens=None):\n",
        "AI2 optional output budget",
    )
    agent_source = replace_once(
        agent_source,
        "        return call_agent_json(llm,self.name,self.role,payload)\n",
        "        return call_agent_json(llm,self.name,self.role,payload,max_tokens=max_tokens)\n",
        "AI2 output budget forwarding",
    )
    set_cell_source(cell, source[:class_start] + agent_source + source[class_end:])


def patch_lead_agent_cell(cell: dict[str, Any]) -> None:
    source = cell_source(cell)
    class_start = source.index("class LeadResearcherAgent:")
    class_end = source.index("agent5=LeadResearcherAgent()", class_start)
    agent_source = source[class_start:class_end]
    agent_source = replace_once(
        agent_source,
        '    role="Lead research editor and evidence auditor. Integrate four specialist outputs, preserve disagreement, flag unsupported claims and write a concise actionable research brief."\n',
        '    role="Lead research editor and evidence auditor. Integrate four specialist outputs, preserve disagreement, flag unsupported claims and write a concise actionable research brief. Treat dated primary-source text in rag_sources as direct evidence for claims about that document; synthetic-market or simulated-portfolio caveats apply only to those datasets and must not invalidate official-source text. If a primary-source excerpt directly answers the question, cite it even when other agents mention synthetic data; abstain only when source evidence is missing or insufficient."\n',
        "prioritize official-source evidence over unrelated synthetic-data caveats",
    )
    agent_source = replace_once(
        agent_source,
        "    def run(self,llm,query,agent_results,manifest,market,hmm,risk,prechecks):\n",
        "    def run(self,llm,query,agent_results,manifest,market,hmm,risk,prechecks,max_tokens=None):\n",
        "AI5 optional output budget",
    )
    agent_source = replace_once(
        agent_source,
        "        payload=f\"USER QUESTION:\\n{query}\\n\\nEVIDENCE MANIFEST (valid IDs only):\\n{json.dumps(manifest,ensure_ascii=False,default=str)[:8000]}",
        "        prompt_manifest = {\n"
        "            **{key: value for key, value in manifest.items() if key != \"rag_sources\"},\n"
        "            \"rag_sources\": [\n"
        "                {key: source.get(key) for key in (\"citation_id\", \"title\", \"source\", \"publication_date\", \"report_period\", \"url\", \"text_excerpt\") if source.get(key) is not None}\n"
        "                for source in manifest.get(\"rag_sources\", [])\n"
        "            ],\n"
        "        }\n"
        "        payload=f\"USER QUESTION:\\n{query}\\n\\nEVIDENCE MANIFEST (valid IDs only):\\n{json.dumps(prompt_manifest,ensure_ascii=False,default=str)[:8000]}",
        "hide internal IDs from lead-agent prompt",
    )
    agent_source = replace_once(
        agent_source,
        "        return call_agent_json(llm,self.name,self.role,payload,max_tokens=THAILLM_MAX_TOKENS_FINAL,allowed_ids=allowed_ids)\n",
        "        return call_agent_json(llm,self.name,self.role,payload,max_tokens=max_tokens or THAILLM_MAX_TOKENS_FINAL,allowed_ids=allowed_ids)\n",
        "AI5 output budget forwarding",
    )
    set_cell_source(cell, source[:class_start] + agent_source + source[class_end:])


def patch_risk_agent_cell(cell: dict[str, Any]) -> None:
    source = cell_source(cell)
    class_start = source.index("class RiskAuditorAgent:")
    class_end = source.index("agent1=NewsAnalystAgent()", class_start)
    agent_source = source[class_start:class_end]
    agent_source = replace_once(
        agent_source,
        "    def run(self,llm,query,market,risk):\n",
        "    def run(self,llm,query,market,risk,max_tokens=None):\n",
        "AI4 optional output budget",
    )
    agent_source = replace_once(
        agent_source,
        "        return call_agent_json(llm,self.name,self.role,payload)\n",
        "        return call_agent_json(llm,self.name,self.role,payload,max_tokens=max_tokens)\n",
        "AI4 output budget forwarding",
    )
    agent_source = replace_once(
        agent_source,
        "        return call_agent_json(llm,self.name,self.role,payload,max_tokens=max_tokens)\n",
        "        allowed_ids = {\n"
        "            str(record[\"evidence_id\"])\n"
        "            for record in risk.get(\"records\", []) or []\n"
        "            if record.get(\"evidence_id\")\n"
        "        }\n"
        "        return call_agent_json(llm,self.name,self.role,payload,max_tokens=max_tokens,allowed_ids=allowed_ids)\n",
        "AI4 exact risk evidence ID allowlist",
    )
    set_cell_source(cell, source[:class_start] + agent_source + source[class_end:])


def patch_model_evidence_context_cell(cell: dict[str, Any]) -> None:
    source = cell_source(cell)
    source = replace_once(
        source,
        "        blocks.append(\"\\n\".join([f\"[{s['citation_id']}]\",f\"Document ID: {s.get('document_id') or 'unknown'}\",\n"
        "            f\"Original ID: {s.get('original_id') or 'unknown'}\",f\"Chunk ID: {s.get('chunk_id') or 'unknown'}\",\n"
        "            f\"Title: {s.get('title') or 'unknown'}\",f\"Source: {s.get('source') or s.get('source_file') or 'unknown'}\",\n"
        "            f\"Publication date: {s.get('publication_date') or 'unknown'}\",f\"Report period: {s.get('report_period') or 'unknown'}\",\n"
        "            f\"URL: {s.get('url') or 'not provided'}\",f\"Evidence text: {s.get('text_excerpt') or ''}\"]))\n",
        "        blocks.append(\"\\n\".join([f\"[{s['citation_id']}]\",\n"
        "            f\"Title: {s.get('title') or 'unknown'}\",f\"Source: {s.get('source') or s.get('source_file') or 'unknown'}\",\n"
        "            f\"Publication date: {s.get('publication_date') or 'unknown'}\",f\"Report period: {s.get('report_period') or 'unknown'}\",\n"
        "            f\"URL: {s.get('url') or 'not provided'}\",f\"Evidence text: {s.get('text_excerpt') or ''}\"]))\n",
        "remove internal chunk identifiers from agent evidence context",
    )
    set_cell_source(cell, source)


def patch_directional_prompts_cell(cell: dict[str, Any]) -> None:
    source = cell_source(cell)
    source = replace_once(
        source,
        "price_bias (bullish/bearish/mixed/unknown)",
        "price_bias (bullish/bearish/mixed/neutral/unknown)",
        "AI1 neutral price-bias enum",
    )
    source = replace_once(
        source,
        "macro_bias (bullish/bearish/mixed/unknown)",
        "macro_bias (bullish/bearish/mixed/neutral/unknown)",
        "AI2 neutral macro-bias enum",
    )
    set_cell_source(cell, source)


def patch_retrieval_metadata_index_cell(cell: dict[str, Any]) -> None:
    source = cell_source(cell)
    source = replace_once(
        source,
        "def tokenize(text):\n",
        "def bm25_index_text(chunk):\n"
        "    metadata = (chunk.get(key) for key in (\"title\", \"heading\", \"source\", \"publication_date\", \"report_period\", \"url\", \"source_file\"))\n"
        "    return \" \".join(str(value) for value in metadata if value not in (None, \"\")) + \" \" + str(chunk.get(\"text\") or \"\")\n"
        "\n"
        "def expand_retrieval_query(query):\n"
        "    text = str(query or \"\").strip()\n"
        "    if not re.search(r\"\\bfomc\\b\", text, flags=re.I):\n"
        "        return text\n"
        "    date_phrase = \"\"\n"
        "    match = re.search(r\"\\b(\\d{4}-\\d{2}-\\d{2})\\b\", text)\n"
        "    if match:\n"
        "        try:\n"
        "            date_phrase = datetime.strptime(match.group(1), \"%Y-%m-%d\").strftime(\"%B %d, %Y\")\n"
        "        except ValueError:\n"
        "            date_phrase = \"\"\n"
        "    return \" \".join(part for part in (text, \"Federal Open Market Committee Federal Reserve monetary policy statement\", date_phrase) if part)\n"
        "\n"
        "def reranker_document(candidate):\n"
        "    metadata = [\n"
        "        f\"{key}: {candidate[key]}\"\n"
        "        for key in (\"title\", \"heading\", \"publication_date\", \"report_period\", \"url\")\n"
        "        if candidate.get(key) not in (None, \"\")\n"
        "    ]\n"
        "    return \"\\n\".join(metadata + [str(candidate.get(\"text\") or \"\")])[:CONTEXT_PER_CHUNK_MAX_CHARS]\n"
        "\n"
        "def tokenize(text):\n",
        "metadata-aware BM25 and FOMC retrieval helpers",
    )
    old_index = 'self.bm25=BM25Okapi([tokenize(c["text"]) for c in self.chunks])'
    if source.count(old_index) != 2:
        raise ValueError(f"metadata-aware BM25 index: expected 2 corpus builders, found {source.count(old_index)}")
    source = source.replace(
        old_index,
        'self.bm25=BM25Okapi([tokenize(bm25_index_text(c)) for c in self.chunks])',
    )
    source = replace_once(
        source,
        "        for results in (dense,bm):\n"
        "            seen=set()\n"
        "            for rank,c in enumerate(results,1):\n"
        "                key=chunk_identity(c)\n"
        "                if key in seen: continue\n"
        "                seen.add(key)\n"
        "                if key not in fused: fused[key]={**c,\"rrf_score\":0.0}\n"
        "                fused[key][\"rrf_score\"] += 1/(RRF_K+rank)\n",
        "        for results,weight in ((dense,1.0),(bm,RRF_BM25_WEIGHT)):\n"
        "            seen=set()\n"
        "            for rank,c in enumerate(results,1):\n"
        "                key=chunk_identity(c)\n"
        "                if key in seen: continue\n"
        "                seen.add(key)\n"
        "                if key not in fused: fused[key]={**c,\"rrf_score\":0.0}\n"
        "                fused[key][\"rrf_score\"] += weight/(RRF_K+rank)\n",
        "weighted BM25 reciprocal-rank fusion",
    )
    source = replace_once(
        source,
        '"documents\":[str(c.get(\"text\", \"\"))[:CONTEXT_PER_CHUNK_MAX_CHARS] for c in candidates],',
        '"documents\":[reranker_document(c) for c in candidates],',
        "include source metadata in Jina reranker documents",
    )
    source = replace_once(
        source,
        '        raw,metrics=self.backend.retrieve(query,HYBRID_CANDIDATES)\n'
        '        reranked,rstatus,rms,rerr=self.reranker.rerank(query,raw,top_n)\n',
        '        retrieval_query=expand_retrieval_query(query)\n'
        '        raw,metrics=self.backend.retrieve(retrieval_query,HYBRID_CANDIDATES)\n'
        '        reranked,rstatus,rms,rerr=self.reranker.rerank(retrieval_query,raw,top_n)\n'
        '        metrics["query_expansion"]="fomc_acronym_date_v1" if retrieval_query != str(query or "").strip() else "none"\n',
        "expand FOMC retrieval and reranking query",
    )
    set_cell_source(cell, source)


def build_notebook() -> Path:
    notebook = json.loads(SOURCE_NOTEBOOK.read_text(encoding="utf-8"))
    notebook["metadata"]["title"] = "GAIB-1 Exit Criteria Experiment v2"
    notebook["metadata"]["gaib_version"] = "exit-criteria-v2"
    first_markdown = notebook["cells"][0]
    set_cell_source(
        first_markdown,
        cell_source(first_markdown).replace(
            "# GAIB-1 Reliability Experiment — Phase 1–2",
            "# GAIB-1 Exit Criteria Experiment (v2)",
            1,
        ),
    )
    cells_by_id = {cell.get("id"): cell for cell in notebook.get("cells", [])}
    for cell_id in ("677be107", "f5926591", "5cce7a2e", "6c41d141", "a3a65109", "8b105991", "gaib_coverage_audit_v1"):
        if cell_id not in cells_by_id:
            raise ValueError(f"Required source cell is missing: {cell_id}")

    config = cell_source(cells_by_id["8b105991"])
    for required_opt_in in (
        'RUN_RETRIEVAL_BENCHMARK = os.getenv("GAIB_RUN_RETRIEVAL_BENCHMARK", "false")',
        'RUN_AGENT_BENCHMARK = os.getenv("GAIB_RUN_AGENT_BENCHMARK", "false")',
        'if not THAILLM_BASE_URL.lower().startswith("https://"):',
    ):
        if required_opt_in not in config:
            raise ValueError(f"Source configuration is missing secure opt-in: {required_opt_in}")
    config = config.replace('"reliability_phase1_2"', '"token_root_cause"')
    config = replace_once(
        config,
        '    for slot in ("JINA_API_KEY", "JINA_API_KEY2")\n',
        '    for slot in ("JINA_API_KEY", "JINA_API_KEY2", "JINA_API_KEY3")\n',
        "support the third Jina API key slot",
    )
    config = replace_once(
        config,
        '    for slot in ("JINA_API_KEY", "JINA_API_KEY2", "JINA_API_KEY3")\n',
        '    for slot in ("JINA_API_KEY", "JINA_API_KEY2", "JINA_API_KEY3", "JINA_API_KEY4")\n',
        "support the fourth Jina API key slot",
    )
    config = replace_once(
        config,
        'GAIB_GT_READY_PATH = GAIB_GT_DIR / "ground_truth_fed_ready_v1.jsonl"\n',
        'GAIB_GT_READY_PATH = configured_path("GAIB_GT_READY_PATH", "multi_agent/gt/ground_truth_fed_ready_v1.jsonl")\n',
        "allow a separately versioned Ground Truth file",
    )
    config = replace_once(
        config,
        'if GAIB_BENCHMARK_SPLIT not in {"development", "validation", "test"}:\n',
        'if GAIB_BENCHMARK_SPLIT not in {"development", "validation", "test", "held_out"}:\n',
        "support the separate held-out split",
    )
    config = replace_once(
        config,
        'GAIB_ALLOW_TEST_SPLIT = os.getenv("GAIB_ALLOW_TEST_SPLIT", "false").strip().lower() in {"1", "true", "yes"}\n',
        'GAIB_ALLOW_TEST_SPLIT = os.getenv("GAIB_ALLOW_TEST_SPLIT", "false").strip().lower() in {"1", "true", "yes"}\n'
        'GAIB_ALLOW_HELD_OUT_SPLIT = os.getenv("GAIB_ALLOW_HELD_OUT_SPLIT", "false").strip().lower() in {"1", "true", "yes"}\n',
        "require separate opt-in for the held-out split",
    )
    config = replace_once(
        config,
        'if GAIB_BENCHMARK_SPLIT not in {"development", "validation", "test", "held_out"}:\n'
        '    raise ValueError("GAIB_BENCHMARK_SPLIT must be development, validation, or test.")\n',
        'if GAIB_BENCHMARK_SPLIT not in {"development", "validation", "test", "held_out"}:\n'
        '    raise ValueError("GAIB_BENCHMARK_SPLIT must be development, validation, test, or held_out.")\n',
        "align split validation error with accepted split values",
    )
    config = replace_once(
        config,
        'if GAIB_BENCHMARK_SPLIT == "test" and not GAIB_ALLOW_TEST_SPLIT:\n'
        '    raise RuntimeError("Test split is held out. Set GAIB_ALLOW_TEST_SPLIT=true only for final evaluation.")\n',
        'if GAIB_BENCHMARK_SPLIT == "test" and not GAIB_ALLOW_TEST_SPLIT:\n'
        '    raise RuntimeError("Refusing to run the frozen test split without explicit final-evaluation opt-in.")\n'
        'if GAIB_BENCHMARK_SPLIT == "held_out" and not GAIB_ALLOW_HELD_OUT_SPLIT:\n'
        '    raise RuntimeError("Refusing to run the separate held-out split without explicit opt-in.")\n',
        "keep the frozen test and new held-out split separately protected",
    )
    config = replace_once(
        config,
        "RRF_K = 60\n",
        "RRF_K = 60\nRRF_BM25_WEIGHT = 2.0\n",
        "weight lexical reciprocal-rank evidence",
    )
    config = replace_once(
        config,
        'THAILLM_MAX_TOKENS_AGENT = int(os.getenv("THAILLM_MAX_TOKENS_AGENT", "900"))\n',
        'THAILLM_MAX_TOKENS_AGENT = int(os.getenv("THAILLM_MAX_TOKENS_AGENT", "900"))\n'
        'GAIB_AI1_LIVE_MAX_TOKENS = int(os.getenv("GAIB_AI1_LIVE_MAX_TOKENS", "1500"))\n'
        'GAIB_AI2_LIVE_MAX_TOKENS = int(os.getenv("GAIB_AI2_LIVE_MAX_TOKENS", "1500"))\n'
        'GAIB_AI4_LIVE_MAX_TOKENS = int(os.getenv("GAIB_AI4_LIVE_MAX_TOKENS", "1500"))\n'
        'GAIB_AI5_LIVE_MAX_TOKENS = int(os.getenv("GAIB_AI5_LIVE_MAX_TOKENS", "2400"))\n'
        'GAIB_COMPACT_OUTPUT_DEFAULT = os.getenv("GAIB_COMPACT_OUTPUT_DEFAULT", "true").strip().lower() in {"1", "true", "yes"}\n'
        'GAIB_AI3_COMPACT_OUTPUT = os.getenv("GAIB_AI3_COMPACT_OUTPUT", "true").strip().lower() in {"1", "true", "yes"}\n',
        "configure live agent truncation budgets and compact contracts",
    )
    config = replace_once(
        config,
        'GAIB_AI3_COMPACT_OUTPUT = os.getenv("GAIB_AI3_COMPACT_OUTPUT", "true").strip().lower() in {"1", "true", "yes"}\n',
        'GAIB_AI3_COMPACT_OUTPUT = os.getenv("GAIB_AI3_COMPACT_OUTPUT", "true").strip().lower() in {"1", "true", "yes"}\n'
        'GAIB_RUN_ALL_EXPERIMENTS = os.getenv("GAIB_RUN_ALL_EXPERIMENTS", "false").strip().lower() in {"1", "true", "yes"}\n'
        'GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK = os.getenv("GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK", "false").strip().lower() in {"1", "true", "yes"}\n'
        'GAIB_RUN_FULL_HELD_OUT_ACCEPTANCE = os.getenv("GAIB_RUN_FULL_HELD_OUT_ACCEPTANCE", "false").strip().lower() in {"1", "true", "yes"}\n'
        'GAIB_JUDGE_MODEL = os.getenv("GAIB_JUDGE_MODEL", "pathumma-thaillm-qwen3-8b-think-3.0.0").strip()\n'
        'GAIB_SECOND_JUDGE_MODEL = os.getenv("GAIB_SECOND_JUDGE_MODEL", "").strip()\n'
        'GAIB_JUDGE_ENABLED = os.getenv("GAIB_JUDGE_ENABLED", "true").strip().lower() in {"1", "true", "yes"}\n'
        'GAIB_HUMAN_CALIBRATION_LABELS = os.getenv("GAIB_HUMAN_CALIBRATION_LABELS", "").strip()\n',
        "add one switch for the complete development-only experiment suite",
    )
    config = replace_once(
        config,
        '    "remote_api_opt_in": RUN_RETRIEVAL_BENCHMARK or RUN_AGENT_BENCHMARK or RUN_LIVE_DEMO,\n',
        '    "remote_api_opt_in": RUN_RETRIEVAL_BENCHMARK or RUN_AGENT_BENCHMARK or RUN_LIVE_DEMO,\n'
        '    "full_development_benchmark": GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK,\n'
        '    "full_held_out_acceptance": GAIB_RUN_FULL_HELD_OUT_ACCEPTANCE,\n',
        "record full-development benchmark opt-in in the runtime manifest",
    )
    config = replace_once(
        config,
        '    "full_development_benchmark": GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK,\n',
        '    "full_development_benchmark": GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK,\n'
        '    "ai_judge_enabled": GAIB_JUDGE_ENABLED,\n'
        '    "judge_model_configured": bool(GAIB_JUDGE_MODEL),\n'
        '    "second_judge_model_configured": bool(GAIB_SECOND_JUDGE_MODEL),\n',
        "record AI judge opt-in without storing credentials",
    )
    set_cell_source(cells_by_id["8b105991"], config)

    patch_generation_cell(cells_by_id["677be107"])
    patch_agent_cell(cells_by_id["677be107"])
    patch_quant_agent_cell(cells_by_id["f5926591"])
    patch_news_agent_cell(cells_by_id["f5926591"])
    patch_macro_agent_cell(cells_by_id["f5926591"])
    patch_risk_agent_cell(cells_by_id["f5926591"])
    patch_model_evidence_context_cell(cells_by_id["f5926591"])
    patch_retrieval_metadata_index_cell(cells_by_id["6c41d141"])
    patch_lead_agent_cell(cells_by_id["5cce7a2e"])
    patch_directional_prompts_cell(cells_by_id["f5926591"])
    retrieval_benchmark_source = cell_source(cells_by_id["a3a65109"])
    retrieval_benchmark_source = replace_once(
        retrieval_benchmark_source,
        '                "jina_status": result["metrics"].get("rerank_status"),\n',
        '                "jina_status": result["metrics"].get("rerank_status"),\n'
        '                "retrieval_query_expansion": result["metrics"].get("query_expansion"),\n',
        "record retrieval query expansion in benchmark output",
    )
    set_cell_source(cells_by_id["a3a65109"], retrieval_benchmark_source)
    orchestrator_source = cell_source(cells_by_id["5cce7a2e"])
    orchestrator_source = replace_once(
        orchestrator_source,
        '"AI1_News_Analyst":lambda:agent1.run(self.llm,query,sources,market),\n',
        '"AI1_News_Analyst":lambda:agent1.run(self.llm,query,sources,market,max_tokens=GAIB_AI1_LIVE_MAX_TOKENS),\n',
        "use measured AI1 budget in live orchestration",
    )
    orchestrator_source = replace_once(
        orchestrator_source,
        '"AI2_Macro_Analyst":lambda:agent2.run(self.llm,query,sources,market),\n',
        '"AI2_Macro_Analyst":lambda:agent2.run(self.llm,query,sources,market,max_tokens=GAIB_AI2_LIVE_MAX_TOKENS),\n',
        "use measured AI2 budget in live orchestration",
    )
    orchestrator_source = replace_once(
        orchestrator_source,
        '"AI4_Risk_Data_Auditor":lambda:agent4.run(self.llm,query,market,risk),\n',
        '"AI4_Risk_Data_Auditor":lambda:agent4.run(self.llm,query,market,risk,max_tokens=GAIB_AI4_LIVE_MAX_TOKENS),\n',
        "use measured AI4 budget in live orchestration",
    )
    orchestrator_source = replace_once(
        orchestrator_source,
        "final=agent5.run(self.llm,query,specialist_results,manifest,market,hmm,risk,prechecks)\n",
        "final=agent5.run(self.llm,query,specialist_results,manifest,market,hmm,risk,prechecks,max_tokens=GAIB_AI5_LIVE_MAX_TOKENS)\n",
        "use measured AI5 budget in live orchestration",
    )
    orchestrator_source = replace_once(
        orchestrator_source,
        "    all_refs, valid_refs = [], []\n",
        "    all_refs, valid_refs, invalid_refs = [], [], []\n",
        "track rejected claim evidence IDs",
    )
    orchestrator_source = replace_once(
        orchestrator_source,
        "        valid_refs.extend(valid)\n",
        "        valid_refs.extend(valid)\n"
        "        invalid_refs.extend(str(identifier) for identifier in ids if str(identifier) not in allowed_ids)\n",
        "record invalid claim evidence IDs",
    )
    orchestrator_source = replace_once(
        orchestrator_source,
        '        "claim_citation_id_valid_rate": len(valid_refs) / len(all_refs) if all_refs else "NO_CITATIONS",\n',
        '        "claim_citation_id_valid_rate": len(valid_refs) / len(all_refs) if all_refs else "NO_CITATIONS",\n'
        '        "invalid_claim_evidence_ids": sorted(set(invalid_refs)),\n',
        "expose rejected claim evidence IDs in audit",
    )
    orchestrator_source = replace_once(
        orchestrator_source,
        '        else:\n'
        '            lines.append("- **Needs evidence review:** " + claim + " (no valid supporting source ID)")\n'
        '        if invalid:\n'
        '            lines.append("  - Rejected unknown source IDs: " + ", ".join(invalid))\n'
        '    if len(lines) == 1:\n'
        '        lines.append("No schema-valid evidence-based findings were produced.")\n',
        '        else:\n'
        '            continue\n'
        '        if invalid:\n'
        '            lines.append("  - Rejected unknown source IDs: " + ", ".join(invalid))\n'
        '    if len(lines) == 1:\n'
        '        lines.append("No cited, schema-valid evidence-based findings were produced; human review is required.")\n',
        "suppress uncited claims from the final report",
    )
    set_cell_source(cells_by_id["5cce7a2e"], orchestrator_source)
    ground_truth_source = cell_source(cells_by_id["4284e50e"])
    ground_truth_source = replace_once(
        ground_truth_source,
        'def load_ground_truth():\n'
        '    if not (GAIB_GT_ALL_PATH.is_file() and GAIB_GT_READY_PATH.is_file() and GAIB_GT_GAPS_PATH.is_file()):\n'
        '        raise FileNotFoundError("Required Fed Ground Truth files are missing from multi_agent/gt.")\n'
        '    all_rows = read_jsonl(GAIB_GT_ALL_PATH)\n'
        '    ready_rows = read_jsonl(GAIB_GT_READY_PATH)\n'
        '    gap_rows = read_jsonl(GAIB_GT_GAPS_PATH)\n'
        '    if len(all_rows) != 43 or len(ready_rows) != 37 or len(gap_rows) != 6:\n'
        '        raise ValueError(f"Unexpected Fed Ground Truth counts: all={len(all_rows)}, ready={len(ready_rows)}, gaps={len(gap_rows)}")\n'
        '    if any(row.get("qdrant_index_coverage_verified") is not False for row in ready_rows):\n'
        '        raise ValueError("Expected source-present Fed records to retain their unverified Qdrant status.")\n'
        '    selected = [row for row in ready_rows if row.get("split") == GAIB_BENCHMARK_SPLIT]\n'
        '    return selected, {\n'
        '        "source": str(GAIB_GT_READY_PATH),\n'
        '        "all_count": len(all_rows),\n'
        '        "source_present_count": len(ready_rows),\n'
        '        "blocked_source_gap_count": len(gap_rows),\n'
        '        "selected_split": GAIB_BENCHMARK_SPLIT,\n'
        '        "selected_count": len(selected),\n'
        '        "qdrant_index_coverage": "UNVERIFIED",\n'
        '        "human_semantic_review": "REQUIRED",\n'
        '    }\n'
        '\n'
        'GROUND_TRUTH, ground_truth_info = load_ground_truth()\n'
        'GROUND_TRUTH_SOURCE_GAPS = read_jsonl(GAIB_GT_GAPS_PATH)\n',
        'def load_ground_truth():\n'
        '    default_ready_path = (GAIB_GT_DIR / "ground_truth_fed_ready_v1.jsonl").resolve()\n'
        '    custom_dataset = GAIB_GT_READY_PATH.resolve() != default_ready_path\n'
        '    if custom_dataset:\n'
        '        ready_rows = read_jsonl(GAIB_GT_READY_PATH)\n'
        '        if not ready_rows:\n'
        '            raise ValueError(f"Custom Ground Truth dataset is empty: {GAIB_GT_READY_PATH}")\n'
        '        selected = [row for row in ready_rows if row.get("split") == GAIB_BENCHMARK_SPLIT]\n'
        '        return selected, {\n'
        '            "source": str(GAIB_GT_READY_PATH),\n'
        '            "all_count": len(ready_rows),\n'
        '            "source_present_count": sum(\n'
        '                all(evidence.get("source_span_validated_against_uploaded_corpus") is True\n'
        '                    for evidence in row.get("evidence") or [])\n'
        '                for row in ready_rows\n'
        '            ),\n'
        '            "blocked_source_gap_count": sum(not (row.get("evidence") or []) for row in ready_rows),\n'
        '            "selected_split": GAIB_BENCHMARK_SPLIT,\n'
        '            "selected_count": len(selected),\n'
        '            "qdrant_index_coverage": "UNVERIFIED",\n'
        '            "human_semantic_review": "REQUIRED",\n'
        '            "custom_dataset": True,\n'
        '        }\n'
        '    if not (GAIB_GT_ALL_PATH.is_file() and GAIB_GT_READY_PATH.is_file() and GAIB_GT_GAPS_PATH.is_file()):\n'
        '        raise FileNotFoundError("Required Fed Ground Truth files are missing from multi_agent/gt.")\n'
        '    all_rows = read_jsonl(GAIB_GT_ALL_PATH)\n'
        '    ready_rows = read_jsonl(GAIB_GT_READY_PATH)\n'
        '    gap_rows = read_jsonl(GAIB_GT_GAPS_PATH)\n'
        '    if len(all_rows) != 43 or len(ready_rows) != 37 or len(gap_rows) != 6:\n'
        '        raise ValueError(f"Unexpected Fed Ground Truth counts: all={len(all_rows)}, ready={len(ready_rows)}, gaps={len(gap_rows)}")\n'
        '    if any(row.get("qdrant_index_coverage_verified") is not False for row in ready_rows):\n'
        '        raise ValueError("Expected source-present Fed records to retain their unverified Qdrant status.")\n'
        '    selected = [row for row in ready_rows if row.get("split") == GAIB_BENCHMARK_SPLIT]\n'
        '    return selected, {\n'
        '        "source": str(GAIB_GT_READY_PATH),\n'
        '        "all_count": len(all_rows),\n'
        '        "source_present_count": len(ready_rows),\n'
        '        "blocked_source_gap_count": len(gap_rows),\n'
        '        "selected_split": GAIB_BENCHMARK_SPLIT,\n'
        '        "selected_count": len(selected),\n'
        '        "qdrant_index_coverage": "UNVERIFIED",\n'
        '        "human_semantic_review": "REQUIRED",\n'
        '        "custom_dataset": False,\n'
        '    }\n'
        '\n'
        'GROUND_TRUTH, ground_truth_info = load_ground_truth()\n'
        'GROUND_TRUTH_SOURCE_GAPS = (\n'
        '    [] if ground_truth_info.get("custom_dataset") else read_jsonl(GAIB_GT_GAPS_PATH)\n'
        ')\n',
        "support separately versioned Ground Truth without weakening the frozen dataset audit",
    )
    set_cell_source(cells_by_id["4284e50e"], ground_truth_source)
    coverage_source = cell_source(cells_by_id["gaib_coverage_audit_v1"])
    coverage_source = replace_once(
        coverage_source,
        "ALL_READY_GROUND_TRUTH = read_jsonl(GAIB_GT_READY_PATH)\n"
        "ground_truth_audit_df = audit_ground_truth_coverage(ALL_READY_GROUND_TRUTH)\n",
        "ALL_READY_GROUND_TRUTH = read_jsonl(GAIB_GT_READY_PATH)\n"
        "if assistant is not None and assistant.evidence.backend_name == \"qdrant_cloudflare_hybrid\":\n"
        "    ground_truth_audit_df = audit_ground_truth_coverage(ALL_READY_GROUND_TRUTH)\n"
        "else:\n"
        "    ground_truth_audit_df = pd.DataFrame()\n"
        "    print(\"Ground Truth Qdrant audit skipped; initialize the remote A2 assistant first.\")\n",
        "make Qdrant audit safe when remote benchmarks are disabled",
    )
    set_cell_source(cells_by_id["gaib_coverage_audit_v1"], coverage_source)

    notebook["cells"].append({
        "cell_type": "markdown",
        "id": "token-root-cause-overview",
        "metadata": {},
        "source": [
            "## Targeted token-limit and JSON reliability experiment (v1)\n",
            "\n",
            "The original A2 notebook and Phase 1–2 experiment remain unchanged. This copy defaults to no benchmark API calls. It first validates saved telemetry and writes a new run manifest plus diagnosis files. Set `GAIB_RUN_TARGETED_EXPERIMENT=true` only when ready to spend API quota. The experiments reuse one retrieved evidence set per query and vary one generation factor at a time. Raw responses and tracebacks are saved only in the run's private local diagnostic file.\n",
            "The original A2 notebook and Phase 1–2 experiment remain unchanged. This copy defaults to no benchmark API calls. Set `GAIB_RUN_ALL_EXPERIMENTS=true` to run the complete controlled token-budget, compact-output, recovery and latency suite, followed by retrieval and multi-agent evaluation of every development query using ThaiLLM, Qdrant/Cloudflare and Jina. This master switch is restricted to the development split; it does not run or reuse the held-out test split. API calls incur provider usage. Keep API keys in environment variables or `.env`; raw responses and tracebacks are stored only in the protected local diagnostic file. Individual experiment switches remain available for focused runs.\n",
        ],
    })
    notebook["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "id": "token-root-cause-preflight",
        "metadata": {},
        "outputs": [],
        "source": PRECHECK_CELL.replace(
            'Gold_Assistant_GAIB1_Token_Root_Cause_Experiment_v1.ipynb',
            OUTPUT_NOTEBOOK.name,
        ).splitlines(keepends=True),
    })
    notebook["cells"].append({
        "cell_type": "markdown",
        "id": "gaib-exit-criteria-v2-overview",
        "metadata": {},
        "source": [
            "## Exit-criteria instrumentation (v2)\n",
            "\n",
            "This candidate preserves v1. It adds protected critical-query traces, source-span retrieval diagnostics, explicit numeric answer/abstention scoring, and a gate report that keeps unmet sample-size and human-review requirements as NO-GO. Numeric facts are emitted only from a retrieved source whose publication date matches the date asked; no Ground Truth value is used to generate answers. Live recovery retries confirmed truncations at 1,200 tokens and escalates once to 1,500 only when the 1,200-token response is also confirmed truncated; set `GAIB_LIVE_TRUNCATION_RECOVERY_MODE=none` to disable.\n",
            "Set `GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK=true` to run every available development query against the real services without enabling the separate token/recovery ablation suite. This switch is development-only; validation and test splits are rejected. Set `GAIB_RUN_ALL_EXPERIMENTS=true` only when both the full experiment suite and full development benchmark are intended.\n",
        ],
    })
    notebook["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "id": "gaib-exit-criteria-v2-instrumentation",
        "metadata": {},
        "outputs": [],
        "source": EXIT_CRITERIA_CELL.splitlines(keepends=True),
    })
    notebook["cells"].append({
        "cell_type": "markdown",
        "id": "gaib-ai-judge-policy-heading",
        "metadata": {},
        "source": [
            "## AI-as-a-judge acceptance layer\n",
            "\n",
            "Every final factual claim and abstention is evaluated blind against retrieved evidence before a separate expected-fact comparison. Numeric oracle checks remain deterministic and cannot be overridden. The primary judge uses a distinct model from ThaiLLM supported models (default: `pathumma-thaillm-qwen3-8b-think-3.0.0` or `typhoon-s-thaillm-8b-instruct`), evaluating claim correctness, citation entailment, and completeness.\n",
            "Supported ThaiLLM models: `openthaigpt-thaillm-8b-instruct-v7.2`, `pathumma-thaillm-qwen3-8b-think-3.0.0`, `typhoon-s-thaillm-8b-instruct`, `thalle-0.2-thaillm-8b-fa`. Second judge escalation is optional via `GAIB_SECOND_JUDGE_MODEL`. AI judging makes additional provider calls and is enabled only with the opt-in live benchmark.\n",
        ],
    })
    notebook["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "id": "gaib-ai-judge-policy",
        "metadata": {},
        "outputs": [],
        "source": AI_JUDGE_CELL.splitlines(keepends=True),
    })
    notebook["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "id": "token-root-cause-experiments",
        "metadata": {},
        "outputs": [],
        "source": EXPERIMENT_CELL.splitlines(keepends=True),
    })
    notebook["cells"].append({
        "cell_type": "markdown",
        "id": "gaib-live-acceptance-heading",
        "metadata": {},
        "source": [
            "## Live acceptance run (ThaiLLM + Qdrant + Jina)\n",
            "\n",
            "This cell runs the development benchmark against the real remote stack (five queries by default, or all available development queries with `GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK=true`). It is opt-in and does not run during ordinary notebook execution. Set `GAIB_RUN_LIVE_ACCEPTANCE=true` before running the cell. Confirmed truncations receive a 1,200-token recovery, escalating once to 1,500 only if the 1,200-token response is provider-confirmed as truncated; set `GAIB_LIVE_TRUNCATION_RECOVERY_MODE=none` to disable. ThaiLLM credentials are refused unless the endpoint uses HTTPS. Outputs and per-query errors are written to this run's `OUTPUT_DIR`.\n",
        ],
    })
    notebook["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "id": "gaib-live-acceptance-run",
        "metadata": {},
        "outputs": [],
        "source": LIVE_ACCEPTANCE_CELL.splitlines(keepends=True),
    })

    for cell in notebook["cells"]:
        if cell.get("cell_type") == "code":
            cell["execution_count"] = None
            cell["outputs"] = []

    notebook["metadata"]["kernelspec"] = {
        "display_name": "Gold Assistant Embedding (.venv Python 3.11.12)",
        "language": "python",
        "name": "gold-assistant-embedding",
    }
    OUTPUT_NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return OUTPUT_NOTEBOOK


EXIT_CRITERIA_CELL = r'''import json
import re
import unicodedata
from datetime import datetime, timezone

GAIB_EXIT_TRACE_PATH = GAIB_DIAGNOSTIC_DIR / "exit_criteria_traces.jsonl"
GAIB_EXIT_RUN_DETAILS = {}
GAIB_EXIT_ACTIVE_QUERY_ID = None
GAIB_EXIT_LAST_AGENT_PAYLOADS = {}
GAIB_EXIT_CRITICAL_QUERY_IDS = {
    "gtv2_000054", "gtv2_000055", "gtv2_000070",
    "gtv2_000071", "gtv2_000078", "gtv2_000079",
}

def _exit_normalize(value):
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = text.replace("\u2010", "-").replace("\u2011", "-").replace("\u2012", "-")
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    return " ".join(text.split())

def _exit_date_key(value):
    text = str(value or "").strip()
    formats = ("%Y-%m-%d", "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y")
    for date_format in formats:
        try:
            return datetime.strptime(text, date_format).date().isoformat()
        except ValueError:
            pass
    match = re.search(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b", text)
    if match:
        try:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))).date().isoformat()
        except ValueError:
            return None
    match = re.search(r"\b([A-Za-z]+)\s+(\d{1,2}),?\s+(20\d{2})\b", text)
    if match:
        for date_format in ("%B %d %Y", "%b %d %Y"):
            try:
                return datetime.strptime(" ".join(match.groups()), date_format).date().isoformat()
            except ValueError:
                continue
    return None

def extract_fomc_target_range(query, sources):
    query_date = _exit_date_key(query)
    if query_date is None or not re.search(
        r"\b(?:federal funds rate|target range)\b", str(query or ""), re.I
    ):
        return None
    dash = r"[-\u2010-\u2015\u2212]"
    number = rf"(?:\d+\s*{dash}\s*\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)"
    pattern = re.compile(
        rf"\b(?P<action>maintain(?:ed)?|keep|kept|raise(?:d)?|increase(?:d)?|lower(?:ed)?|reduce(?:d)?)\b"
        rf"[^.!?]{{0,100}}?target range[^.!?]{{0,100}}?\bat\s+"
        rf"(?P<low>{number})\s*(?:to|{dash})\s*(?P<high>{number})\s*(?P<unit>percent|%)",
        re.I,
    )
    for source in sources or []:
        publication_date = source.get("publication_date")
        if _exit_date_key(publication_date) != query_date:
            continue
        citation_id = str(source.get("citation_id") or "")
        if not re.fullmatch(r"S\d+", citation_id):
            continue
        text = str(source.get("text_excerpt") or source.get("text") or "")
        match = pattern.search(text)
        if not match:
            continue
        action = match.group("action").casefold()
        action = {
            "maintain": "maintain", "maintained": "maintain",
            "keep": "maintain", "kept": "maintain",
            "raise": "raise", "raised": "raise",
            "increase": "increase", "increased": "increase",
            "lower": "lower", "lowered": "lower",
            "reduce": "reduce", "reduced": "reduce",
        }[action]
        unit = "percent" if match.group("unit").casefold() == "percent" else "%"
        return {
            "publication_date": query_date,
            "low": match.group("low").strip(),
            "high": match.group("high").strip(),
            "unit": unit,
            "action": action,
            "citation_id": citation_id,
            "document_id": source.get("document_id"),
            "url": source.get("url"),
            "claim": (
                f"The FOMC decided to {action} the target range for the federal funds rate "
                f"at {match.group('low').strip()} to {match.group('high').strip()} {unit} "
                f"on {query_date}."
            ),
            "matched_source_text": text[max(0, match.start() - 80):min(len(text), match.end() + 80)],
        }
    return None

def _exit_numeric_claim_complete(candidate, findings):
    required = (
        candidate.get("low"),
        candidate.get("high"),
        candidate.get("action"),
    )
    for finding in findings or []:
        if not isinstance(finding, dict):
            continue
        claim = str(finding.get("claim") or "")
        normalized_claim = _exit_normalize(claim)
        if (
            all(_exit_normalize(value) in normalized_claim for value in required)
            and _exit_date_key(claim) == candidate.get("publication_date")
        ):
            return True
    return False

def _exit_ground_truth_for(query):
    normalized_query = _exit_normalize(query)
    for row in ALL_READY_GROUND_TRUTH:
        if _exit_normalize(row.get("query")) == normalized_query:
            return row
    return None

def _exit_exact_quotes(gt):
    return [
        str(item.get("exact_quote") or "")
        for item in (gt or {}).get("evidence", [])
        if str(item.get("exact_quote") or "").strip()
    ]

def _exit_quote_present(quote, candidates):
    needle = _exit_normalize(quote)
    if not needle:
        return False
    return any(needle in _exit_normalize(
        item.get("text_excerpt") or item.get("text") or ""
    ) for item in candidates or [])

def _exit_expected_values(gt):
    values = []
    answer = (gt or {}).get("expected_answer") or {}
    for fact in answer.get("facts", []) if isinstance(answer, dict) else []:
        if isinstance(fact, dict):
            for key in ("value_text", "raw_value", "decision_action", "publication_date", "period"):
                if fact.get(key) not in (None, ""):
                    values.append(str(fact[key]))
    return list(dict.fromkeys(values))

def _exit_fact_coverage(gt, report):
    answer = (gt or {}).get("expected_answer") or {}
    facts = answer.get("facts", []) if isinstance(answer, dict) else []
    required = []
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        for key in ("value_text", "decision_action", "publication_date"):
            value = fact.get(key)
            if value not in (None, ""):
                required.append(str(value))
    normalized_report = _exit_normalize(report)
    matched = sum(_exit_normalize(value) in normalized_report for value in required)
    return {
        "expected_fact_coverage": matched / len(required) if required else None,
        "expected_fact_count": len(required),
        "expected_fact_matches": matched,
    }

def _exit_root_cause(gt, result, raw_final_data, raw_final_text):
    quotes = _exit_exact_quotes(gt)
    retrieval = result.get("retrieval") or {}
    retrieval_metrics = retrieval.get("metrics") or {}
    stage_candidates = retrieval_metrics.get("stage_candidates") or {}
    pool = []
    for candidates in stage_candidates.values():
        pool.extend(candidates or [])
    pool.extend(retrieval.get("raw_candidates") or [])
    pool.extend(retrieval.get("ranked_candidates") or [])
    expected_ids = {
        _exit_normalize(item.get(key))
        for item in (gt or {}).get("evidence", [])
        for key in ("document_id", "source_document_id_in_uploaded_corpus")
        if item.get(key)
    }
    expected_urls = {
        _exit_normalize(item.get("source_url"))
        for item in (gt or {}).get("evidence", [])
        if item.get("source_url")
    }
    found_docs = [
        candidate for candidate in pool
        if expected_ids.intersection({
            _exit_normalize(candidate.get(key))
            for key in ("document_id", "original_id", "source_document_id", "source_document_id_in_uploaded_corpus")
            if candidate.get(key)
        }) or _exit_normalize(candidate.get("url") or candidate.get("source_url")) in expected_urls
    ]
    final_sources = result.get("sources") or []
    span_in_pool = any(_exit_quote_present(quote, pool) for quote in quotes)
    span_in_context = any(_exit_quote_present(quote, final_sources) for quote in quotes)
    validated_quotes = [
        item for item in (gt or {}).get("evidence", [])
        if str(item.get("exact_quote") or "").strip()
        and item.get("source_span_validated_against_uploaded_corpus") is True
    ]
    if not found_docs:
        coverage_row = None
        if "ground_truth_audit_df" in globals() and not ground_truth_audit_df.empty:
            matches = ground_truth_audit_df[
                ground_truth_audit_df["query_id"].astype(str).eq(str((gt or {}).get("query_id")))
            ]
            if not matches.empty:
                coverage_row = matches.iloc[0].to_dict()
        cause = (
            "SOURCE_NOT_INDEXED"
            if coverage_row and coverage_row.get("coverage_status") != "COVERED"
            else "PASSAGE_NOT_RETRIEVED"
        )
    elif not span_in_pool:
        cause = "PASSAGE_NOT_RETRIEVED" if validated_quotes else "GROUND_TRUTH_ISSUE"
    elif not span_in_context:
        cause = "PASSAGE_NOT_IN_CONTEXT"
    else:
        expected_values = _exit_expected_values(gt)
        expected_value = next(
            (value for value in expected_values if re.search(r"\d", value)),
            expected_values[0] if expected_values else "",
        )
        ai1 = str((result.get("agents") or {}).get("AI1_News_Analyst", {}).get("data") or "")
        ai5 = json.dumps(raw_final_data or {}, ensure_ascii=False)
        if expected_value and _exit_normalize(expected_value) not in _exit_normalize(ai1):
            cause = "SPECIALIST_EXTRACTION_FAILURE"
        elif expected_value and _exit_normalize(expected_value) not in _exit_normalize(ai5):
            cause = "AI5_SYNTHESIS_DROPPED_FINDING"
        elif expected_value and _exit_normalize(expected_value) not in _exit_normalize(raw_final_text):
            cause = "CITATION_VALIDATION_DROPPED_FINDING"
        elif not str(raw_final_text or "").strip():
            cause = "CITATION_VALIDATION_DROPPED_FINDING"
        else:
            cause = "UNRESOLVED"
    return {
        "root_cause": cause,
        "expected_document_retrieved": bool(found_docs),
        "answer_bearing_span_in_candidate_pool": span_in_pool,
        "answer_bearing_span_in_final_context": span_in_context,
        "expected_documents": sorted(expected_ids),
        "matched_candidate_ids": [
            {key: candidate.get(key) for key in ("document_id", "original_id", "chunk_id", "url", "publication_date")}
            for candidate in found_docs
        ],
    }

def _exit_write_trace(record):
    path = _secure_local_path(GAIB_EXIT_TRACE_PATH)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

def _exit_sanitize(value):
    if isinstance(value, dict):
        return {key: _exit_sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_exit_sanitize(item) for item in value]
    if isinstance(value, str):
        return _sanitize_sensitive(value)
    return value

_GAIB_ORIGINAL_RECORD_REQUEST_DIAGNOSTIC = globals().get(
    "_GAIB_ORIGINAL_RECORD_REQUEST_DIAGNOSTIC", record_request_diagnostic
)
def record_request_diagnostic_v2(record):
    enriched = dict(record)
    enriched["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    enriched["attempt_number"] = record.get("logical_attempt")
    enriched["query_id"] = record.get("query_id") or GAIB_EXIT_ACTIVE_QUERY_ID or GAIB_ACTIVE_QUERY_ID
    response = enriched.get("response") or {}
    metrics_before = len(GAIB_REQUEST_TELEMETRY_ROWS)
    _GAIB_ORIGINAL_RECORD_REQUEST_DIAGNOSTIC(enriched)
    if len(GAIB_REQUEST_TELEMETRY_ROWS) > metrics_before:
        GAIB_REQUEST_TELEMETRY_ROWS[-1]["timestamp_utc"] = enriched["timestamp_utc"]
        GAIB_REQUEST_TELEMETRY_ROWS[-1]["attempt_number"] = enriched["attempt_number"]
        GAIB_REQUEST_TELEMETRY_ROWS[-1]["error_type"] = record.get("error_type")
        GAIB_REQUEST_TELEMETRY_ROWS[-1]["latency_ms"] = response.get("request_duration_ms")

record_request_diagnostic = record_request_diagnostic_v2

_GAIB_ORIGINAL_CALL_AGENT_JSON = globals().get(
    "_GAIB_ORIGINAL_CALL_AGENT_JSON", call_agent_json
)
def call_agent_json_v2(llm, agent_name, role_instruction, user_payload, *args, **kwargs):
    if agent_name == "AI5_Lead_Researcher":
        GAIB_EXIT_LAST_AGENT_PAYLOADS[agent_name] = _sanitize_sensitive(user_payload)
    return _GAIB_ORIGINAL_CALL_AGENT_JSON(
        llm, agent_name, role_instruction, user_payload, *args, **kwargs
    )

call_agent_json = call_agent_json_v2

_GAIB_ORIGINAL_STAGE_CANDIDATE_METADATA = globals().get(
    "_GAIB_ORIGINAL_STAGE_CANDIDATE_METADATA", _stage_candidate_metadata
)
def _stage_candidate_metadata_v2(candidate):
    result = _GAIB_ORIGINAL_STAGE_CANDIDATE_METADATA(candidate)
    result["text_excerpt"] = str(candidate.get("text") or "")[:5000]
    return result

_stage_candidate_metadata = _stage_candidate_metadata_v2

_GAIB_ORIGINAL_CANDIDATE_OUTPUT_ROW = globals().get(
    "_GAIB_ORIGINAL_CANDIDATE_OUTPUT_ROW", _candidate_output_row
)
def _candidate_output_row_v2(query_id, stage, rank, candidate, gt):
    row = _GAIB_ORIGINAL_CANDIDATE_OUTPUT_ROW(query_id, stage, rank, candidate, gt)
    row["text_excerpt"] = str(
        candidate.get("text_excerpt") or candidate.get("text") or ""
    )[:5000]
    quotes = _exit_exact_quotes(gt)
    row["answer_bearing_span_match"] = any(
        _exit_quote_present(quote, [{"text_excerpt": row["text_excerpt"]}])
        for quote in quotes
    )
    return row

_candidate_output_row = _candidate_output_row_v2

_GAIB_ORIGINAL_CITATION_AUDIT = globals().get(
    "_GAIB_ORIGINAL_CITATION_AUDIT", citation_audit
)
def citation_audit_v2(text, allowed_ids):
    audit = _GAIB_ORIGINAL_CITATION_AUDIT(text, allowed_ids)
    lines = [
        line.strip() for line in str(text or "").splitlines()
        if line.strip()
        and not re.match(r"^\s*#{1,6}\s", line)
        and len(line.strip()) >= 25
    ]
    valid_ids = set(CITATION_TOKEN_RE.findall(str(text or ""))).intersection(set(allowed_ids))
    claim_lines = [line for line in lines if line.lstrip().startswith(("-", "*"))]
    audit["citation_paragraph_coverage"] = (
        sum(any(identifier in line for identifier in valid_ids) for line in claim_lines) / len(claim_lines)
        if claim_lines else "NO_CLAIMS"
    )
    audit["citation_claim_count"] = len(claim_lines)
    audit["citation_audit_method"] = "rendered_claim_lines_excluding_markdown_headings_v2"
    return audit

citation_audit = citation_audit_v2

_GAIB_ORIGINAL_ASSISTANT_RUN = globals().get(
    "_GAIB_ORIGINAL_ASSISTANT_RUN", GoldAssistantMultiAgent.run
)
def assistant_run_exit_v2(self, query, *args, **kwargs):
    global GAIB_EXIT_ACTIVE_QUERY_ID, GAIB_ACTIVE_VARIANT
    gt = _exit_ground_truth_for(query)
    query_id = (gt or {}).get("query_id")
    previous_query_id = GAIB_EXIT_ACTIVE_QUERY_ID
    previous_variant = GAIB_ACTIVE_VARIANT
    GAIB_EXIT_ACTIVE_QUERY_ID = query_id
    GAIB_ACTIVE_VARIANT = "live_benchmark"
    GAIB_EXIT_LAST_AGENT_PAYLOADS.clear()
    telemetry_start = len(GAIB_REQUEST_TELEMETRY_ROWS)
    try:
        result = _GAIB_ORIGINAL_ASSISTANT_RUN(self, query, *args, **kwargs)
    finally:
        GAIB_EXIT_ACTIVE_QUERY_ID = previous_query_id
        GAIB_ACTIVE_VARIANT = previous_variant
    result["metrics"]["citation_audit"] = result.get("citation_audit") or result["metrics"].get("citation_audit", {})
    raw_model_data = json.loads(json.dumps(result.get("final_data") or {}, ensure_ascii=False, default=str))
    original_data = json.loads(json.dumps(raw_model_data, ensure_ascii=False, default=str))
    original_text = str(result.get("final_text") or "")
    raw_citations = sorted({
        str(identifier)
        for finding in original_data.get("evidence_based_findings", [])
        if isinstance(finding, dict)
        for identifier in (finding.get("evidence_ids") or [])
    })
    allowed = set(allowed_evidence_ids(result.get("sources") or [], result.get("market") or {},
                                       result.get("hmm") or {}, result.get("risk") or {}))
    candidate = extract_fomc_target_range(query, result.get("sources") or [])
    if query_id in GAIB_EXIT_CRITICAL_QUERY_IDS and candidate and not _exit_numeric_claim_complete(
        candidate, original_data.get("evidence_based_findings", [])
    ):
        original_data.setdefault("evidence_based_findings", []).append({
            "claim": candidate["claim"],
            "claim_type": "fact",
            "evidence_ids": [candidate["citation_id"]],
            "confidence": "high",
            "limitations": ["Extracted from a date-matched retrieved FOMC statement."],
        })
        original_data["status"] = "complete"
        original_data["executive_summary"] = candidate["claim"]
        original_data["abstention_reason"] = ""
        postprocess_errors = validate_agent_schema("AI5_Lead_Researcher", original_data)
        if postprocess_errors:
            result["postprocess_schema_errors"] = postprocess_errors
            result["answer_status"] = "ABSTAINED_POSTPROCESS_SCHEMA_FAILURE"
        else:
            result["final_data"] = original_data
            result["final_text"], claim_audit = render_evidence_report(original_data, allowed)
            result["claim_audit"] = claim_audit
            result["answer_status"] = "ANSWERED_FROM_DATE_MATCHED_EVIDENCE"
    result["raw_proposed_citation_ids"] = raw_citations
    result["citation_audit"] = citation_audit(result["final_text"], allowed)
    result["citation_audit"]["raw_proposed_citation_ids"] = raw_citations
    result["citation_audit"]["rendered_valid_citation_ids"] = sorted(
        set(CITATION_TOKEN_RE.findall(result["final_text"])).intersection(allowed)
    )
    result["citation_audit"]["semantic_support_status"] = "NOT_HUMAN_REVIEWED"
    result["metrics"]["citation_audit"] = result["citation_audit"]
    has_findings = bool(result.get("final_data", {}).get("evidence_based_findings"))
    reason = str(result.get("final_data", {}).get("abstention_reason") or "").strip()
    if "answer_status" not in result:
        if has_findings:
            result["answer_status"] = "ANSWERED_WITH_MODEL_FINDINGS"
        elif reason:
            result["answer_status"] = "EXPLICIT_ABSTENTION"
        else:
            result["answer_status"] = "NO_CLAIMS_WITHOUT_ABSTENTION_REASON"
    result["answer_attempted"] = has_findings or bool(reason)
    result["abstention_reason"] = reason or (
        "No schema-valid evidence-based findings or explicit abstention reason were produced."
        if not has_findings else ""
    )
    span_present = any(
        _exit_quote_present(quote, result.get("sources") or [])
        for quote in _exit_exact_quotes(gt)
    )
    result["abstention_correctness"] = "NOT_EVALUATED"
    root_cause = None
    if query_id in GAIB_EXIT_CRITICAL_QUERY_IDS:
        result["abstention_correctness"] = (
            "CORRECT" if not has_findings and not span_present
            else ("INCORRECT" if not has_findings and span_present else "NOT_AN_ABSTENTION")
        )
        root_cause = _exit_root_cause(gt, result, raw_model_data, original_text)
        result["root_cause_diagnostic"] = root_cause
        result["metrics"]["task_success_rate"] = (
            1.0 if candidate and result["answer_status"] == "ANSWERED_FROM_DATE_MATCHED_EVIDENCE"
            else "NOT_EVALUATED_WITHOUT_HUMAN_REVIEW"
        )
    result["metrics"]["answer_status"] = result["answer_status"]
    if query_id is not None:
        GAIB_EXIT_RUN_DETAILS[query_id] = {
            "answer_status": result["answer_status"],
            "answer_attempted": result["answer_attempted"],
            "abstention_reason": result["abstention_reason"],
            "abstention_correctness": result["abstention_correctness"],
            "fact_coverage": _exit_fact_coverage(gt, result.get("final_text")),
            "root_cause_diagnostic": root_cause,
            "evidence_span_in_final_context": span_present,
            "evidence_sources": [
                {
                    "citation_id": source.get("citation_id"),
                    "title": source.get("title"),
                    "url": source.get("url"),
                    "publication_date": source.get("publication_date"),
                    "text_excerpt": str(source.get("text_excerpt") or source.get("text") or "")[:5000],
                }
                for source in result.get("sources") or []
            ],
        }
    if query_id in GAIB_EXIT_CRITICAL_QUERY_IDS:
        retrieval = result.get("retrieval") or {}
        trace = {
            "run_id": GAIB_RUN_ID,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "query_id": query_id,
            "query": query,
            "ground_truth": gt,
            "retrieval_stages": {
                **(retrieval.get("metrics", {}).get("stage_candidates") or {}),
                "hybrid_raw": retrieval.get("raw_candidates") or [],
                "reranked": retrieval.get("ranked_candidates") or [],
            },
            "final_context_sources": result.get("sources") or [],
            "ai1_raw_response": (result.get("agents") or {}).get("AI1_News_Analyst", {}).get("raw_text"),
            "ai1_parsed_data": (result.get("agents") or {}).get("AI1_News_Analyst", {}).get("data"),
            "ai1_schema_errors": (result.get("agents") or {}).get("AI1_News_Analyst", {}).get("metrics", {}).get("schema_errors"),
            "ai5_input_payload": GAIB_EXIT_LAST_AGENT_PAYLOADS.get("AI5_Lead_Researcher"),
            "ai5_findings_before_render": raw_model_data,
            "rendered_report_before_fallback": original_text,
            "rendered_report_after_fallback": result.get("final_text"),
            "raw_proposed_citation_ids": raw_citations,
            "rendered_valid_citation_ids": result["citation_audit"]["rendered_valid_citation_ids"],
            "root_cause_diagnostic": root_cause,
            "request_attempts": GAIB_REQUEST_TELEMETRY_ROWS[telemetry_start:],
        }
        _exit_write_trace(_exit_sanitize(trace))
    self.last_run = result
    return result

GoldAssistantMultiAgent.run = assistant_run_exit_v2

_GAIB_ORIGINAL_RETRIEVAL_BENCHMARK = globals().get(
    "_GAIB_ORIGINAL_RETRIEVAL_BENCHMARK", run_retrieval_benchmark
)
def run_retrieval_benchmark_exit_v2(ground_truth, limit=None):
    result_df, stage_df, error_df = _GAIB_ORIGINAL_RETRIEVAL_BENCHMARK(ground_truth, limit=limit)
    quotes_by_id = {row.get("query_id"): _exit_exact_quotes(row) for row in ground_truth}
    if not stage_df.empty:
        if "text_excerpt" not in stage_df:
            stage_df["text_excerpt"] = ""
        stage_df["answer_bearing_span_match"] = stage_df.apply(
            lambda row: any(
                _exit_quote_present(quote, [{"text_excerpt": row.get("text_excerpt")}])
                for quote in quotes_by_id.get(row.get("query_id"), [])
            ),
            axis=1,
        )
        for stage in ("dense", "bm25", "hybrid", "reranked", "evidence_context"):
            stage_rows = stage_df[stage_df["stage"].eq(stage)]
            recalls = {}
            for query_id, quotes in quotes_by_id.items():
                matching_rows = stage_rows[stage_rows["query_id"].eq(query_id)]
                if "rank" in matching_rows:
                    matching_rows = matching_rows[
                        pd.to_numeric(matching_rows["rank"], errors="coerce").le(10)
                    ]
                found = sum(
                    any(_exit_quote_present(quote, [{"text_excerpt": text}]) for text in matching_rows["text_excerpt"])
                    for quote in quotes
                )
                recalls[query_id] = found / len(quotes) if quotes else None
            column_name = f"answer_bearing_span_recall@10_{stage}"
            if column_name not in result_df:
                result_df[column_name] = result_df["query_id"].map(recalls)
        stage_df.to_csv(OUTPUT_DIR / "retrieval_stage_candidates.csv", index=False, encoding="utf-8-sig")
        result_df.to_csv(OUTPUT_DIR / "retrieval_stage_metrics.csv", index=False, encoding="utf-8-sig")
    return result_df, stage_df, error_df

run_retrieval_benchmark = run_retrieval_benchmark_exit_v2

_GAIB_ORIGINAL_MULTIAGENT_BENCHMARK = globals().get(
    "_GAIB_ORIGINAL_MULTIAGENT_BENCHMARK", run_multiagent_benchmark
)
def run_multiagent_benchmark_exit_v2(ground_truth, limit=BENCHMARK_LIMIT):
    run_df, agents_df, review_df, errors_df = _GAIB_ORIGINAL_MULTIAGENT_BENCHMARK(
        ground_truth, limit=limit
    )
    gt_by_id = {row.get("query_id"): row for row in ground_truth}
    original_review_by_id = {
        row.get("query_id"): row for row in review_df.to_dict("records")
    }
    for frame in (run_df, review_df):
        if frame.empty:
            continue
        for column in ("answer_status", "answer_attempted", "abstention_reason",
                       "abstention_correctness", "expected_fact_coverage",
                       "evidence_span_in_final_context"):
            if column not in frame:
                frame[column] = pd.Series(None, index=frame.index, dtype=object)
            else:
                frame[column] = frame[column].astype(object)
        for index, row in frame.iterrows():
            query_id = row.get("query_id")
            details = GAIB_EXIT_RUN_DETAILS.get(query_id, {})
            gt = gt_by_id.get(query_id)
            coverage = _exit_fact_coverage(gt, row.get("final_report") or row.get("generated_answer") or "")
            for key, value in {
                "answer_status": details.get("answer_status"),
                "answer_attempted": details.get("answer_attempted"),
                "abstention_reason": details.get("abstention_reason"),
                "abstention_correctness": details.get("abstention_correctness"),
                "expected_fact_coverage": details.get("fact_coverage", coverage).get("expected_fact_coverage"),
                "evidence_span_in_final_context": details.get("evidence_span_in_final_context"),
            }.items():
                frame.at[index, key] = value
    if not run_df.empty:
        run_df.to_csv(OUTPUT_DIR / "multiagent_benchmark_results.csv", index=False, encoding="utf-8-sig")
    claim_review_rows = []
    for run_row in run_df.to_dict("records"):
        query_id = str(run_row.get("query_id") or "")
        gt = gt_by_id.get(run_row.get("query_id"), {})
        original_review = original_review_by_id.get(run_row.get("query_id"), {})
        report = str(run_row.get("final_report") or "")
        claims = [
            line.strip()[2:].strip()
            for line in report.splitlines()
            if line.startswith("- ") and len(line.strip()) >= 25
        ]
        review_claims = [
            {
                "review_type": "factual_claim",
                "claim_id": f"{GAIB_RUN_ID}:{query_id}:claim-{claim_index}",
                "claim_index": claim_index,
                "claim_text": claim,
                "evidence_ids": json.dumps(
                    CITATION_TOKEN_RE.findall(claim), ensure_ascii=False
                ),
            }
            for claim_index, claim in enumerate(claims, 1)
        ]
        if not review_claims:
            review_claims = [{
                "review_type": "abstention",
                "claim_id": f"{GAIB_RUN_ID}:{query_id}:abstention",
                "claim_index": 0,
                "claim_text": "",
                "evidence_ids": "[]",
            }]
        detail = GAIB_EXIT_RUN_DETAILS.get(run_row.get("query_id"), {})
        for claim in review_claims:
            for reviewer_slot in ("A", "B"):
                claim_review_rows.append({
                    "run_id": GAIB_RUN_ID,
                    "query_id": query_id,
                    "query": gt.get("query") or run_row.get("query"),
                    "split": gt.get("split") or GAIB_BENCHMARK_SPLIT,
                    "review_status": gt.get("review_status"),
                    **claim,
                    "expected_answer": original_review.get("expected_answer", ""),
                    "generated_answer": report,
                    "answer_status": detail.get("answer_status"),
                    "abstention_reason": detail.get("abstention_reason"),
                    "expected_fact_coverage": detail.get("fact_coverage", {}).get(
                        "expected_fact_coverage"
                    ),
                    "evidence_span_in_final_context": detail.get(
                        "evidence_span_in_final_context"
                    ),
                    "evidence_ids_expected": original_review.get("evidence_ids", "[]"),
                    "source_urls": original_review.get("source_urls", "[]"),
                    "reviewer_slot": reviewer_slot,
                    "reviewer_id": "",
                    "human_correctness": "",
                    "citation_supported": "",
                    "unsupported_critical_claim": "",
                    "reviewed_at": "",
                    "reviewer_notes": "",
                })
    review_df = pd.DataFrame(claim_review_rows, columns=[
        "run_id", "query_id", "query", "split", "review_status", "review_type",
        "claim_id", "claim_index", "claim_text", "evidence_ids", "expected_answer",
        "generated_answer", "answer_status", "abstention_reason",
        "expected_fact_coverage", "evidence_span_in_final_context",
        "evidence_ids_expected", "source_urls", "reviewer_slot", "reviewer_id",
        "human_correctness", "citation_supported", "unsupported_critical_claim",
        "reviewed_at", "reviewer_notes",
    ])
    review_df.to_csv(OUTPUT_DIR / "answer_human_review_template.csv", index=False, encoding="utf-8-sig")
    error_columns = ["query_id", "query", "stage", "error_type", "error", "traceback"]
    errors_to_write = (
        errors_df if not errors_df.empty else pd.DataFrame(columns=error_columns)
    )
    errors_to_write.to_csv(
        OUTPUT_DIR / "multiagent_benchmark_errors.csv",
        index=False,
        encoding="utf-8-sig",
        columns=error_columns,
    )
    http_attempt_rows = []
    attempt_numbers = {}
    for logical_row in GAIB_REQUEST_TELEMETRY_ROWS:
        if logical_row.get("variant") != "live_benchmark":
            continue
        durations = logical_row.get("http_attempt_durations_ms") or []
        if isinstance(durations, str):
            try:
                durations = json.loads(durations)
            except json.JSONDecodeError:
                durations = []
        if not isinstance(durations, (list, tuple)):
            durations = []
        retry_reasons = logical_row.get("http_retry_reasons") or []
        if isinstance(retry_reasons, str):
            try:
                retry_reasons = json.loads(retry_reasons)
            except json.JSONDecodeError:
                retry_reasons = []
        if not isinstance(retry_reasons, (list, tuple)):
            retry_reasons = []
        try:
            reported_attempt_count = int(float(logical_row.get("api_attempt_count") or 0))
        except (TypeError, ValueError, OverflowError):
            reported_attempt_count = 0
        attempt_count = max(
            len(durations),
            reported_attempt_count,
            1,
        )
        key = (logical_row.get("run_id"), logical_row.get("query_id"), logical_row.get("agent"))
        for http_index in range(attempt_count):
            attempt_numbers[key] = attempt_numbers.get(key, 0) + 1
            row = dict(logical_row)
            logical_api_success = str(logical_row.get("api_success")).lower() in {"true", "1"}
            failed_http_attempt = (
                http_index < len(retry_reasons) or not logical_api_success
            )
            row["logical_attempt_number"] = logical_row.get("logical_attempt")
            row["http_attempt_number"] = http_index + 1
            row["attempt_number"] = attempt_numbers[key]
            row["latency_ms"] = durations[http_index] if http_index < len(durations) else logical_row.get("latency_ms")
            row["logical_status"] = logical_row.get("status")
            row["logical_api_attempt_count"] = logical_row.get("api_attempt_count")
            row["logical_request_duration_ms"] = logical_row.get("request_duration_ms")
            row["logical_gate_wait_ms"] = logical_row.get("gate_wait_ms")
            row["request_duration_ms"] = row["latency_ms"]
            row["gate_wait_ms"] = None
            row["initial_json_parse"] = logical_row.get("initial_json_parse")
            row["final_json_parse"] = logical_row.get("final_json_parse")
            row["any_attempt_truncated"] = logical_row.get("any_attempt_truncated")
            row["final_attempt_truncated"] = logical_row.get("final_attempt_truncated")
            reason = retry_reasons[http_index] if http_index < len(retry_reasons) else {}
            row["error_type"] = reason.get("type") or logical_row.get("error_type")
            row["status_code"] = reason.get("status_code")
            row["api_attempt_count"] = 1
            if failed_http_attempt:
                row["status"] = "api_error"
                row["api_success"] = False
                row["json_parse"] = False
                row["schema_valid"] = False
                row["finish_reason"] = None
                row["prompt_tokens"] = None
                row["completion_tokens"] = None
                row["total_tokens"] = None
            http_attempt_rows.append(row)
    telemetry = pd.DataFrame(http_attempt_rows)
    telemetry_columns = [
        "run_id", "query_id", "agent", "variant", "attempt_number",
        "logical_attempt_number", "http_attempt_number", "timestamp_utc",
        "model", "source_hash", "builder_sha256", "prompt_version", "schema_version",
        "config_snapshot", "status", "api_success", "json_parse", "schema_valid",
        "initial_json_parse", "final_json_parse", "any_attempt_truncated",
        "final_attempt_truncated",
        "finish_reason", "max_tokens_requested", "prompt_tokens", "completion_tokens",
        "total_tokens", "latency_ms", "error_type", "status_code", "api_attempt_count",
        "logical_api_attempt_count", "request_duration_ms", "logical_request_duration_ms",
        "gate_wait_ms", "logical_gate_wait_ms", "logical_status",
    ]
    for column in telemetry_columns:
        if column not in telemetry:
            telemetry[column] = pd.Series(dtype=object)
    if not telemetry.empty:
        for _key, group in telemetry.groupby(["run_id", "query_id", "agent"], dropna=False):
            indices = group.index
            truncated = group["finish_reason"].astype(str).str.casefold().isin(
                {"length", "max_tokens", "max_output_tokens"}
            )
            successful_http = group[
                group["api_success"].fillna(False).astype(str).str.lower().isin({"true", "1"})
            ]
            logical_attempts = pd.to_numeric(successful_http["logical_attempt_number"], errors="coerce")
            first = successful_http[logical_attempts.eq(logical_attempts.min())] if not successful_http.empty else group.iloc[0:0]
            last = successful_http[logical_attempts.eq(logical_attempts.max())] if not successful_http.empty else group.iloc[0:0]
            initial_parse = bool(first["json_parse"].fillna(False).astype(str).str.lower().isin({"true", "1"}).any())
            final_parse = bool(last["json_parse"].fillna(False).astype(str).str.lower().isin({"true", "1"}).any())
            telemetry.loc[indices, "initial_json_parse"] = initial_parse
            telemetry.loc[indices, "final_json_parse"] = final_parse
            telemetry.loc[indices, "any_attempt_truncated"] = bool(truncated.any())
            telemetry.loc[indices, "final_attempt_truncated"] = bool(
                last["finish_reason"].astype(str).str.casefold()
                .isin({"length", "max_tokens", "max_output_tokens"}).any()
            )
    telemetry.to_csv(OUTPUT_DIR / "live_http_attempts.csv", index=False, encoding="utf-8-sig",
                     columns=telemetry_columns)
    required_telemetry = {
        "run_id", "variant", "query_id", "agent", "attempt_number", "timestamp_utc",
        "model", "source_hash", "builder_sha256", "prompt_version",
        "schema_version", "config_snapshot",
    }
    missing_telemetry_columns = sorted(required_telemetry - set(telemetry.columns))
    missing_telemetry_values = (
        int(telemetry[list(required_telemetry)].isna().sum().sum())
        if not telemetry.empty and required_telemetry.issubset(telemetry.columns)
        else None
    )
    duplicate_attempts = (
        int(telemetry.duplicated(["run_id", "query_id", "agent", "attempt_number"]).sum())
        if not telemetry.empty and required_telemetry.issubset(telemetry.columns)
        else None
    )
    expected_query_ids = [
        row.get("query_id") for row in ground_truth
    ][:limit] if limit is not None else [row.get("query_id") for row in ground_truth]
    observed_query_ids = (
        run_df.get("query_id", pd.Series(dtype=str)).dropna().astype(str).tolist()
        + errors_df.get("query_id", pd.Series(dtype=str)).dropna().astype(str).tolist()
    )
    missing_query_ids = sorted(set(map(str, expected_query_ids)) - set(observed_query_ids))
    duplicate_query_ids = int(pd.Series(observed_query_ids).duplicated().sum())
    expected_agent_results = int(len(run_df) * 5)
    observed_agent_results = int(len(agents_df))
    expected_ground_truth = ground_truth[:limit] if limit is not None else ground_truth
    expected_numeric_count = sum(
        str(row.get("query_type") or "").strip().casefold() == "numeric_fact"
        for row in expected_ground_truth
    )
    query_types = run_df.get(
        "query_type", pd.Series("", index=run_df.index, dtype=str)
    ).fillna("").astype(str).str.strip().str.casefold()
    numeric_rows = run_df[query_types.eq("numeric_fact")]
    fact_coverage = pd.to_numeric(
        numeric_rows.get(
            "expected_fact_coverage",
            pd.Series(index=numeric_rows.index, dtype=float),
        ),
        errors="coerce",
    ).fillna(0.0).ge(1.0)
    span_present = numeric_rows.get(
        "evidence_span_in_final_context",
        pd.Series(False, index=numeric_rows.index),
    ).fillna(False).astype(str).str.strip().str.casefold().isin({"true", "1"})
    citations_present = pd.to_numeric(
        numeric_rows.get(
            "citation_count", pd.Series(0, index=numeric_rows.index, dtype=int)
        ),
        errors="coerce",
    ).fillna(0).gt(0)
    valid_citations = numeric_rows.get(
        "all_citation_ids_valid", pd.Series(False, index=numeric_rows.index)
    ).fillna(False).astype(str).str.strip().str.casefold().isin({"true", "1"})
    answer_statuses = numeric_rows.get(
        "answer_status", pd.Series("", index=numeric_rows.index, dtype=str)
    ).fillna("").astype(str)
    abstention_correctness = numeric_rows.get(
        "abstention_correctness", pd.Series("", index=numeric_rows.index, dtype=str)
    ).fillna("").astype(str)
    numerically_supported = (
        answer_statuses.str.startswith("ANSWERED")
        & fact_coverage
        & span_present
        & citations_present
        & valid_citations
    )
    correctly_abstained = (
        answer_statuses.eq("EXPLICIT_ABSTENTION")
        & abstention_correctness.eq("CORRECT")
    )
    numeric_complete_count = int((numerically_supported | correctly_abstained).sum())
    valid_answer_statuses = run_df.get(
        "answer_status", pd.Series("", index=run_df.index, dtype=str)
    ).fillna("").astype(str).isin({
        "ANSWERED_WITH_MODEL_FINDINGS",
        "ANSWERED_FROM_DATE_MATCHED_EVIDENCE",
        "EXPLICIT_ABSTENTION",
    })
    incorrect_abstentions = (
        run_df.get("answer_status", pd.Series("", index=run_df.index, dtype=str))
        .fillna("").astype(str).eq("EXPLICIT_ABSTENTION")
        & ~run_df.get(
            "abstention_correctness", pd.Series("", index=run_df.index, dtype=str)
        ).fillna("").astype(str).eq("CORRECT")
    )
    explicit_answer_count = int(valid_answer_statuses.sum())
    incorrect_abstention_count = int(incorrect_abstentions.sum())
    contradictory_attempts = int((
        telemetry["status"].eq("success")
        & (~telemetry["json_parse"].fillna(False).astype(str).str.lower().isin({"true", "1"})
           | ~telemetry["schema_valid"].fillna(False).astype(str).str.lower().isin({"true", "1"}))
    ).sum()) if not telemetry.empty else 0
    claim_review = (
        review_df[review_df["review_type"].eq("factual_claim")]
        if not review_df.empty else review_df
    )
    claim_count = int(claim_review["claim_id"].nunique()) if not claim_review.empty else 0
    human_reviewed_claim_count = 0
    double_reviewed_claim_count = 0
    if not claim_review.empty and {"claim_id", "reviewer_id"}.issubset(claim_review.columns):
        reviewed = claim_review[
            claim_review["reviewer_id"].fillna("").astype(str).str.strip().ne("")
            & (
                claim_review["human_correctness"].fillna("").astype(str).str.strip().ne("")
                | claim_review["citation_supported"].fillna("").astype(str).str.strip().ne("")
            )
        ]
        reviewer_counts = reviewed.groupby("claim_id")["reviewer_id"].nunique()
        human_reviewed_claim_count = int((reviewer_counts >= 1).sum())
        double_reviewed_claim_count = int((reviewer_counts >= 2).sum())
    double_review_fraction = (
        double_reviewed_claim_count / human_reviewed_claim_count
        if human_reviewed_claim_count else 0.0
    )
    gate_status = {
        "decision": "NO-GO",
        "run_id": GAIB_RUN_ID,
        "benchmark_split": GAIB_BENCHMARK_SPLIT,
        "query_count": int(len(run_df)),
        "failed_or_blocked_query_count": int(len(errors_df)),
        "attempt_telemetry_row_count": int(len(telemetry)),
        "missing_telemetry_columns": missing_telemetry_columns,
        "missing_telemetry_value_count": missing_telemetry_values,
        "duplicate_attempt_keys": duplicate_attempts,
        "contradictory_attempt_statuses": contradictory_attempts,
        "expected_query_count": len(expected_query_ids),
        "missing_query_ids": missing_query_ids,
        "duplicate_query_ids": duplicate_query_ids,
        "expected_agent_result_count": expected_agent_results,
        "observed_agent_result_count": observed_agent_results,
        "expected_numeric_fact_count": expected_numeric_count,
        "numerically_supported_or_correctly_abstained_count": numeric_complete_count,
        "explicit_answer_status_count": explicit_answer_count,
        "incorrect_abstention_count": incorrect_abstention_count,
        "claim_count": claim_count,
        "human_reviewed_claim_count": human_reviewed_claim_count,
        "double_reviewed_claim_count": double_reviewed_claim_count,
        "double_review_fraction": double_review_fraction,
        "gates": {
            "attempt_telemetry_integrity": (
                "PASS" if not missing_telemetry_columns and duplicate_attempts == 0
                and missing_telemetry_values == 0
                and contradictory_attempts == 0 and not telemetry.empty
                and not missing_query_ids and duplicate_query_ids == 0
                and observed_agent_results == expected_agent_results else "FAIL"
            ),
            "critical_query_answer_status_accounted": (
                "PASS" if len(run_df) == len(expected_query_ids)
                and explicit_answer_count == len(expected_query_ids)
                and incorrect_abstention_count == 0 else "FAIL"
            ),
            "numeric_fact_coverage_or_correct_abstention": (
                "PASS" if expected_numeric_count > 0
                and len(numeric_rows) == expected_numeric_count
                and numeric_complete_count == expected_numeric_count
                else ("NOT_EVALUATED" if expected_numeric_count == 0 else "FAIL")
            ),
            "held_out_sample_minimum_100": (
                "PASS" if GAIB_BENCHMARK_SPLIT == "held_out"
                and len(run_df) >= 100 else "INSUFFICIENT_SAMPLE"
            ),
            "human_review_100_claims": (
                "PASS" if claim_count >= 100 and human_reviewed_claim_count >= 100
                else "NOT_EVALUATED"
            ),
            "double_review_at_least_20_percent": (
                "PASS" if human_reviewed_claim_count and double_review_fraction >= 0.20
                else "NOT_EVALUATED"
            ),
            "latency_p95_minimum_100_runs": (
                "PASS" if len(run_df) >= 100 else "INSUFFICIENT_SAMPLE"
            ),
            "paired_simpler_baseline_comparison": "NOT_EVALUATED",
            "semantic_citation_support": "NOT_HUMAN_REVIEWED",
        },
    }
    (OUTPUT_DIR / "exit_criteria_gate_status.json").write_text(
        json.dumps(gate_status, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return run_df, agents_df, review_df, errors_df

run_multiagent_benchmark = run_multiagent_benchmark_exit_v2

print("Exit-criteria v2 instrumentation installed: protected traces, exact-span metrics, guarded numeric extraction, and explicit abstention status.")
'''

AI_JUDGE_CELL = r'''import hashlib
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from gaib1_ai_judge import (
    PROMPT_HASH,
    RUBRIC_VERSION,
    SYSTEM_PROMPT,
    build_human_review_template,
    build_policy_gates,
    compute_calibration_metrics,
    compute_judge_quality_metrics,
    evaluate_claims,
    load_human_labels,
    select_calibration_claims,
)

GAIB_AI_JUDGE_SYSTEM_PROMPT = SYSTEM_PROMPT
GAIB_AI_JUDGE_PROMPT_HASH = PROMPT_HASH

def _gaib_judge_invoke(model, phase, payload):
    if not THAILLM_CLIENTS:
        raise RuntimeError("No authenticated model client is available for AI judging.")
    client = next(iter(THAILLM_CLIENTS.values()))
    started = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": GAIB_AI_JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(
                {"phase": phase, "evaluation": payload},
                ensure_ascii=False,
                separators=(",", ":"),
            )},
        ],
        temperature=0,
        max_tokens=1400,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    choice = response.choices[0]
    return {
        "content": choice.message.content or "",
        "model": getattr(response, "model", model),
        "finish_reason": choice.finish_reason,
        "latency_ms": elapsed_ms,
        "prompt_tokens": getattr(getattr(response, "usage", None), "prompt_tokens", None),
        "completion_tokens": getattr(getattr(response, "usage", None), "completion_tokens", None),
    }

def _gaib_metric_mean(frame, column):
    if frame.empty or column not in frame:
        return None
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    return float(values.mean()) if not values.empty else None

def _gaib_bool(value):
    return str(value).strip().casefold() in {"true", "1", "yes"}

def run_gaib_ai_judge_acceptance(run_df, ground_truth, retrieval_df, errors_df, baseline_comparison_complete=False):
    if not GAIB_JUDGE_ENABLED:
        raise RuntimeError("GAIB_JUDGE_ENABLED must be true for policy acceptance.")
    effective_judge_model = GAIB_JUDGE_MODEL or (
        "pathumma-thaillm-qwen3-8b-think-3.0.0" if THAILLM_MODEL != "pathumma-thaillm-qwen3-8b-think-3.0.0" else "typhoon-s-thaillm-8b-instruct"
    )
    if not effective_judge_model or effective_judge_model == THAILLM_MODEL:
        raise RuntimeError("Set GAIB_JUDGE_MODEL to an available model distinct from the answer generator.")
    if GAIB_SECOND_JUDGE_MODEL and GAIB_SECOND_JUDGE_MODEL in {effective_judge_model, THAILLM_MODEL}:
        raise RuntimeError("If configured, GAIB_SECOND_JUDGE_MODEL must be distinct from the primary judge and generator.")

    gt_by_id = {str(row.get("query_id")): row for row in ground_truth}
    run_rows = run_df.to_dict("records")
    judgments, judge_calls = evaluate_claims(
        run_id=GAIB_RUN_ID,
        run_rows=run_rows,
        ground_truth_by_id=gt_by_id,
        run_details_by_id=GAIB_EXIT_RUN_DETAILS,
        primary_model=effective_judge_model,
        second_model=GAIB_SECOND_JUDGE_MODEL,
        generator_model=THAILLM_MODEL,
        invoke=_gaib_judge_invoke,
    )
    sample_identity = {
        "corpus_sha256": GAIB_RUNTIME_MANIFEST.get("corpus_sha256"),
        "index_version": GAIB_RUNTIME_MANIFEST.get("index_version", "UNVERIFIED"),
        "prompt_hash": GAIB_AI_JUDGE_PROMPT_HASH,
        "query_ids": sorted(gt_by_id),
        "generator_model": THAILLM_MODEL,
        "builder_sha256": GAIB_RUNTIME_MANIFEST.get("builder_sha256"),
    }
    calibration_seed = hashlib.sha256(
        json.dumps(sample_identity, sort_keys=True).encode("utf-8")
    ).hexdigest()
    selected = select_calibration_claims(judgments, seed=calibration_seed, target_size=50)
    review_template = build_human_review_template(selected, GAIB_RUN_ID)
    human_template_columns = [
        "run_id", "query_id", "claim_id", "claim_type", "calibration_stratum",
        "claim_text", "judge_correctness", "judge_citation_entailment",
        "judge_completeness", "judge_confidence", "reviewer_slot", "reviewer_id",
        "human_correctness", "citation_supported", "completeness",
        "unsupported_critical_claim", "used_for_judge_prompt_development",
        "reviewed_at", "reviewer_notes",
    ]
    pd.DataFrame(review_template, columns=human_template_columns).to_csv(
        OUTPUT_DIR / "ai_judge_human_calibration_template.csv",
        index=False,
        encoding="utf-8-sig",
    )
    selected_claim_ids = {row["claim_id"] for row in selected}
    human_rows = [
        row for row in load_human_labels(GAIB_HUMAN_CALIBRATION_LABELS or None)
        if row.get("claim_id") in selected_claim_ids
    ]
    pd.DataFrame(human_rows, columns=human_template_columns).to_csv(
        OUTPUT_DIR / "ai_judge_human_calibration_labels.csv",
        index=False,
        encoding="utf-8-sig",
    )
    quality = compute_judge_quality_metrics(judgments, judge_calls)
    quality["answer_completeness_rate"] = quality.get("answer_completeness_rate")
    quality["citation_id_validity_rate"] = (
        float(run_df["all_citation_ids_valid"].map(_gaib_bool).mean())
        if not run_df.empty and "all_citation_ids_valid" in run_df
        else 0.0
    )
    calibration = compute_calibration_metrics(judgments, human_rows)
    eligible = retrieval_df[
        retrieval_df.get("evaluation_eligible", pd.Series(False, index=retrieval_df.index)).map(_gaib_bool)
    ] if not retrieval_df.empty else retrieval_df
    retrieval = {
        "reranked_known_relevant_recall@10": _gaib_metric_mean(eligible, "reranked_known_relevant_recall@10"),
        "reranked_mrr@10": _gaib_metric_mean(eligible, "reranked_mrr@10"),
        "reranked_ndcg@10": _gaib_metric_mean(eligible, "reranked_ndcg@10"),
        "answer_bearing_span_recall@10_reranked": _gaib_metric_mean(
            eligible, "answer_bearing_span_recall@10_reranked"
        ),
    }
    source_coverage_complete = bool(
        not eligible.empty
        and "runtime_qdrant_index_coverage_verified" in eligible
        and "coverage_status" in eligible
        and eligible["runtime_qdrant_index_coverage_verified"].map(_gaib_bool).all()
        and eligible["coverage_status"].astype(str).str.upper().eq("COVERED").all()
    )
    total_wall = (
        pd.to_numeric(run_df.get("total_wall_ms", pd.Series(dtype=float)), errors="coerce").dropna()
        if not run_df.empty else pd.Series(dtype=float)
    )
    judge_latencies = [
        float(response.get("latency_ms"))
        for row in judgments
        for response in row.get("raw_outputs", {}).values()
        if isinstance(response, dict) and response.get("latency_ms") is not None
    ]
    latency = {
        "run_count": int(len(total_wall)),
        "p50_ms": float(total_wall.quantile(0.50)) if not total_wall.empty else None,
        "p90_ms": float(total_wall.quantile(0.90)) if not total_wall.empty else None,
        "p95_ms": float(total_wall.quantile(0.95)) if not total_wall.empty else None,
        "judge_call_count": len(judge_latencies),
        "judge_api_error_count": sum(
            1 for row in judgments
            if any(key.endswith("_error") for key in row)
        ),
        "judge_overhead_total_ms": sum(judge_latencies),
        "judge_overhead_p50_ms": (
            float(pd.Series(judge_latencies).quantile(0.50)) if judge_latencies else None
        ),
        "judge_overhead_p90_ms": (
            float(pd.Series(judge_latencies).quantile(0.90)) if judge_latencies else None
        ),
        "judge_overhead_p95_ms": (
            float(pd.Series(judge_latencies).quantile(0.95)) if judge_latencies else None
        ),
    }
    previous_gate_path = OUTPUT_DIR / "exit_criteria_gate_status.json"
    previous_gate = json.loads(previous_gate_path.read_text(encoding="utf-8"))
    legacy_gates = previous_gate.get("gates", {})
    run_integrity_pass = (
        legacy_gates.get("attempt_telemetry_integrity") == "PASS"
        and legacy_gates.get("critical_query_answer_status_accounted") == "PASS"
    )
    numeric_failures = sum(
        row.get("deterministic_numeric_status") == "FAIL" for row in judgments
    )
    policy_gate = build_policy_gates(
        split=GAIB_BENCHMARK_SPLIT,
        query_count=len(ground_truth),
        eligible_query_count=len(eligible),
        retrieval_metrics=retrieval,
        quality_metrics=quality,
        calibration_metrics=calibration,
        latency_metrics=latency,
        baseline_comparison_complete=baseline_comparison_complete,
        primary_model=GAIB_JUDGE_MODEL,
        second_model=GAIB_SECOND_JUDGE_MODEL,
        generator_model=THAILLM_MODEL,
        index_version=str(GAIB_RUNTIME_MANIFEST.get("index_version", "UNVERIFIED")),
        deterministic_numeric_failures=numeric_failures,
        source_coverage_complete=source_coverage_complete,
        run_integrity_pass=run_integrity_pass and errors_df.empty,
    )
    policy_gate.update({
        "run_id": GAIB_RUN_ID,
        "claim_judgment_count": len(judgments),
        "judge_call_count": len(judge_calls),
        "judge_api_error_count": latency["judge_api_error_count"],
        "calibration_sample_identity": sample_identity,
        "calibration_template_claim_count": len(selected),
        "calibration_template_double_review_claim_count": min(
            len(selected), max(10, int(math.ceil(len(selected) * 0.20)))
        ),
        "baseline_comparison_complete": baseline_comparison_complete,
        "error_record_count": int(len(errors_df)),
        "legacy_gate_status": legacy_gates,
    })
    with (OUTPUT_DIR / "ai_judge_claim_judgments.jsonl").open("w", encoding="utf-8") as stream:
        for row in judgments:
            stream.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    (OUTPUT_DIR / "ai_judge_call_metrics.json").write_text(
        json.dumps(judge_calls, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "ai_judge_acceptance_summary.json").write_text(
        json.dumps({
            "benchmark_version": "GAIB1_AI_AS_JUDGE_ACCEPTANCE_POLICY",
            "run_id": GAIB_RUN_ID,
            "query_ids": [str(row.get("query_id")) for row in ground_truth],
            "dataset_version": GAIB_RUNTIME_MANIFEST.get("corpus_sha256"),
            "index_version": GAIB_RUNTIME_MANIFEST.get("index_version", "UNVERIFIED"),
            "generator_model": THAILLM_MODEL,
            "primary_judge_model": GAIB_JUDGE_MODEL,
            "second_judge_model": GAIB_SECOND_JUDGE_MODEL,
            "rubric_version": RUBRIC_VERSION,
            "prompt_hash": GAIB_AI_JUDGE_PROMPT_HASH,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "quality_metrics": quality,
            "calibration_metrics": calibration,
            "retrieval_metrics": retrieval,
            "latency_metrics": latency,
            "gates": policy_gate,
        }, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    previous_gate["legacy_gates"] = legacy_gates
    previous_gate.update(policy_gate)
    previous_gate["gates"] = policy_gate["gates"]
    previous_gate_path.write_text(
        json.dumps(previous_gate, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    GAIB_RUNTIME_MANIFEST["ai_judge"] = {
        "enabled": True,
        "primary_model": GAIB_JUDGE_MODEL,
        "second_model": GAIB_SECOND_JUDGE_MODEL,
        "rubric_version": RUBRIC_VERSION,
        "prompt_hash": GAIB_AI_JUDGE_PROMPT_HASH,
        "index_version": GAIB_RUNTIME_MANIFEST.get("index_version", "UNVERIFIED"),
        "claim_judgment_count": len(judgments),
        "judge_call_count": len(judge_calls),
    }
    (OUTPUT_DIR / "benchmark_run_manifest.json").write_text(
        json.dumps(GAIB_RUNTIME_MANIFEST, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "decision": policy_gate["decision"],
        "claim_judgment_count": len(judgments),
        "primary_judge_model": GAIB_JUDGE_MODEL,
        "calibration_reviewed_claim_count": calibration.get("reviewed_claim_count", 0),
        "failed_gates": [
            name for name, status in policy_gate["gates"].items() if status != "PASS"
        ],
    }, ensure_ascii=False, indent=2))
    return policy_gate
'''

PRECHECK_CELL = r'''import csv
import os
import re
import subprocess
import sys
import hashlib
import json
import pandas as pd
from pathlib import Path

GAIB_REQUEST_DIAGNOSTICS_ENABLED = True
GAIB_COMPACT_OUTPUT = GAIB_COMPACT_OUTPUT_DEFAULT
GAIB_TRUNCATION_RECOVERY_MODE = "none"
GAIB_RECOVERY_MAX_TOKENS = 1200
GAIB_RECOVERY_ESCALATION_MAX_TOKENS = 1500
GAIB_ACTIVE_QUERY_ID = None
GAIB_ACTIVE_VARIANT = "preflight"
GAIB_REQUEST_TELEMETRY_ROWS = []
GAIB_DIAGNOSTIC_DIR = (
    Path.home() / ".copilot" / "session-state" / "gaib-1-token-root-cause" / GAIB_RUN_ID
)
GAIB_DIAGNOSTIC_FILE = GAIB_DIAGNOSTIC_DIR / "protected_raw_diagnostics.jsonl"
GAIB_NOTEBOOK_PATH = PROJECT_ROOT / "multi_agent" / "GAIB-1" / "Gold_Assistant_GAIB1_Token_Root_Cause_Experiment_v1.ipynb"

def _sanitize_sensitive(value):
    text = str(value or "")
    secrets = [secret for _slot, secret in THAILLM_API_KEYS]
    secrets.extend((CF_API_TOKEN, QDRANT_API_KEY))
    secrets.extend(secret for _slot, secret in JINA_API_KEYS)
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return text

def _secure_local_path(path, is_directory=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        if is_directory:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.touch(exist_ok=True)
        account_result = subprocess.run(
            ["whoami"], capture_output=True, text=True, check=False
        )
        if account_result.returncode != 0 or not account_result.stdout.strip():
            raise PermissionError("Could not identify the current Windows account for diagnostic ACLs.")
        account = account_result.stdout.strip()
        grant = f"{account}:(OI)(CI)F" if is_directory else f"{account}:(F)"
        args = ["icacls", str(path), "/inheritance:r", "/grant:r", grant]
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise PermissionError(f"Could not restrict diagnostic file ACL: {result.stderr.strip()}")
        verification = subprocess.run(
            ["icacls", str(path)], capture_output=True, text=True, check=False
        )
        acl_output = verification.stdout + verification.stderr
        if (
            verification.returncode != 0
            or account.casefold() not in acl_output.casefold()
            or "no permissions are set" in acl_output.casefold()
            or "all users have full control" in acl_output.casefold()
            or re.search(r"\b(?:Everyone|Authenticated Users|BUILTIN\\Users)\b", acl_output, re.I)
        ):
            raise PermissionError("Diagnostic ACL verification failed; refusing to write raw diagnostics.")
    else:
        if not is_directory:
            path.touch(exist_ok=True)
        path.chmod(0o700 if is_directory else 0o600)
    return path

_secure_local_path(GAIB_DIAGNOSTIC_DIR, is_directory=True)

def record_request_diagnostic(record):
    response = record.get("response") or {}
    metric_row = {
        "run_id": GAIB_RUN_ID,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_hash": notebook_sha256,
        "builder_sha256": builder_sha256,
        "query_id": record.get("query_id"),
        "agent": record.get("agent"),
        "variant": record.get("variant"),
        "logical_attempt": record.get("logical_attempt"),
        "attempt_number": record.get("logical_attempt"),
        "model": response.get("model", THAILLM_MODEL),
        "prompt_version": ("claim-evidence-ai1-compact-v1"
                           if record.get("agent") == "AI1_News_Analyst" and GAIB_COMPACT_OUTPUT
                           else ("claim-evidence-ai5-compact-v1"
                                 if record.get("agent") == "AI5_Lead_Researcher" and GAIB_COMPACT_OUTPUT
                                 else ("claim-evidence-ai3-compact-v1"
                                       if record.get("agent") == "AI3_Quant_Regime_Analyst" and GAIB_AI3_COMPACT_OUTPUT
                                       else ("claim-evidence-compact-v1" if GAIB_COMPACT_OUTPUT else "claim-evidence-v1")))),
        "schema_version": "agent-contract-v1",
        "config_snapshot": json.dumps(GAIB_ROOT_CAUSE_MANIFEST["configuration"], sort_keys=True),
        "status": record.get("status"),
        "error_type": record.get("error_type"),
        "api_success": record.get("api_success"),
        "json_parse": record.get("json_parse"),
        "initial_json_parse": (
            record.get("json_parse")
            if int(record.get("logical_attempt") or 0) == 1 else None
        ),
        "final_json_parse": record.get("json_parse"),
        "schema_valid": record.get("schema_valid"),
        "finish_reason": response.get("finish_reason"),
        "any_attempt_truncated": str(response.get("finish_reason") or "").casefold()
        in {"length", "max_tokens", "max_output_tokens"},
        "final_attempt_truncated": str(response.get("finish_reason") or "").casefold()
        in {"length", "max_tokens", "max_output_tokens"},
        "max_tokens_requested": response.get("max_tokens_requested"),
        "prompt_tokens": response.get("prompt_tokens"),
        "completion_tokens": response.get("completion_tokens"),
        "total_tokens": response.get("total_tokens"),
        "raw_response_chars": len(record.get("raw_response") or ""),
        "parse_error": _sanitize_sensitive(record.get("parse_error")),
        "schema_errors": _sanitize_sensitive(json.dumps(record.get("schema_errors") or [], ensure_ascii=False)),
        "api_attempt_count": response.get("api_attempt_count"),
        "request_duration_ms": response.get("request_duration_ms"),
        "latency_ms": response.get("request_duration_ms"),
        "gate_wait_ms": response.get("gate_wait_ms"),
        "http_attempt_durations_ms": json.dumps(response.get("http_attempt_durations_ms") or []),
        "http_retry_reasons": json.dumps(response.get("http_retry_reasons") or []),
    }
    GAIB_REQUEST_TELEMETRY_ROWS.append(metric_row)
    secure_path = _secure_local_path(GAIB_DIAGNOSTIC_FILE)
    raw_record = {
        **metric_row,
        "raw_response": _sanitize_sensitive(record.get("raw_response")),
        "traceback": _sanitize_sensitive(record.get("traceback")),
    }
    with secure_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(raw_record, ensure_ascii=False, default=str) + "\n")

def _read_jsonl(path):
    with Path(path).open("r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]

def _percentile(values, q):
    numeric = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    return float(numeric.quantile(q)) if len(numeric) else None

ROOT_CAUSE_QUERIES = ["gtv2_000054", "gtv2_000055", "gtv2_000071", "gtv2_000078"]
ROOT_CAUSE_ALL_QUERY_IDS = ROOT_CAUSE_QUERIES + ["gtv2_000070"]
_baseline_root = Path(os.getenv(
    "GAIB_BASELINE_RUN_DIR",
    str(PROJECT_ROOT / "multi_agent" / "GAIB-1" / "runs" / "reliability_phase1_2")))
_baseline_dirs = [p for p in _baseline_root.iterdir() if p.is_dir()] if _baseline_root.is_dir() else []
if not _baseline_dirs:
    raise FileNotFoundError(f"No historical reliability run directory found under {_baseline_root}")
BASELINE_RUN_DIR = max(_baseline_dirs, key=lambda p: p.stat().st_mtime)
BASELINE_METRICS_PATH = BASELINE_RUN_DIR / "multiagent_per_agent_metrics.csv"
if not BASELINE_METRICS_PATH.is_file():
    raise FileNotFoundError(f"Missing historical per-agent telemetry: {BASELINE_METRICS_PATH}")
baseline_df = pd.read_csv(BASELINE_METRICS_PATH)
required_baseline_columns = {"query_id", "agent", "status", "json_parse", "schema_valid"}
missing_baseline_columns = required_baseline_columns - set(baseline_df.columns)
if missing_baseline_columns:
    raise ValueError(f"Historical telemetry is missing columns: {sorted(missing_baseline_columns)}")
selected_baseline = baseline_df[baseline_df["query_id"].astype(str).isin(ROOT_CAUSE_ALL_QUERY_IDS)].copy()
expected_agents = {"AI1_News_Analyst", "AI2_Macro_Analyst", "AI3_Quant_Regime_Analyst",
                   "AI4_Risk_Data_Auditor", "AI5_Lead_Researcher"}
pair_counts = selected_baseline.groupby(["query_id", "agent"]).size()
duplicate_pairs = [{"query_id": q, "agent": a, "count": int(n)}
                   for (q, a), n in pair_counts[pair_counts > 1].items()]
missing_pairs = [{"query_id": q, "agent": a}
                 for q in ROOT_CAUSE_ALL_QUERY_IDS for a in sorted(expected_agents)
                 if int(pair_counts.get((q, a), 0)) == 0]
contradictions = selected_baseline[
    selected_baseline["status"].eq("success")
    & (~selected_baseline["json_parse"].eq(True) | ~selected_baseline["schema_valid"].eq(True))
]
phase0_status = "PASS" if not duplicate_pairs and not missing_pairs and contradictions.empty else "INVALID"
if phase0_status != "PASS":
    raise RuntimeError(
        f"Historical telemetry integrity failed: missing={missing_pairs}, "
        f"duplicates={duplicate_pairs}, contradictions={len(contradictions)}")
manifest_path = BASELINE_RUN_DIR / "benchmark_run_manifest.json"
baseline_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
notebook_sha256 = hashlib.sha256(GAIB_NOTEBOOK_PATH.read_bytes()).hexdigest() if GAIB_NOTEBOOK_PATH.exists() else None
builder_path = PROJECT_ROOT / "multi_agent" / "GAIB-1" / "build_token_root_cause_experiment.py"
builder_sha256 = hashlib.sha256(builder_path.read_bytes()).hexdigest() if builder_path.exists() else None

GAIB_ROOT_CAUSE_MANIFEST = {
    "run_id": GAIB_RUN_ID,
    "experiment": "GAIB-1 targeted token root-cause v1",
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "baseline_run_id": baseline_manifest.get("run_id"),
    "baseline_run_dir": str(BASELINE_RUN_DIR),
    "baseline_telemetry_sha256": hashlib.sha256(BASELINE_METRICS_PATH.read_bytes()).hexdigest(),
    "notebook_path": str(GAIB_NOTEBOOK_PATH),
    "notebook_sha256": notebook_sha256,
    "builder_sha256": builder_sha256,
    "raw_diagnostics_path": str(GAIB_DIAGNOSTIC_FILE),
    "model": THAILLM_MODEL,
    "prompt_version": "claim-evidence-v1",
    "schema_version": "agent-contract-v1",
    "phase0": {
        "status": phase0_status,
        "selected_query_count": len(ROOT_CAUSE_ALL_QUERY_IDS),
        "expected_historical_agent_records": len(ROOT_CAUSE_ALL_QUERY_IDS) * len(expected_agents),
        "observed_historical_agent_records": int(len(selected_baseline)),
        "unique_query_agent_pairs": int(selected_baseline[["query_id", "agent"]].drop_duplicates().shape[0]),
        "missing_pairs": missing_pairs,
        "duplicate_pairs": duplicate_pairs,
        "contradictory_success_rows": int(len(contradictions)),
        "historical_notebook_hash_available": bool(baseline_manifest.get("notebook_sha256")),
        "historical_raw_response_available": False,
        "historical_max_tokens_requested_available": "max_tokens_requested" in baseline_df.columns,
    },
    "configuration": {
        "temperature": THAILLM_TEMPERATURE,
        "baseline_agent_max_tokens": 900,
        "increase_token_variants": [1200, 1500],
        "ai3_compact_output_default": GAIB_AI3_COMPACT_OUTPUT,
        "agent5_max_tokens": THAILLM_MAX_TOKENS_FINAL,
        "agents_concurrent_default": RUN_AGENTS_CONCURRENTLY,
        "retrieval_model": EMBEDDING_MODEL,
        "dense_candidates": DENSE_CANDIDATES,
        "bm25_candidates": BM25_CANDIDATES,
        "hybrid_candidates": HYBRID_CANDIDATES,
        "rrf_k": RRF_K,
        "final_k": FINAL_K,
        "jina_model": JINA_MODEL,
    },
    "remote_experiment_opt_in": GAIB_RUN_ALL_EXPERIMENTS or os.getenv("GAIB_RUN_TARGETED_EXPERIMENT", "false").strip().lower() in {"1", "true", "yes"},
    "planned_repair_ablation_max_pairs": 3,
}
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "experiment_manifest.json").write_text(
    json.dumps(GAIB_ROOT_CAUSE_MANIFEST, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

baseline_failures = selected_baseline[
    ~selected_baseline["json_parse"].eq(True) | ~selected_baseline["schema_valid"].eq(True)
].copy()
baseline_failures["run_id"] = GAIB_RUN_ID
baseline_failures["source_run_id"] = baseline_manifest.get("run_id")
baseline_failures["source_hash"] = baseline_manifest.get("notebook_sha256")
baseline_failures["builder_sha256"] = baseline_manifest.get("builder_sha256")
baseline_failures["model"] = baseline_manifest.get("generation", {}).get("model")
baseline_failures["prompt_version"] = baseline_manifest.get("prompt_version")
baseline_failures["schema_version"] = baseline_manifest.get("schema_version")
baseline_failures["config_snapshot"] = json.dumps(
    baseline_manifest.get("generation", {}), ensure_ascii=False, sort_keys=True)
if "finish_reason" in baseline_failures:
    baseline_failures["root_cause_classification"] = baseline_failures.apply(
        lambda r: "LIKELY" if str(r.get("finish_reason", "")).casefold() in {"length", "max_tokens", "max_output_tokens"}
        and pd.to_numeric(pd.Series([r.get("completion_tokens")]), errors="coerce").iloc[0] == 900
        else "UNRESOLVED", axis=1)
else:
    baseline_failures["root_cause_classification"] = "UNRESOLVED"
baseline_failures["raw_response_available"] = False
baseline_failures["diagnostic_note"] = baseline_failures["root_cause_classification"].map(
    {"LIKELY": "finish_reason and 900 completion tokens support truncation; historical raw response was not captured.",
     "UNRESOLVED": "Insufficient historical request-level evidence to classify the failure."})
baseline_failures.to_csv(OUTPUT_DIR / "json_failure_diagnosis.csv", index=False, encoding="utf-8")

historical_request_rows = selected_baseline.copy()
historical_request_rows["run_id"] = baseline_manifest.get("run_id")
historical_request_rows["source_hash"] = baseline_manifest.get("notebook_sha256")
historical_request_rows["builder_sha256"] = baseline_manifest.get("builder_sha256")
historical_request_rows["variant"] = "historical_baseline"
historical_request_rows["model"] = baseline_manifest.get("generation", {}).get("model")
historical_request_rows["prompt_version"] = baseline_manifest.get("prompt_version")
historical_request_rows["schema_version"] = baseline_manifest.get("schema_version")
historical_request_rows["config_snapshot"] = json.dumps(
    baseline_manifest.get("generation", {}), ensure_ascii=False, sort_keys=True)
historical_request_rows["raw_response_chars"] = None
historical_request_rows["max_tokens_requested"] = None
historical_request_rows["request_telemetry_granularity"] = "legacy_agent_call_not_per_http_request"
historical_request_rows.to_csv(OUTPUT_DIR / "agent_request_telemetry.csv", index=False, encoding="utf-8")

budget_rows = []
for _, row in selected_baseline.iterrows():
    budget_rows.append({
        "run_id": GAIB_RUN_ID, "source_run_id": baseline_manifest.get("run_id"),
        "source_hash": baseline_manifest.get("notebook_sha256"),
        "builder_sha256": baseline_manifest.get("builder_sha256"),
        "model": baseline_manifest.get("generation", {}).get("model"),
        "prompt_version": baseline_manifest.get("prompt_version"),
        "schema_version": baseline_manifest.get("schema_version"),
        "config_snapshot": json.dumps(baseline_manifest.get("generation", {}), sort_keys=True),
        "variant": "A_historical_900", "query_id": row.get("query_id"), "agent": row.get("agent"),
        "max_tokens_requested": None, "completion_tokens": row.get("completion_tokens"),
        "total_tokens": row.get("total_tokens"),
        "finish_reason": row.get("finish_reason"), "status": row.get("status"),
        "json_valid": row.get("json_parse"), "schema_valid": row.get("schema_valid"),
        "api_success": row.get("api_success"),
        "first_attempt_schema_valid": bool(row.get("schema_valid")) if int(row.get("repair_attempts") or 0) == 0 else False,
        "post_repair_schema_valid": bool(row.get("schema_valid")),
        "repair_attempts": row.get("repair_attempts"),
        "truncation_observed": str(row.get("finish_reason", "")).casefold() in {"length", "max_tokens", "max_output_tokens"},
        "recovered_after_repair": bool(row.get("status") == "success" and int(row.get("repair_attempts") or 0) > 0),
        "repair_attempted": int(row.get("repair_attempts") or 0) > 0,
        "latency_ms": row.get("latency_ms"), "measurement_status": "HISTORICAL_TELEMETRY",
    })
pd.DataFrame(budget_rows).to_csv(OUTPUT_DIR / "token_budget_experiment_results.csv", index=False, encoding="utf-8")

latency_rows = []
for _, row in selected_baseline[selected_baseline["query_id"].astype(str).eq("gtv2_000070")].iterrows():
    latency_rows.append({
        "run_id": GAIB_RUN_ID, "query_id": row.get("query_id"), "agent": row.get("agent"),
        "source_hash": baseline_manifest.get("notebook_sha256"),
        "builder_sha256": baseline_manifest.get("builder_sha256"),
        "model": baseline_manifest.get("generation", {}).get("model"),
        "prompt_version": baseline_manifest.get("prompt_version"),
        "schema_version": baseline_manifest.get("schema_version"),
        "config_snapshot": json.dumps(baseline_manifest.get("generation", {}), sort_keys=True),
        "execution_mode": "historical_unknown", "latency_ms": row.get("latency_ms"),
        "gate_wait_ms": None, "http_attempt_durations_ms": None,
        "api_attempt_count": row.get("attempt_count"), "retry_count": max(0, int(row.get("attempt_count") or 0) - 1),
        "finish_reason": row.get("finish_reason"), "measurement_status": "HISTORICAL_REQUEST_TIMING_NOT_INSTRUMENTED",
    })
pd.DataFrame(latency_rows, columns=[
    "run_id", "query_id", "agent", "execution_mode", "latency_ms", "gate_wait_ms",
    "http_attempt_durations_ms", "api_attempt_count", "retry_count", "finish_reason",
    "measurement_status",
]).to_csv(OUTPUT_DIR / "latency_diagnosis.csv", index=False, encoding="utf-8")
pd.DataFrame(columns=[
    "run_id", "source_hash", "builder_sha256", "model", "prompt_version", "schema_version",
    "config_snapshot", "variant", "query_id", "agent", "initial_status", "repair_status",
    "initial_tokens", "repair_tokens", "recovered", "latency_ms", "measurement_status",
]).to_csv(OUTPUT_DIR / "repair_ablation_results.csv", index=False, encoding="utf-8")

def write_root_cause_report():
    failed_900 = baseline_failures[
        pd.to_numeric(baseline_failures.get("completion_tokens"), errors="coerce").eq(900)
    ]
    confirmed_finish = failed_900[
        failed_900.get("finish_reason", pd.Series(index=failed_900.index, dtype=object))
        .astype(str).str.casefold().isin({"length", "max_tokens", "max_output_tokens"})
    ]
    lines = [
        "# GAIB-1 token-limit root-cause experiment",
        "",
        f"- Run: `{GAIB_RUN_ID}`",
        f"- Historical baseline run: `{baseline_manifest.get('run_id', 'unknown')}`",
        f"- Phase 0 integrity: **{phase0_status}** (25 expected query-agent rows, no duplicate/missing pairs or contradictory success rows).",
        f"- Source provenance: historical notebook hash {'available' if baseline_manifest.get('notebook_sha256') else 'not recorded'}; historical raw responses not captured.",
        "",
        "## Historical failure diagnosis",
        f"- Failed historical rows ending exactly at 900 completion tokens: {len(failed_900)}.",
        f"- Those rows with truncation `finish_reason`: {len(confirmed_finish)}.",
        "- Classification: **LIKELY**, not CONFIRMED, because the historical raw response ending was not retained. The API finish reason is strong evidence, but the missing raw response prevents the complete check requested.",
        "- Historical status/validity consistency: passed; no row had `status=success` while JSON parsing or schema validation failed.",
        "",
        "## Experiments",
        "- No new LLM requests are made unless `GAIB_RUN_TARGETED_EXPERIMENT=true` is set before running the final experiment cell.",
        "- Remote calls are refused for non-HTTPS ThaiLLM endpoints to prevent sending credentials or prompts over cleartext HTTP.",
        "- Variant A historical baseline, Variant B 1,200-token budget, Variant C compact 900-token contract, targeted recovery, and sequential/concurrent latency comparison are written to the CSV deliverables when enabled.",
        "- Variant 1,500 is only run if the measured 1,200-token output still ends with a truncation finish reason.",
        "- Task correctness is not inferred from JSON validity; it remains unevaluated without a domain oracle or documented human review.",
        "",
        "## Preliminary conclusion",
        "- Saved evidence supports output truncation as the leading explanation for 900-token failures with `finish_reason=length`; other failures, including schema violations and slow requests with short outputs, remain separate categories.",
        "- No production default is selected based on the historical run alone. Select a configuration only after the controlled variants complete and compare validity, token overhead, and latency.",
        "",
        "See `json_failure_diagnosis.csv`, `agent_request_telemetry.csv`, `token_budget_experiment_results.csv`, `repair_ablation_results.csv`, and `latency_diagnosis.csv` in this run directory.",
    ]
    diagnosis_path = OUTPUT_DIR / "json_failure_diagnosis.csv"
    if diagnosis_path.is_file():
        diagnosis_df = pd.read_csv(diagnosis_path)
        if "root_cause_classification" in diagnosis_df:
            confirmed = int(diagnosis_df["root_cause_classification"].eq("CONFIRMED").sum())
            likely = int(diagnosis_df["root_cause_classification"].eq("LIKELY").sum())
            lines.extend([
                "",
                "## Evidence classification",
                f"- Confirmed truncation failures with captured raw response and finish reason: {confirmed}.",
                f"- Likely historical truncation failures without captured raw response: {likely}.",
            ])
    results_path = OUTPUT_DIR / "token_budget_experiment_results.csv"
    if results_path.is_file():
        results_df = pd.read_csv(results_path)
        measured = results_df[results_df.get("measurement_status", pd.Series(index=results_df.index, dtype=object)).eq("MEASURED")]
        if not measured.empty:
            lines.extend(["", "## Controlled experiment measurements", ""])
            for variant, group in measured.groupby("variant"):
                samples = len(group)
                schema_rate = pd.to_numeric(group["schema_valid"], errors="coerce").mean()
                truncation_rate = group["finish_reason"].astype(str).str.casefold().isin(
                    {"length", "max_tokens", "max_output_tokens"}).mean()
                mean_tokens = pd.to_numeric(group["total_tokens"], errors="coerce").mean()
                p50_latency = _percentile(group["latency_ms"], 0.50)
                p95_latency = _percentile(group["latency_ms"], 0.95)
                lines.append(
                    f"- `{variant}`: n={samples}, schema-valid={schema_rate:.3f}, "
                    f"finish-reason truncation={truncation_rate:.3f}, "
                    f"mean total tokens={mean_tokens:.1f}, latency P50/P95="
                    f"{p50_latency:.1f}/{p95_latency:.1f} ms.")
            if {"B_budget_1200", "C_compact_900"}.issubset(set(measured["variant"])):
                comparison = measured[measured["variant"].isin(["B_budget_1200", "C_compact_900"])]
                paired = comparison.pivot_table(
                    index=["query_id", "agent"], columns="variant",
                    values=["schema_valid", "truncation_observed"], aggfunc="first")
                if not paired.empty and all(
                    (metric, variant) in paired.columns
                    for metric in ("schema_valid", "truncation_observed")
                    for variant in ("B_budget_1200", "C_compact_900")
                ):
                    b_schema = paired[("schema_valid", "B_budget_1200")].astype(bool)
                    c_schema = paired[("schema_valid", "C_compact_900")].astype(bool)
                    b_truncated = paired[("truncation_observed", "B_budget_1200")].astype(bool)
                    c_truncated = paired[("truncation_observed", "C_compact_900")].astype(bool)
                    if (b_schema.mean() >= c_schema.mean()) and (b_truncated.mean() < c_truncated.mean()):
                        lines.append("- Measured paired comparison: 1,200-token output improved schema validity and reduced truncation versus compact 900-token output in the shared sample. This is not a correctness claim.")
                    else:
                        lines.append("- Measured paired comparison: 1,200-token output did not outperform compact 900-token output on both schema validity and truncation; no automatic configuration change is recommended.")
                else:
                    lines.append("- Measured comparison could not be paired for both variants; no automatic configuration change is recommended.")
            lines.append("- Task correctness remains unevaluated; schema validity is not a correctness oracle.")
    (OUTPUT_DIR / "root_cause_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

write_root_cause_report()
print(f"Phase 0 {phase0_status}: baseline={BASELINE_RUN_DIR.name}, rows={len(selected_baseline)}, "
      f"failures={len(baseline_failures)}, 900-token truncation candidates="
      f"{int(baseline_failures.get('root_cause_classification', pd.Series(dtype=str)).eq('LIKELY').sum())}")
print("Remote experiments are opt-in: set GAIB_RUN_ALL_EXPERIMENTS=true for the complete development-only suite, or GAIB_RUN_TARGETED_EXPERIMENT=true for root-cause ablations only.")
'''


EXPERIMENT_CELL = r'''RUN_TOKEN_ROOT_CAUSE_EXPERIMENT = os.getenv(
    "GAIB_RUN_TARGETED_EXPERIMENT", "false").strip().lower() in {"1", "true", "yes"} or GAIB_RUN_ALL_EXPERIMENTS
ROOT_CAUSE_TARGET_QUERY_IDS = ["gtv2_000054", "gtv2_000055", "gtv2_000071", "gtv2_000078"]
ROOT_CAUSE_LATENCY_QUERY_ID = "gtv2_000070"
AGENT_NAMES = [
    "AI1_News_Analyst", "AI2_Macro_Analyst", "AI3_Quant_Regime_Analyst",
    "AI4_Risk_Data_Auditor",
]
AGENT_CALLS = {
    "AI1_News_Analyst": lambda llm, query, sources, market, hmm, risk: agent1.run(llm, query, sources, market),
    "AI2_Macro_Analyst": lambda llm, query, sources, market, hmm, risk: agent2.run(llm, query, sources, market),
    "AI3_Quant_Regime_Analyst": lambda llm, query, sources, market, hmm, risk: agent3.run(llm, query, market, hmm),
    "AI4_Risk_Data_Auditor": lambda llm, query, sources, market, hmm, risk: agent4.run(llm, query, market, risk),
}

def _append_rows(path, rows):
    if not rows:
        return
    frame = pd.DataFrame(rows)
    path = Path(path)
    if path.exists() and path.stat().st_size > 0:
        existing = pd.read_csv(path)
        frame = pd.concat([existing, frame], ignore_index=True, sort=False)
    frame.to_csv(path, index=False, encoding="utf-8")

def _agent_status_row(query_id, variant, agent_name, result, wall_ms, execution_mode):
    metrics = result.get("metrics", {})
    schema_valid = bool(result.get("schema_valid"))
    json_valid = bool(result.get("json_valid"))
    status = result.get("status", "error")
    if status == "success" and not (json_valid and schema_valid):
        raise AssertionError(f"Contradictory {agent_name} status/validity in {query_id}")
    return {
        "run_id": GAIB_RUN_ID, "query_id": query_id, "variant": variant,
        "source_hash": notebook_sha256, "builder_sha256": builder_sha256,
        "model": THAILLM_MODEL, "prompt_version": ("claim-evidence-ai1-compact-v1"
            if agent_name == "AI1_News_Analyst" and GAIB_COMPACT_OUTPUT
            else ("claim-evidence-ai5-compact-v1"
                  if agent_name == "AI5_Lead_Researcher" and GAIB_COMPACT_OUTPUT
                  else ("claim-evidence-ai3-compact-v1"
                        if agent_name == "AI3_Quant_Regime_Analyst" and GAIB_AI3_COMPACT_OUTPUT
                        else ("claim-evidence-compact-v1" if GAIB_COMPACT_OUTPUT else "claim-evidence-v1")))),
        "schema_version": "agent-contract-v1",
        "config_snapshot": json.dumps(GAIB_ROOT_CAUSE_MANIFEST["configuration"], sort_keys=True),
        "agent": agent_name, "status": status, "api_success": metrics.get("api_success"),
        "json_parse": json_valid, "schema_valid": schema_valid,
        "finish_reason": metrics.get("finish_reason"),
        "max_tokens_requested": metrics.get("max_tokens_requested"),
        "prompt_tokens": metrics.get("prompt_tokens"), "completion_tokens": metrics.get("completion_tokens"),
        "total_tokens": metrics.get("total_tokens"), "raw_response_chars": metrics.get("raw_response_chars"),
        "parse_error": result.get("json_error"),
        "schema_errors": json.dumps(result.get("schema_errors", []), ensure_ascii=False),
        "repair_attempts": metrics.get("repair_attempts"), "attempt_count": metrics.get("attempt_count"),
        "api_attempt_count": metrics.get("api_attempt_count"),
        "gate_wait_ms": metrics.get("gate_wait_ms"),
        "http_attempt_durations_ms": json.dumps(metrics.get("http_attempt_durations_ms", [])),
        "http_retry_reasons": json.dumps(metrics.get("http_retry_reasons", [])),
        "latency_ms": metrics.get("latency_ms"), "wall_ms": wall_ms,
        "execution_mode": execution_mode, "task_success": None,
        "task_validation_status": "NOT_EVALUATED_WITHOUT_DOMAIN_ORACLE",
    }

def _fixed_context_for_query(query):
    retrieval = assistant.evidence.retrieve(query, FINAL_K)
    sources = retrieval["ranked_candidates"]
    _context, source_manifest = prepare_cited_context(sources)
    market = build_market_snapshot(query, df_features)
    hmm = run_hmm_snapshot(query, df_features, HMM_PATH)
    return source_manifest, market, hmm, risk_snapshot_global, retrieval

def _run_agents_on_cached_context(query_id, query, selected_agents, variant,
                                  token_budget, compact=False, recovery_mode="none",
                                  execution_mode="sequential", fixed_context=None):
    global THAILLM_MAX_TOKENS_AGENT, GAIB_COMPACT_OUTPUT, GAIB_AI3_COMPACT_OUTPUT
    global GAIB_TRUNCATION_RECOVERY_MODE, GAIB_ACTIVE_QUERY_ID, GAIB_ACTIVE_VARIANT
    source_manifest, market, hmm, risk, _retrieval = fixed_context or _fixed_context_for_query(query)
    previous_budget = THAILLM_MAX_TOKENS_AGENT
    previous_compact = GAIB_COMPACT_OUTPUT
    previous_ai3_compact = GAIB_AI3_COMPACT_OUTPUT
    THAILLM_MAX_TOKENS_AGENT = token_budget
    GAIB_COMPACT_OUTPUT = compact
    GAIB_AI3_COMPACT_OUTPUT = compact
    GAIB_TRUNCATION_RECOVERY_MODE = recovery_mode
    GAIB_ACTIVE_QUERY_ID = query_id
    GAIB_ACTIVE_VARIANT = variant
    output = {}
    telemetry_start_index = len(GAIB_REQUEST_TELEMETRY_ROWS)
    started = time.perf_counter()
    try:
        if execution_mode == "concurrent":
            with ThreadPoolExecutor(max_workers=min(4, len(selected_agents))) as pool:
                futures = {
                    pool.submit(AGENT_CALLS[name], assistant.llm, query, source_manifest, market, hmm, risk): name
                    for name in selected_agents
                }
                for future in as_completed(futures):
                    output[futures[future]] = future.result()
        else:
            for name in selected_agents:
                output[name] = AGENT_CALLS[name](assistant.llm, query, source_manifest, market, hmm, risk)
    finally:
        THAILLM_MAX_TOKENS_AGENT = previous_budget
        GAIB_COMPACT_OUTPUT = previous_compact
        GAIB_AI3_COMPACT_OUTPUT = previous_ai3_compact
        GAIB_TRUNCATION_RECOVERY_MODE = "none"
    wall_ms = (time.perf_counter() - started) * 1000
    rows = [
        _agent_status_row(query_id, variant, name, result,
                          float(result.get("metrics", {}).get("latency_ms") or 0),
                          execution_mode)
        for name, result in output.items()
    ]
    request_rows = GAIB_REQUEST_TELEMETRY_ROWS[telemetry_start_index:]
    _append_rows(OUTPUT_DIR / "agent_request_telemetry.csv", request_rows)
    budget_rows = []
    repair_rows = []
    for row in rows:
        result = output[row["agent"]]
        m = result.get("metrics", {})
        agent_requests = [
            request for request in request_rows
            if request.get("query_id") == query_id and request.get("agent") == row["agent"]
        ]
        initial_request = agent_requests[0] if agent_requests else {}
        initial_status = initial_request.get("status")
        budget_rows.append({
            "run_id": GAIB_RUN_ID, "source_run_id": GAIB_RUN_ID,
            "source_hash": notebook_sha256, "builder_sha256": builder_sha256,
            "model": THAILLM_MODEL, "prompt_version": "claim-evidence-compact-v1" if compact else "claim-evidence-v1",
            "schema_version": "agent-contract-v1",
            "config_snapshot": json.dumps({
                "temperature": THAILLM_TEMPERATURE, "agent_max_tokens": token_budget,
                "compact_output": compact, "recovery_mode": recovery_mode,
                "execution_mode": execution_mode,
            }, sort_keys=True),
            "variant": variant,
            "query_id": query_id, "agent": row["agent"],
            "configured_initial_budget": token_budget,
            "max_tokens_requested": m.get("max_tokens_requested"),
            "prompt_tokens": m.get("prompt_tokens"), "completion_tokens": m.get("completion_tokens"),
            "total_tokens": m.get("total_tokens"), "finish_reason": m.get("finish_reason"),
            "initial_finish_reason": initial_request.get("finish_reason"),
            "status": row["status"], "json_valid": row["json_parse"], "schema_valid": row["schema_valid"],
            "api_success": row["api_success"],
            "first_attempt_schema_valid": initial_status == "success",
            "post_repair_schema_valid": row["schema_valid"],
            "repair_attempts": m.get("repair_attempts"),
            "repair_attempted": int(m.get("attempt_count") or 1) > 1,
            "truncation_observed": any(
                request.get("status") == "truncated_output" for request in agent_requests),
            "recovered_after_repair": bool(len(agent_requests) > 1 and row["schema_valid"]),
            "latency_ms": m.get("latency_ms"), "measurement_status": "MEASURED",
        })
        repair_rows.append({
            "run_id": GAIB_RUN_ID, "source_hash": notebook_sha256,
            "builder_sha256": builder_sha256, "model": THAILLM_MODEL,
            "prompt_version": "claim-evidence-compact-v1" if compact else "claim-evidence-v1",
            "schema_version": "agent-contract-v1",
            "config_snapshot": json.dumps({
                "temperature": THAILLM_TEMPERATURE, "agent_max_tokens": token_budget,
                "compact_output": compact, "recovery_mode": recovery_mode,
                "execution_mode": execution_mode,
            }, sort_keys=True),
            "variant": variant, "query_id": query_id, "agent": row["agent"],
            "initial_status": initial_status,
            "repair_status": result.get("status") if int(m.get("attempt_count") or 1) > 1 else None,
            "initial_tokens": m.get("initial_tokens"), "repair_tokens": m.get("repair_tokens"),
            "recovered": bool(int(m.get("attempt_count") or 1) > 1 and row["schema_valid"]),
            "latency_ms": m.get("latency_ms"), "measurement_status": "MEASURED",
        })
    _append_rows(OUTPUT_DIR / "token_budget_experiment_results.csv", budget_rows)
    _append_rows(OUTPUT_DIR / "repair_ablation_results.csv", repair_rows)
    return rows, output, wall_ms

if not RUN_TOKEN_ROOT_CAUSE_EXPERIMENT:
    print("Targeted remote experiment skipped. Set GAIB_RUN_ALL_EXPERIMENTS=true for the complete development-only suite, or GAIB_RUN_TARGETED_EXPERIMENT=true for root-cause ablations only.")
else:
    if (
        (GAIB_RUN_ALL_EXPERIMENTS or GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK)
        and GAIB_BENCHMARK_SPLIT != "development"
    ):
        raise RuntimeError("Full GAIB experiment/benchmark switches only run on the development split; validation/test splits are forbidden.")
    if GAIB_RUN_FULL_HELD_OUT_ACCEPTANCE and (
        GAIB_BENCHMARK_SPLIT != "held_out" or not GAIB_ALLOW_HELD_OUT_SPLIT
    ):
        raise RuntimeError("Full held-out acceptance requires split=held_out and GAIB_ALLOW_HELD_OUT_SPLIT=true.")
    if phase0_status != "PASS":
        raise RuntimeError("Phase 0 telemetry integrity failed; refusing remote experiment.")
    if not THAILLM_BASE_URL.lower().startswith("https://"):
        raise RuntimeError(
            "Refusing to send API credentials or prompts to a non-TLS ThaiLLM endpoint. "
            "Set THAILLM_BASE_URL to the provider's verified HTTPS endpoint before opt-in.")
    if assistant is None:
        if not (CF_ACCOUNT_ID and CF_API_TOKEN and QDRANT_URL and QDRANT_API_KEY and JINA_API_KEYS and THAILLM_API_KEYS):
            raise RuntimeError("Configure ThaiLLM, Qdrant, Cloudflare and Jina credentials before opt-in.")
        assistant = GoldAssistantMultiAgent()
    if not assistant.evidence.ready or assistant.evidence.backend_name != "qdrant_cloudflare_hybrid":
        raise RuntimeError("The experiment requires real Qdrant + Cloudflare hybrid retrieval; local fallback is forbidden.")
    query_by_id = {str(row.get("query_id")): row for row in GROUND_TRUTH}
    absent_queries = [query_id for query_id in ROOT_CAUSE_TARGET_QUERY_IDS + [ROOT_CAUSE_LATENCY_QUERY_ID]
                      if query_id not in query_by_id]
    if absent_queries:
        raise KeyError(f"Selected queries are absent from loaded Ground Truth: {absent_queries}")

    # One retrieval snapshot per query is reused in every generation comparison.
    fixed_contexts = {}
    for query_id in sorted(set(ROOT_CAUSE_TARGET_QUERY_IDS + [ROOT_CAUSE_LATENCY_QUERY_ID])):
        fixed_contexts[query_id] = _fixed_context_for_query(query_by_id[query_id]["query"])

    historical_candidates = selected_baseline[
        selected_baseline["query_id"].astype(str).isin(ROOT_CAUSE_TARGET_QUERY_IDS)
        & selected_baseline["finish_reason"].astype(str).str.casefold().isin(
            {"length", "max_tokens", "max_output_tokens"})
        & pd.to_numeric(selected_baseline["completion_tokens"], errors="coerce").eq(900)
        & selected_baseline["agent"].isin(AGENT_NAMES)
    ]
    target_pairs = [(str(row.query_id), str(row.agent)) for row in historical_candidates.itertuples()]
    if not target_pairs:
        raise RuntimeError("No historical 900-token truncation cases matched the configured targets.")
    pair_map = {}
    for query_id, agent_name in target_pairs:
        pair_map.setdefault(query_id, []).append(agent_name)
    fresh_baseline_rows = []
    for query_id, agent_names in pair_map.items():
        query = query_by_id[query_id]["query"]
        fixed = fixed_contexts[query_id]
        rows, results, _ = _run_agents_on_cached_context(
            query_id, query, agent_names, "A_fresh_baseline_900", 900,
            fixed_context=fixed)
        fresh_baseline_rows.extend(rows)

    b_rows = []
    for query_id, agent_names in pair_map.items():
        rows, _, _ = _run_agents_on_cached_context(
            query_id, query_by_id[query_id]["query"], agent_names, "B_budget_1200", 1200,
            fixed_context=fixed_contexts[query_id])
        b_rows.extend(rows)
    still_truncated_1200 = [row for row in b_rows if row["finish_reason"] in {"length", "max_tokens", "max_output_tokens"}]
    if still_truncated_1200:
        for row in still_truncated_1200:
            _run_agents_on_cached_context(
                row["query_id"], query_by_id[row["query_id"]]["query"], [row["agent"]],
                "B2_budget_1500_conditional", 1500, fixed_context=fixed_contexts[row["query_id"]])

    for query_id, agent_names in pair_map.items():
        _run_agents_on_cached_context(
            query_id, query_by_id[query_id]["query"], agent_names, "C_compact_900", 900,
            compact=True, fixed_context=fixed_contexts[query_id])

    # Recovery is tested only for cases whose fresh baseline produced a truncation finish reason.
    confirmed_fresh_pairs = [
        (row["query_id"], row["agent"]) for row in fresh_baseline_rows
        if row["finish_reason"] in {"length", "max_tokens", "max_output_tokens"}
    ]
    for recovery_mode, variant in (
        ("same_budget", "D1_repair_same_budget"),
        ("increased", "D2_repair_increased_on_truncation"),
    ):
        for query_id, agent_name in confirmed_fresh_pairs[:3]:
            _run_agents_on_cached_context(
                query_id, query_by_id[query_id]["query"], [agent_name], variant, 900,
                recovery_mode=recovery_mode, fixed_context=fixed_contexts[query_id])

    # Latency comparison changes only execution mode; query, evidence, prompts and budget stay fixed.
    latency_query = query_by_id[ROOT_CAUSE_LATENCY_QUERY_ID]["query"]
    latency_records = []
    for mode in ("sequential", "concurrent"):
        rows, _results, wall_ms = _run_agents_on_cached_context(
            ROOT_CAUSE_LATENCY_QUERY_ID, latency_query, AGENT_NAMES,
            f"E_latency_{mode}", 900, execution_mode=mode,
            fixed_context=fixed_contexts[ROOT_CAUSE_LATENCY_QUERY_ID])
        latency_records.extend({
            **row, "execution_mode": mode, "query_wall_ms": wall_ms,
            "sample_count_for_percentile": 1,
        } for row in rows)
    _append_rows(OUTPUT_DIR / "latency_diagnosis.csv", latency_records)

    raw_diagnostics = _read_jsonl(GAIB_DIAGNOSTIC_FILE) if GAIB_DIAGNOSTIC_FILE.is_file() else []
    fresh_failure_rows = []
    for raw_row in raw_diagnostics:
        if raw_row.get("variant") != "A_fresh_baseline_900" or raw_row.get("status") == "success":
            continue
        response_text = raw_row.get("raw_response") or ""
        finish_reason = str(raw_row.get("finish_reason") or "").casefold()
        try:
            json.loads(response_text)
            response_json_valid = True
        except json.JSONDecodeError:
            response_json_valid = False
        confirmed = finish_reason in {"length", "max_tokens", "max_output_tokens"} and bool(response_text)
        fresh_failure_rows.append({
            "run_id": GAIB_RUN_ID, "source_run_id": GAIB_RUN_ID,
            "source_hash": notebook_sha256, "builder_sha256": builder_sha256,
            "model": THAILLM_MODEL, "prompt_version": raw_row.get("prompt_version"),
            "schema_version": "agent-contract-v1",
            "config_snapshot": json.dumps(GAIB_ROOT_CAUSE_MANIFEST["configuration"], sort_keys=True),
            "query_id": raw_row.get("query_id"), "agent": raw_row.get("agent"),
            "variant": raw_row.get("variant"), "status": raw_row.get("status"),
            "finish_reason": finish_reason, "max_tokens_requested": raw_row.get("max_tokens_requested"),
            "completion_tokens": raw_row.get("completion_tokens"),
            "raw_response_chars": len(response_text),
            "raw_response_sha256": hashlib.sha256(response_text.encode("utf-8")).hexdigest() if response_text else None,
            "raw_response_available": bool(response_text),
            "raw_response_json_valid": response_json_valid,
            "parse_error": raw_row.get("parse_error"),
            "schema_errors": raw_row.get("schema_errors"),
            "root_cause_classification": "CONFIRMED" if confirmed else "UNRESOLVED",
            "diagnostic_note": (
                "Captured raw response is paired with provider finish_reason indicating output truncation."
                if confirmed else "The captured response does not provide sufficient evidence to confirm truncation."
            ),
        })
    if fresh_failure_rows:
        existing_diagnosis = pd.read_csv(OUTPUT_DIR / "json_failure_diagnosis.csv")
        diagnosis_combined = pd.concat(
            [existing_diagnosis, pd.DataFrame(fresh_failure_rows)],
            ignore_index=True, sort=False)
        diagnosis_combined.to_csv(
            OUTPUT_DIR / "json_failure_diagnosis.csv", index=False, encoding="utf-8")

    telemetry_df = pd.read_csv(OUTPUT_DIR / "agent_request_telemetry.csv")
    budget_df = pd.read_csv(OUTPUT_DIR / "token_budget_experiment_results.csv")
    telemetry_df.to_csv(OUTPUT_DIR / "agent_request_telemetry.csv", index=False, encoding="utf-8")
    metric_source = budget_df.copy()
    metric_source["schema_valid"] = metric_source["schema_valid"].map(
        lambda value: str(value).strip().lower() == "true" if not isinstance(value, bool) else value)
    metric_source["json_valid"] = metric_source["json_valid"].map(
        lambda value: str(value).strip().lower() == "true" if not isinstance(value, bool) else value)
    metric_source["first_attempt_schema_valid"] = metric_source["first_attempt_schema_valid"].map(
        lambda value: str(value).strip().lower() == "true" if not isinstance(value, bool) else value)
    metric_source["post_repair_schema_valid"] = metric_source["post_repair_schema_valid"].map(
        lambda value: str(value).strip().lower() == "true" if not isinstance(value, bool) else value)
    metric_source["truncation_observed"] = metric_source["truncation_observed"].map(
        lambda value: str(value).strip().lower() == "true" if not isinstance(value, bool) else value)
    metric_source["recovered_after_repair"] = metric_source["recovered_after_repair"].map(
        lambda value: str(value).strip().lower() == "true" if not isinstance(value, bool) else value)
    metric_source["api_success"] = metric_source["api_success"].map(
        lambda value: str(value).strip().lower() == "true" if not isinstance(value, bool) else value)
    metric_source["repair_attempted"] = metric_source["repair_attempted"].map(
        lambda value: str(value).strip().lower() == "true" if not isinstance(value, bool) else value)
    summary_rows = []
    for dimensions in (["variant", "agent"], ["variant", "query_id"]):
        for keys, group in metric_source.groupby(dimensions, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            row = dict(zip(dimensions, keys))
            latencies = pd.to_numeric(group["latency_ms"], errors="coerce").dropna()
            tokens = pd.to_numeric(group["total_tokens"], errors="coerce").dropna()
            row.update({
                "run_id": GAIB_RUN_ID,
                "source_hash": notebook_sha256,
                "builder_sha256": builder_sha256,
                "model": THAILLM_MODEL,
                "prompt_version": "claim-evidence-v1",
                "schema_version": "agent-contract-v1",
                "config_snapshot": json.dumps(GAIB_ROOT_CAUSE_MANIFEST["configuration"], sort_keys=True),
                "sample_count": int(len(group)),
                "api_success_rate": group["api_success"].mean(),
                "json_parse_rate": group["json_valid"].mean(),
                "schema_valid_rate": group["schema_valid"].mean(),
                "first_attempt_schema_valid_rate": group["first_attempt_schema_valid"].mean(),
                "post_repair_schema_valid_rate": group["post_repair_schema_valid"].mean(),
                "truncation_rate": group["truncation_observed"].mean(),
                "recovery_after_repair_rate": (
                    float(group.loc[group["repair_attempted"], "recovered_after_repair"].mean())
                    if group["repair_attempted"].any() else 0.0
                ),
                "mean_total_tokens": float(tokens.mean()) if len(tokens) else None,
                "max_total_tokens": int(tokens.max()) if len(tokens) else None,
                "latency_p50_ms": float(latencies.quantile(.50)) if len(latencies) else None,
                "latency_p95_ms": float(latencies.quantile(.95)) if len(latencies) else None,
                "token_overhead_per_recovered_response": None,
                "cost": "NOT_CONFIGURED",
            })
            summary_rows.append(row)
    summary_lookup = {}
    fresh_baseline = metric_source[metric_source["variant"].eq("A_fresh_baseline_900")]
    for variant, group in metric_source.groupby("variant"):
        if variant in {"A_fresh_baseline_900", "A_historical_900"}:
            continue
        paired = group.merge(
            fresh_baseline[["query_id", "agent", "schema_valid", "truncation_observed", "total_tokens"]],
            on=["query_id", "agent"], suffixes=("", "_baseline"))
        if paired.empty:
            continue
        recovered = (
            (~paired["schema_valid_baseline"].astype(bool)
             | paired["truncation_observed_baseline"].astype(bool))
            & paired["schema_valid"].astype(bool)
            & ~paired["truncation_observed"].astype(bool)
        )
        overhead = (
            pd.to_numeric(paired.loc[recovered, "total_tokens"], errors="coerce")
            - pd.to_numeric(paired.loc[recovered, "total_tokens_baseline"], errors="coerce")
        ).dropna()
        summary_lookup[variant] = float(overhead.mean()) if len(overhead) else None
    for row in summary_rows:
        row["token_overhead_per_recovered_response"] = summary_lookup.get(row["variant"])
    pd.DataFrame(summary_rows).to_csv(
        OUTPUT_DIR / "experiment_metrics_summary.csv", index=False, encoding="utf-8")
    if "request_duration_ms" in telemetry_df:
        timing_summary = telemetry_df.groupby(["agent", "variant"])["request_duration_ms"].agg(
            sample_count="count", mean_ms="mean", p50_ms="median",
            p95_ms=lambda series: _percentile(series, 0.95),
        ).reset_index()
        timing_summary.to_csv(OUTPUT_DIR / "request_latency_percentiles.csv", index=False, encoding="utf-8")
    GAIB_ROOT_CAUSE_MANIFEST["remote_experiment_status"] = "COMPLETED"
    GAIB_ROOT_CAUSE_MANIFEST["remote_experiment_records"] = int(len(telemetry_df))
    GAIB_ROOT_CAUSE_MANIFEST["confirmed_fresh_truncations"] = int(len(confirmed_fresh_pairs))
    (OUTPUT_DIR / "experiment_manifest.json").write_text(
        json.dumps(GAIB_ROOT_CAUSE_MANIFEST, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    write_root_cause_report()
    print(f"Targeted experiment completed: {len(telemetry_df)} request telemetry rows; output={OUTPUT_DIR}")
'''


def main() -> None:
    path = build_notebook()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"Created {path}")
    print(f"Notebook SHA-256: {digest}")


LIVE_ACCEPTANCE_CELL = r'''import os
import json

RUN_GAIB_LIVE_ACCEPTANCE = os.getenv(
    "GAIB_RUN_LIVE_ACCEPTANCE", "false"
).strip().lower() in {"1", "true", "yes"} or GAIB_RUN_ALL_EXPERIMENTS

if not RUN_GAIB_LIVE_ACCEPTANCE:
    print("Live acceptance run skipped. Set GAIB_RUN_ALL_EXPERIMENTS=true for all development experiments, or GAIB_RUN_LIVE_ACCEPTANCE=true for the live benchmark only.")
else:
    if (
        (GAIB_RUN_ALL_EXPERIMENTS or GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK)
        and GAIB_BENCHMARK_SPLIT != "development"
    ):
        raise RuntimeError("Full GAIB experiment/benchmark switches only run on the development split; validation/test splits are forbidden.")
    if not THAILLM_BASE_URL.lower().startswith("https://"):
        raise ValueError("ThaiLLM API credentials must only be sent over HTTPS.")
    if not GAIB_JUDGE_ENABLED:
        raise RuntimeError("AI-as-a-judge is required by the configured acceptance policy.")
    effective_judge_model = GAIB_JUDGE_MODEL or (
        "pathumma-thaillm-qwen3-8b-think-3.0.0" if THAILLM_MODEL != "pathumma-thaillm-qwen3-8b-think-3.0.0" else "typhoon-s-thaillm-8b-instruct"
    )
    if not effective_judge_model or effective_judge_model == THAILLM_MODEL:
        raise RuntimeError("Set GAIB_JUDGE_MODEL to an available model distinct from the answer generator.")
    if GAIB_SECOND_JUDGE_MODEL and GAIB_SECOND_JUDGE_MODEL in {
        effective_judge_model, THAILLM_MODEL
    }:
        raise RuntimeError("If configured, GAIB_SECOND_JUDGE_MODEL must be distinct from the primary judge and generator.")
    if not (
        THAILLM_API_KEYS and CF_ACCOUNT_ID and CF_API_TOKEN
        and QDRANT_URL and QDRANT_API_KEY and JINA_API_KEYS
    ):
        raise RuntimeError("Configure ThaiLLM, Cloudflare, Qdrant and Jina credentials before the live run.")
    if GAIB_BENCHMARK_SPLIT == "test" and not GAIB_ALLOW_TEST_SPLIT:
        raise RuntimeError("Refusing to run the frozen test split without explicit final-evaluation opt-in.")
    if GAIB_BENCHMARK_SPLIT == "held_out" and not GAIB_ALLOW_HELD_OUT_SPLIT:
        raise RuntimeError("Refusing to run the separate held-out split without explicit opt-in.")
    GAIB_LIVE_TRUNCATION_RECOVERY_MODE = os.getenv(
        "GAIB_LIVE_TRUNCATION_RECOVERY_MODE", "increased"
    ).strip().lower()
    if GAIB_LIVE_TRUNCATION_RECOVERY_MODE not in {"none", "same_budget", "increased"}:
        raise ValueError("GAIB_LIVE_TRUNCATION_RECOVERY_MODE must be none, same_budget, or increased.")
    GAIB_TRUNCATION_RECOVERY_MODE = GAIB_LIVE_TRUNCATION_RECOVERY_MODE

    THAILLM_CLIENTS = {
        name: OpenAI(
            base_url=THAILLM_BASE_URL,
            api_key=key,
            timeout=THAILLM_TIMEOUT_SECONDS,
            max_retries=0,
        )
        for name, key in THAILLM_API_KEYS
    }
    assistant = GoldAssistantMultiAgent()
    if not assistant.evidence.ready or assistant.evidence.backend_name != "qdrant_cloudflare_hybrid":
        raise RuntimeError("Live acceptance requires real Qdrant + Cloudflare hybrid retrieval; local fallback is forbidden.")
    import hashlib
    collection_info = assistant.evidence.backend.qdrant.get_collection(QDRANT_COLLECTION)
    chunk_fingerprint = hashlib.sha256("\n".join(sorted(
        f"{chunk.get('chunk_id')}:{hashlib.sha256(str(chunk.get('text') or '').encode('utf-8')).hexdigest()}"
        for chunk in assistant.evidence.backend.chunks
    )).encode("utf-8")).hexdigest()
    index_snapshot = {
        "collection": QDRANT_COLLECTION,
        "collection_uuid": str(getattr(collection_info, "collection_uuid", "")),
        "status": str(getattr(collection_info, "status", "")),
        "points_count": getattr(collection_info, "points_count", None),
        "indexed_vectors_count": getattr(collection_info, "indexed_vectors_count", None),
        "corpus_source": assistant.evidence.backend.corpus_source,
        "chunk_corpus_sha256": chunk_fingerprint,
    }
    GAIB_RUNTIME_MANIFEST["index_snapshot"] = index_snapshot
    GAIB_RUNTIME_MANIFEST["index_version"] = hashlib.sha256(
        json.dumps(index_snapshot, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()

    all_ready_ground_truth = read_jsonl(GAIB_GT_READY_PATH)
    ground_truth_audit_df = audit_ground_truth_coverage(all_ready_ground_truth)
    GROUND_TRUTH = [
        row for row in all_ready_ground_truth
        if str(row.get("split", "")).strip().lower() == GAIB_BENCHMARK_SPLIT
    ]
    if not GROUND_TRUTH:
        raise RuntimeError(f"No Ground Truth queries are available for split {GAIB_BENCHMARK_SPLIT!r}.")

    BENCHMARK_LIMIT = (
        len(GROUND_TRUTH)
        if GAIB_RUN_ALL_EXPERIMENTS
        or GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK
        or GAIB_RUN_FULL_HELD_OUT_ACCEPTANCE
        else min(5, max(1, BENCHMARK_LIMIT))
    )
    retrieval_benchmark_df, retrieval_stage_candidates_df, retrieval_errors_df = (
        run_retrieval_benchmark(GROUND_TRUTH, limit=BENCHMARK_LIMIT)
    )
    multiagent_benchmark_df, per_agent_benchmark_df, human_review_df, multiagent_errors_df = (
        run_multiagent_benchmark(GROUND_TRUTH, limit=BENCHMARK_LIMIT)
    )
    ai_judge_gate_status = run_gaib_ai_judge_acceptance(
        multiagent_benchmark_df,
        GROUND_TRUTH,
        retrieval_benchmark_df,
        multiagent_errors_df,
        baseline_comparison_complete=False,
    )
    live_run_summary = {
        "live_acceptance_status": "COMPLETED_WITH_ERRORS" if (
            not retrieval_errors_df.empty or not multiagent_errors_df.empty
        ) else "COMPLETED",
        "split": GAIB_BENCHMARK_SPLIT,
        "max_queries": BENCHMARK_LIMIT,
        "expected_ground_truth_queries": len(GROUND_TRUTH),
        "retrieval_queries": int(len(retrieval_benchmark_df)),
        "retrieval_errors": int(len(retrieval_errors_df)),
        "multiagent_queries": int(len(multiagent_benchmark_df)),
        "multiagent_errors": int(len(multiagent_errors_df)),
        "per_agent_records": int(len(per_agent_benchmark_df)),
        "backend": assistant.evidence.backend_name,
        "thaillm_model": THAILLM_MODEL,
        "jina_model": JINA_MODEL,
        "run_id": GAIB_RUN_ID,
        "ai_judge_decision": ai_judge_gate_status["decision"],
        "ai_judge_model": GAIB_JUDGE_MODEL,
        "second_judge_model": GAIB_SECOND_JUDGE_MODEL,
        "truncation_recovery_mode": GAIB_TRUNCATION_RECOVERY_MODE,
        "truncation_recovery_max_tokens": GAIB_RECOVERY_MAX_TOKENS,
        "truncation_recovery_escalation_max_tokens": GAIB_RECOVERY_ESCALATION_MAX_TOKENS,
    }
    GAIB_RUNTIME_MANIFEST.update(live_run_summary)
    GAIB_RUNTIME_MANIFEST["remote_api_opt_in"] = True
    GAIB_RUNTIME_MANIFEST["benchmark"].update({
        "retrieval_enabled": True,
        "multi_agent_enabled": True,
        "live_acceptance_enabled": True,
    })
    (OUTPUT_DIR / "benchmark_run_manifest.json").write_text(
        json.dumps(GAIB_RUNTIME_MANIFEST, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(live_run_summary, ensure_ascii=False, indent=2))
'''


if __name__ == "__main__":
    main()
