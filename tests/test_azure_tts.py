import json
from llm.cli import cli
from click.testing import CliRunner
import os
import yaml


def test_azure_tts(httpx_mock, tmp_path):
    # Setup mock response
    expected_audio = b"mock-audio-content"
    httpx_mock.add_response(
        url="https://api.example.com/openai/deployments/tts-1/audio/speech?api-version=2024-02-15",
        method="POST",
        status_code=200,
        content=expected_audio,
    )

    # Create mock config
    config = {
        "api_base": "https://api.example.com",
        "api_version": "2024-02-15",
        "deployment_name": "tts-1",
    }

    azure_dir = tmp_path / "azure"
    azure_dir.mkdir()
    with open(azure_dir / "tts.yaml", "w") as f:
        yaml.dump(config, f)

    # Run command
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(
            cli,
            ["azure-tts", "Hello World", "--key", "test-key", "--output", "test.mp3"],
            env={"LLM_USER_PATH": str(tmp_path)},
        )

        # Verify output file was created with correct content
        assert os.path.exists("test.mp3")
        with open("test.mp3", "rb") as f:
            assert f.read() == expected_audio

    # Verify request
    request = httpx_mock.get_request()
    assert (
        request.url
        == "https://api.example.com/openai/deployments/tts-1/audio/speech?api-version=2024-02-15"
    )
    assert request.method == "POST"
    assert request.headers["api-key"] == "test-key"
    assert request.headers["Content-Type"] == "application/json"
    assert json.loads(request.read()) == {
        "model": "tts-1",
        "input": "Hello World",
        "voice": "onyx",  # Default voice
    }


def test_azure_tts_rate_limit(httpx_mock, tmp_path):
    # Setup mock response for rate limit
    httpx_mock.add_response(
        url="https://api.example.com/openai/deployments/tts-1/audio/speech?api-version=2024-02-15",
        method="POST",
        status_code=429,
        headers={"Retry-After": "30"},
    )

    # Create mock config
    config = {
        "api_base": "https://api.example.com",
        "api_version": "2024-02-15",
        "deployment_name": "tts-1",
    }

    azure_dir = tmp_path / "azure"
    azure_dir.mkdir()
    with open(azure_dir / "tts.yaml", "w") as f:
        yaml.dump(config, f)

    # Run command
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["azure-tts", "Hello World", "--key", "test-key"],
        env={"LLM_USER_PATH": str(tmp_path)},
    )

    assert (
        "Rate limit exceeded. Need to wait for 30 seconds before retrying."
        in result.output
    )
