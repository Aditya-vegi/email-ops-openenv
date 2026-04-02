# Email Ops OpenEnv

## Overview
This environment simulates real-world enterprise email operations including triage, prioritization, and response generation.

## Tasks
- Easy: Basic classification
- Medium: Context-aware replies
- Hard: Risk & escalation handling

## Observation Space
- subject
- body
- sender_role

## Action Space
- classification
- action
- response

## Setup

docker build -t email-env .
docker run -p 7860:7860 email-env

## Inference

export API_BASE_URL=...
export MODEL_NAME=...
export HF_TOKEN=...

python inference.py

## Baseline Scores
- easy: ~0.7
- medium: ~0.6
- hard: ~0.5