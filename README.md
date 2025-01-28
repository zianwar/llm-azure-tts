# llm-azure-tts

[![PyPI](https://img.shields.io/pypi/v/llm-azure-tts.svg)](https://pypi.org/project/llm-azure-tts/)
[![Changelog](https://img.shields.io/github/v/release/zianwar/llm-azure-tts?include_prereleases&label=changelog)](https://github.com/zianwar/llm-azure-tts/releases)
[![Tests](https://github.com/zianwar/llm-azure-tts/actions/workflows/test.yml/badge.svg)](https://github.com/zianwar/llm-azure-tts/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/zianwar/llm-azure-tts/blob/main/LICENSE)

Text-to-speech using the Azure OpenAI TTS API

## Installation

Install this plugin in the same environment as [LLM](https://llm.datasette.io/).

```bash
llm install llm-azure-tts
```

## Usage

The plugin adds a new command, `llm azure-tts`. Use it like this:

```bash
llm azure-tts "Hello" --output audio.mp3
```

The synthesized text will be output directly to the specified location.

For full options, run `llm azure-tts --help`.

The plugin will use the API key configured using:

```bash
llm keys set azure-tts
# Paste key here
```

You can also pass an explicit API key using `--key` like this:

```bash
llm azure-tts "Hello" --key $AZURE_OPENAI_TTS_API_KEY --output audio.mp3
```

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:

```bash
cd llm-azure-tts
python -m venv venv
source venv/bin/activate
```

Now install the dependencies and test dependencies:

```bash
llm install -e '.[test]'
```

To run the tests:

```bash
python -m pytest
```
