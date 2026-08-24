# AI Agent Security Control Plane

I started this project to understand what happens when an AI agent is given access to enterprise tools such as GitHub, cloud infrastructure, APIs, and data systems.

The main security question I want to explore is:

> Where should security decisions be enforced when the AI model itself cannot be treated as a trusted decision maker?

## Initial Goal

I am starting with a small, constrained agent and adding security controls incrementally. The first phase focuses on understanding tool invocation, authorization boundaries, least privilege, and auditability before adding more complex controls.

## What I Plan to Explore

- How an AI agent invokes external tools
- How to separate model decisions from security policy decisions
- Least privilege for agent and tool access
- Logging allowed and denied actions
- MCP security boundaries
- Policy as code for agent authorization
- Prompt injection and tool misuse testing
- Short-lived cloud access instead of broad standing privileges
- Detection and response for suspicious agent behavior

## First Milestone

Build a small agent with limited GitHub capabilities. Once the basic interaction works, I will introduce an authorization layer and test what happens when the agent attempts an action outside its approved permissions.

## Project Status

**Phase 1: Project foundation and security model**

The project is intentionally being built one layer at a time so that each security decision can be tested and documented before the next capability is introduced.
