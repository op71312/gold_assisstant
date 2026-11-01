import queue
import unittest
from types import SimpleNamespace

from web.python import gaib_runtime


class LeadResearcherEventTests(unittest.TestCase):
    def run_pipeline_with_lead(self, lead_run):
        events = queue.Queue()
        module = SimpleNamespace(
            agent5=SimpleNamespace(run=lead_run),
            _collect_evidence_ids=lambda _data: [],
        )

        class FakePipeline:
            evidence = SimpleNamespace(retrieve=lambda *_args, **_kwargs: [])

            def _run_specialists(self, *_args, **_kwargs):
                return {}

            def run(self, _question, progress_callback=None):
                return module.agent5.run()

        try:
            gaib_runtime._run_with_events(FakePipeline(), module, "question", events)
        except Exception as error:
            return list(events.queue), error
        return list(events.queue), None

    def test_lead_agent_emits_completion_events_after_result(self):
        events, error = self.run_pipeline_with_lead(lambda: {
            "status": "success",
            "schema_valid": True,
            "json_valid": True,
            "data": {"executive_summary": "มีหลักฐานรองรับ"},
            "metrics": {},
        })

        self.assertIsNone(error)
        lead_events = [event for event in events if event.get("agentId") == 5]
        self.assertEqual(
            [event["type"] for event in lead_events],
            ["agent_start", "tool_call", "tool_result", "agent_done"],
        )
        self.assertEqual(lead_events[-1]["status"], "done")

    def test_lead_agent_emits_error_completion_before_propagating_exception(self):
        def fail():
            raise RuntimeError("model failed")

        events, error = self.run_pipeline_with_lead(fail)

        self.assertIsInstance(error, RuntimeError)
        self.assertEqual(str(error), "model failed")
        lead_events = [event for event in events if event.get("agentId") == 5]
        self.assertEqual(lead_events[-1]["type"], "agent_done")
        self.assertEqual(lead_events[-1]["status"], "error")


if __name__ == "__main__":
    unittest.main()
