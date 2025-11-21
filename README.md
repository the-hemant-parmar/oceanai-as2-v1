# Prompt-Driven Email Productivity Agent (Streamlit)

## Overview
This project is an Email Productivity Agent with:
- Streamlit frontend (UI)
- JSON-backed storage for prompts, mock inbox, processed outputs, and drafts
- LLM integration via Gemini. The app falls back to deterministic simple processors if no API key is provided.

Features:
- Load & view mock inbox
- Edit the "Prompt Brain" (categorization, action extraction, auto-reply)
- Run ingestion to categorize and extract tasks from emails
- Chat-like agent to summarize, extract tasks, and draft replies
- Draft manager to edit/save drafts (never sends emails automatically)

## Files
- `app.py` — Streamlit app
- `backend/` — backend modules (`db.py`, `prompts.py`, `ingestion.py`, `agent.py`, `drafts.py`)
- `data/` — data files: `mock_inbox.json`, `prompts.json`, `drafts.json`, `processed.json`
- `requirements.txt`

## Setup
1. Clone or copy files into folder `email_agent/`.
2. Create a Python venv if desired:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
