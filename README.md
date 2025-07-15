[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Whisper Docker Setup

This is a Docker setup with a FastAPI proxy that provides basic authentication for the Whisper ASR (Automatic Speech Recognition) service.

## Prerequisites

- Docker and Docker Compose
- Access to the ITKDev Docker commands (`idc`)

## Setup

1. Copy the example environment file and configure it for your needs:
```shell
cp .env.example .env
``` 

2. Update the API key and other configuration in the `.env` file:
   - `API_KEY`: Set a secure API key for authentication
   - `ASR_ENGINE`: Choose the ASR engine (default: openai_whisper)
   - `ASR_MODEL`: Set the model to use (default: large-v3)

3. Build and start the containers:
```shell
idc build --pull --no-cache
idc up -d
``` 

## Configuration Options

The following environment variables can be configured in your `.env` file:

- `COMPOSE_PROJECT_NAME`: Project name for Docker Compose (default: whisper)
- `COMPOSE_DOMAIN`: Domain for local development (default: whisper.local.itkdev.dk)
- `API_KEY`: Authentication key for the API
- `WHISPER_ENDPOINT`: Internal endpoint for the Whisper service
- `ASR_ENGINE`: Speech recognition engine to use
- `ASR_MODEL`: Model to use for speech recognition

## API Documentation

The API documentation is available at [/docs](/docs) after starting the services.

## Links

* [Whisper ASR Webservice Documentation](https://ahmetoner.com/whisper-asr-webservice/endpoints/)
* [FastAPI Documentation](https://fastapi.tiangolo.com/)
* [OpenAI Speech to text API](https://platform.openai.com/docs/guides/speech-to-text)
