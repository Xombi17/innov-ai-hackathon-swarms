# WellSync AI API

Multi-Agent Wellness Orchestrator.

## Overview
WellSync AI is an autonomous agent system that coordinates Fitness, Nutrition, Sleep, and Mental Wellness agents to generate personalized, realistic wellness plans that adapt to your real-world constraints.

## Deployment on Hugging Face Spaces
This repository is configured to deploy directly to Hugging Face Spaces using Docker.

1. **Create a Space**: Select "Docker" as the SDK.
2. **Environment Variables**: Set `OPENAI_API_KEY` in the Space's configuration secrets.
3. **Push Code**: Push this repository to the Space.

## Local Development

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment**:
   Create a `.env` file with your `OPENAI_API_KEY`.

3. **Run API**:
   ```bash
   python run_api.py
   ```

## API Endpoints

- `POST /wellness-plan`: Generate a new wellness plan.
- `GET /health`: Health check.