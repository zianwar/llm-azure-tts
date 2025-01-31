import sys
import time
import os
import click
import httpx
import llm
import yaml


@llm.hookimpl
def register_commands(cli):
    @cli.command()
    @click.argument("text", type=click.STRING, default="-")
    @click.option("api_key", "--key", help="API key to use")
    @click.option(
        "voice",
        "--voice",
        type=click.Choice(["alloy", "echo", "fable", "onyx", "nova", "shimmer"]),
        default="onyx",
        help="Voice to use, available: alloy, echo, fable, onyx, nova, and shimmer",
    )
    @click.option(
        "output",
        "--output",
        type=click.File("wb"),
        default=sys.stdout,
        help="Output file path",
    )
    def azure_tts(text, api_key, voice, output):
        """
        Convert text to speech using the Azure Text-to-Speech API

        Usage:

        \b
            llm azure-tts "Hello there!" --output audio.mp3
        """

        if text == "-":
            text = click.get_text_stream("stdin").read()

        if not text:
            raise click.UsageError(
                "Text input is required. Pass text as argument or pipe it from stdin."
            )

        config = get_config()
        # Extract environment variables
        azure_api_base = os.getenv("AZURE_OPENAI_TTS_API_BASE", config["api_base"])
        azure_api_version = os.getenv(
            "AZURE_OPENAI_TTS_API_VERSION", config["api_version"]
        )
        azure_deployment_name = os.getenv(
            "AZURE_OPENAI_TTS_DEPLOYMENT_NAME", config["deployment_name"]
        )

        key = llm.get_key(api_key, "azure-tts")
        if not key:
            raise click.ClickException(
                "Azure API key is required. set it by running: `llm keys set azure-tts`"
            )
        try:
            audio_content = synthesize_speech(
                text,
                voice,
                azure_api_base,
                azure_api_version,
                azure_deployment_name,
                key,
            )

            if output is sys.stdout:
                output.buffer.write(audio_content)
            else:
                output.write(audio_content)

        except httpx.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                # Try to parse Retry-After as seconds
                retry_after = e.response.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait_time = int(retry_after)
                    except ValueError:
                        # If Retry-After is a timestamp, calculate the difference
                        retry_after_time = time.mktime(
                            time.strptime(retry_after, "%a, %d %b %Y %H:%M:%S GMT")
                        )
                        wait_time = max(0, retry_after_time - time.time())
                    print(
                        f"Rate limit exceeded. Need to wait for {wait_time:.0f} seconds before retrying."
                    )
                else:
                    print("Rate limit exceeded. Need to wait before retrying.")
            else:
                raise click.ClickException(str(e))


def synthesize_speech(
    text: str,
    voice: str,
    azure_api_base: str,
    azure_api_version: str,
    azure_deployment_name: str,
    api_key: str,
) -> bytes:
    """
    Synthesize speech from text using Azure's Text-to-Speech API.

    Args:
        text (str): The text to convert to speech.
        voice (str): The voice to use for speech synthesis (e.g., "onyx", "alloy").
        azure_api_base (str): The base URL for the Azure OpenAI API endpoint.
        azure_api_version (str): The API version to use (e.g., "2024-02-15-preview").
        azure_deployment_name (str): The name of the deployment for the text-to-speech model.
        api_key (str): The API key for authenticating requests to the Azure OpenAI service.

    Returns:
        bytes: The audio content as bytes.

    Raises:
        httpx.RequestError: If the API request fails due to network issues or invalid parameters.
        httpx.HTTPStatusError: If the API returns a non-successful HTTP status code (e.g., 429 Too Many Requests).
    """
    with httpx.Client() as client:
        response = client.post(
            url=f"{azure_api_base}/openai/deployments/{azure_deployment_name}/audio/speech?api-version={azure_api_version}",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "model": azure_deployment_name,
                "input": text,
                "voice": voice,
            },
        )
        response.raise_for_status()
        return response.content


def get_config() -> dict:
    dir_path = os.path.join(llm.user_dir(), "azure")
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
        return {}
    with open(os.path.join(dir_path, "tts.yaml")) as f:
        return yaml.safe_load(f)
