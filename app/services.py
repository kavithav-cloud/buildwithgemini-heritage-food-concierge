"""Custom ADK Service Registry configuration for Vertex AI Memory Bank."""

import json
from pathlib import Path
from google.adk.cli.service_registry import get_service_registry
from google.adk.memory import VertexAiMemoryBankService

PROJECT_ID = "qwiklabs-gcp-01-a4a0918623fd"
LOCATION = "us-central1"


def _get_memory_bank_id() -> str:
    metadata_path = Path("deployment_metadata.json")
    if not metadata_path.exists():
        metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
    if metadata_path.exists():
        try:
            data = json.loads(metadata_path.read_text())
            remote_id = data.get("remote_agent_runtime_id", "")
            if remote_id:
                return remote_id.split("/")[-1]
        except Exception:
            pass
    return "2610741431886675968"


def memory_service_factory(uri: str):
    memory_bank_id = _get_memory_bank_id()
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=memory_bank_id,
    )


# Register memory service builder for agentengine:// URIs
get_service_registry().register_memory_service("agentengine", memory_service_factory)
