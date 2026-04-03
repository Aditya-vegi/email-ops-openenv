---
title: email-ops-openenv
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
pinned: false
---

# 📧 Email Ops OpenEnv Environment

## 📌 Overview

This project implements a **real-world OpenEnv environment** that simulates an **Email Operations System**, where an AI agent performs:

- Email triage  
- Priority classification  
- Response generation  
- Escalation decision-making  

The environment follows the **OpenEnv specification** and exposes:

- `reset()`
- `step(action)`
- `state()`

---

## 🚀 Live Deployment

👉 https://ADITYA-VEGI-email-ops-openenv.hf.space/

### ✔ Deployment Status

- `/reset` endpoint → ✅ Working  
- Docker container → ✅ Running  
- Public Space → ✅ Accessible  

---

## 🎯 Objective

The agent must:

- Classify email priority correctly  
- Generate appropriate responses  
- Decide whether to escalate or resolve  
- Efficiently process multiple emails  

---

## 🌍 Real-World Relevance

This environment models real workflows used in:

- Customer support systems  
- IT incident response  
- Business communication pipelines  

Key challenges simulated:

- Time-sensitive emails  
- Multi-email queue management  
- Decision-based workflows  
- Resource constraints  

---



## 🏗️ Architecture Diagram
The system follows a modular OpenEnv architecture:
            +----------------------+
            |   LLM / Agent        |
            | (OpenAI Client)      |
            +----------+-----------+
                       |
                       | Actions (JSON)
                       ▼
            +----------------------+
            |   EmailEnv           |
            |  (Core Environment)  |
            +----------+-----------+
                       |
    ------------------------------------------
    |                |                        |
    ▼                ▼                        ▼
            +----------------------+
            |   LLM / Agent        |
            | (OpenAI Client)      |
            +----------+-----------+
                       |
                       | Actions (JSON)
                       ▼
            +----------------------+
            |   EmailEnv           |
            |  (Core Environment)  |
            +----------+-----------+
                       |
    ------------------------------------------
    |                |                        |
    ▼                ▼                        ▼


### 📥 Observation Space

```json
{
  "current": {
    "email_id": 1,
    "subject": "Production server down",
    "body": "Fix ASAP",
    "sender_role": "boss",
    "expected_priority": "urgent",
    "requires_escalation": true
  },
  "queue_size": 3,
  "last_action": "reply",
  "history": ["classify", "reply"]
}