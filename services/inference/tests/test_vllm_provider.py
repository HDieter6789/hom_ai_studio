import pytest

from hom_core.schemas.deployment import DeploymentRequest
from inference.vllm_provider import VLLMInferenceProvider, VLLMNotInstalled


@pytest.fixture
def provider(tmp_path):
    return VLLMInferenceProvider(registry_path=str(tmp_path / "registry.json"))


def test_health_check_reports_not_deployed_for_unknown_model(provider):
    result = provider.health_check("hom-crm-v3")

    assert result.healthy is False
    assert result.detail == "Not deployed"


def test_list_models_starts_empty(provider):
    assert provider.list_models() == []


def test_stop_model_on_unknown_deployment_is_a_no_op(provider):
    provider.stop_model("does-not-exist")  # must not raise


def test_deploy_without_vllm_installed_raises_clear_error(provider, monkeypatch):
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: None)

    request = DeploymentRequest(
        model_version_id="v3", served_model_name="hom-crm-v3", artifact_path="/artifacts/hom-crm-v3"
    )
    with pytest.raises(VLLMNotInstalled):
        provider.deploy_model(request)


def test_registry_persists_across_provider_instances(tmp_path, monkeypatch):
    registry_path = str(tmp_path / "registry.json")
    provider_a = VLLMInferenceProvider(registry_path=registry_path)

    # Simulate a deployment having been recorded without actually spawning
    # vLLM (that's exercised by the "not installed" test above).
    provider_a._save_registry({"hom-crm-v3": {"pid": 123, "port": 8100, "artifact_path": "/x", "started_at": "now"}})

    provider_b = VLLMInferenceProvider(registry_path=registry_path)
    assert provider_b.list_models() == ["hom-crm-v3"]
