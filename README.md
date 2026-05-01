# 🤖 Claude PR Sentinel

An AI-powered GitHub Pull Request reviewer that automatically reviews PRs using Claude API and posts structured feedback as comments.

## Features

- Automatically triggers on PR open, update, or reopen
- Fetches the full diff and sends it to Claude for analysis
- Posts structured review with summary, issues, suggestions, security concerns, and score
- HMAC-SHA256 webhook signature verification
- Fully async FastAPI implementation

## Tech Stack

- Python 3.12, FastAPI, Anthropic Claude API, PyGithub

## Setup

cp .env.example .env
pip install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

## How It Works

1. GitHub sends a webhook on PR events
2. Bot fetches the PR diff via GitHub API
3. Diff is sent to Claude for code review
4. Structured review is posted as a PR comment
