import json
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage

import api.server_app as server_app
from app.services import trace_span


class FakeStateSnapshot:
    def __init__(self, values, next_node=()):
        self.values = values
        self.next = next_node


class FakeGraph:
    def __init__(self):
        self._states = {}

    async def ainvoke(self, initial_state, config):
        thread_id = config["configurable"]["thread_id"]
        final_state = {
            **initial_state,
            "plan": json.dumps({"goal": initial_state["input"], "tasks": [{"title": "Read overview"}]}, ensure_ascii=False),
            "search_queries": ["python asyncio event loop"],
            "search_results": "SKIPPED: RAG_OK",
            "rag_results": "[RAG Answer]\nAsyncio overview",
            "critique": "Looks good",
            "final_answer": "Asyncio is Python's async runtime.",
            "revision_needed": False,
            "revision_count": 0,
            "step_count": 3,
        }
        self._states[thread_id] = FakeStateSnapshot(final_state, ())
        return final_state

    async def astream(self, initial_state, config):
        thread_id = config["configurable"]["thread_id"]

        planner_state = {
            **initial_state,
            "plan": json.dumps({"goal": initial_state["input"], "tasks": [{"title": "Read overview"}]}, ensure_ascii=False),
            "current_task": "Read overview",
            "search_queries": ["python asyncio event loop"],
            "step_count": 1,
            "messages": [HumanMessage(content="Planner created a plan")],
        }
        with trace_span("planner_node", {"thread_id": thread_id}):
            pass
        yield {"planner": planner_state}

        researcher_state = {
            **planner_state,
            "search_results": "SKIPPED: RAG_OK",
            "rag_results": "[RAG Answer]\nAsyncio overview",
            "final_answer": "Asyncio is Python's async runtime.",
            "step_count": 2,
            "messages": [HumanMessage(content="Researcher synthesized the answer")],
        }
        with trace_span("researcher_node", {"thread_id": thread_id}):
            with trace_span("query_rag", {"thread_id": thread_id}):
                pass
        yield {"researcher": researcher_state}

        critic_state = {
            **researcher_state,
            "critique": "Looks good",
            "revision_needed": False,
            "revision_count": 0,
            "step_count": 3,
            "messages": [HumanMessage(content="Critic approved the answer")],
        }
        with trace_span("critic_node", {"thread_id": thread_id}):
            pass
        yield {"critic": critic_state}

        self._states[thread_id] = FakeStateSnapshot(critic_state, ())

    async def aget_state(self, config):
        thread_id = config["configurable"]["thread_id"]
        return self._states[thread_id]


def run_smoke_test():
    user_id = f"dev-smoke-{uuid.uuid4().hex[:8]}"
    with patch("api.server_app.create_graph", return_value=FakeGraph()):
        with TestClient(server_app.app) as client:
            root = client.get("/")
            assert root.status_code == 200
            assert root.json()["links"]["developer_console"] == "/dev"
            assert root.json()["links"]["student_console"] == "/student"

            student = client.get("/student")
            assert student.status_code == 200
            assert "EduReflex 学生学习界面" in student.text
            assert "开始学习" in student.text

            dev = client.get("/dev")
            assert dev.status_code == 200
            assert "EduReflex 开发者控制台" in dev.text
            assert "开始执行" in dev.text

            workflow = client.get("/api/workflow")
            assert workflow.status_code == 200
            assert workflow.json()["entry_point"] == "planner"

            events = []
            with client.stream(
                "POST",
                "/api/query",
                json={"question": "Explain asyncio", "user_id": user_id, "stream": True},
            ) as response:
                assert response.status_code == 200
                for line in response.iter_lines():
                    if isinstance(line, bytes):
                        line = line.decode("utf-8")
                    if line.startswith("data: "):
                        events.append(json.loads(line[6:]))

            event_types = [event.get("event") for event in events]
            assert "session" in event_types
            assert event_types.count("node") == 3
            assert "result" in event_types
            assert "done" in event_types

            session_event = next(event for event in events if event.get("event") == "session")
            done_event = next(event for event in events if event.get("event") == "done")
            trace_id = session_event["trace_id"]
            thread_id = session_event["thread_id"]

            memory = client.get(f"/api/memory/{user_id}")
            assert memory.status_code == 200
            assert memory.json()["profile"]["interaction_count"] >= 1

            history = client.get(f"/api/history/{thread_id}")
            assert history.status_code == 200
            assert history.json()["state"]["final_answer"] == "Asyncio is Python's async runtime."

            trace = client.get(f"/api/traces/{trace_id}")
            assert trace.status_code == 200
            trace_payload = trace.json()
            assert trace_payload["summary"]["span_count"] >= 3
            assert any(span["name"] == "query_rag" for span in trace_payload["spans"])

            assert done_event["trace_id"] == trace_id
            assert done_event["thread_id"] == thread_id

    print("developer console smoke test: ok")


if __name__ == "__main__":
    run_smoke_test()
