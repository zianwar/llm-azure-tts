import os
import json
from click.testing import CliRunner
from llm.cli import cli
import pytest
import yaml


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_config(tmpdir):
    # Create a mock config file
    config_path = tmpdir.mkdir("azure").join("tts.yaml")
    config = {
        "api_base": "https://mock-api-base.com",
        "api_version": "2024-02-15-preview",
        "deployment_name": "mock-deployment",
    }
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f)
    return config_path


def test_azure_tts_success(httpx_mock, runner, mock_config):
    # Mock the API response
    expected_audio_content = b"mock-audio-content"
    httpx_mock.add_response(
        url="https://mock-api-base.com/openai/deployments/mock-deployment/audio/speech?api-version=2024-02-15-preview",
        method="POST",
        status_code=200,
        content=expected_audio_content,
    )

    # Set environment variables for the test
    os.environ["AZURE_OPENAI_TTS_API_BASE"] = "https://mock-api-base.com"
    os.environ["AZURE_OPENAI_TTS_API_VERSION"] = "2024-02-15-preview"
    os.environ["AZURE_OPENAI_TTS_DEPLOYMENT_NAME"] = "mock-deployment"

    # Run the command
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "azure-tts",
                "Hello, world!",
                "--key",
                "mock-api-key",
                "--output",
                "output.mp3",
            ],
        )

        # Verify the output
        assert result.exit_code == 0
        assert result.output == "output.mp3\n"

        # Verify the audio file was created with the correct content
        with open("output.mp3", "rb") as f:
            assert f.read() == expected_audio_content

    # Verify the API request
    request = httpx_mock.get_request()
    assert (
        request.url
        == "https://mock-api-base.com/openai/deployments/mock-deployment/audio/speech?api-version=2024-02-15-preview"
    )
    assert request.method == "POST"
    assert request.headers["api-key"] == "mock-api-key"
    assert request.headers["Content-Type"] == "application/json"

    # Parse the request body manually
    request_body = json.loads(request.read())
    assert request_body == {
        "model": "mock-deployment",
        "input": "Hello, world!",
        "voice": "onyx",  # Default voice
    }
