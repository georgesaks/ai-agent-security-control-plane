# Local Run Guide

This guide runs the Phase 2 LLM agent locally without storing secrets in the repository.

## Prerequisites

- Git
- Python 3.11 or newer
- Docker Desktop if you want to run OPA locally
- `OPENAI_API_KEY` set as a user environment variable
- `AGENT_IDENTITY_SIGNING_SECRET` set as a user environment variable

## Clone and switch to Phase 2

```powershell
git clone https://github.com/georgesaks/ai-agent-security-control-plane.git
cd ai-agent-security-control-plane
git checkout phase-2-agent-mcp
```

## Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks local script execution for the current session, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Verify secrets without printing them

```powershell
if ($env:OPENAI_API_KEY) { "OPENAI_API_KEY is set" }
if ($env:AGENT_IDENTITY_SIGNING_SECRET) { "AGENT_IDENTITY_SIGNING_SECRET is set" }
```

## Run tests first

```powershell
python -m unittest discover -s tests -v
```

## Run the first live LLM agent

```powershell
python -m llm_agent.agent
```

The first run asks the model to read the approved repository summary. The model may choose the tool, but the request still passes through verified identity, authorization, and audit telemetry before execution.

## Optional: run OPA locally

```powershell
docker compose up opa
```

The current LLM path still uses the Python policy backend for the MCP gateway. A later step will switch the MCP gateway to OPA so the live agent is authorized by externalized Rego policy.

## Secret handling rules

Do not add either secret to source files, commits, issue comments, screenshots, or documentation. If a secret is accidentally committed, rotate it immediately and treat the exposed value as compromised.
