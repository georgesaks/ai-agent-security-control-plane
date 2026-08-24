# AI Agent Security Control Plane

I started this project to understand what happens when an AI agent is given access to enterprise tools such as GitHub, cloud infrastructure, APIs, and data systems.

The main security question I am exploring is:

> Where should security decisions be enforced when the AI model itself cannot be treated as a trusted decision maker?

The project is being built incrementally. Each control is implemented, attacked, tested, and documented before the next capability is introduced.

## Security Objectives

- Separate model intent from authorization decisions
- Give agents verifiable identities rather than trusting caller-supplied metadata
- Enforce least privilege at the tool boundary
- Default deny unknown or unauthorized tools
- Treat production writes differently from lower-risk operations
- Generate structured audit evidence for every authorization decision
- Detect and correlate suspicious agent behavior
- Contain compromised agents independently of the model
- Adapt authorization based on runtime behavioral risk

## Architecture So Far

```text
LLM / AI Agent
      |
      v
Signed Agent Identity
      |
      v
MCP Security Gateway
      |
      +--> Containment State
      |
      +--> Adaptive Risk
      |
      +--> Authorization Policy
      |
      v
Approved Tool Registry
      |
      v
Tool Execution
      |
      v
Structured Audit Telemetry
      |
      v
Detection + Correlation
      |
      v
Containment / Dynamic Access Revocation
```

The model can request an action, but it does not make the final authorization decision. The security control plane does.

## Project Status

### Phase 1: Foundation and security model — COMPLETE

Established the initial trust model and security boundary for agent tool access.

Validated capabilities:

- Constrained MCP-style tool registry
- Default-deny behavior for unregistered tools
- Role and environment-aware authorization
- Separation of policy evaluation from tool execution
- Structured audit events for ALLOW and DENY decisions
- Initial automated security tests

### Phase 2: Live agent security control plane — ACTIVE

Connected a live LLM agent to the security boundary and began testing how the system behaves under normal and adversarial conditions.

Validated milestones:

- Live OpenAI model invocation through the agent
- Signed agent identity and signature verification
- Rejection of expired, tampered, or incorrectly signed identities
- Successful authorized repository-summary tool invocation
- Production write restrictions enforced outside the model
- Controlled prompt-injection experiment
- Compromised-agent simulation where model-level defenses are assumed to have failed
- Production write attempt blocked by the external policy layer
- Structured security telemetry for agent activity
- High-severity detections for denied production and write-oriented actions
- Correlation of repeated denials into `AI-003` critical detection
- Automated quarantine following critical agent behavior
- Post-containment denial of an operation that would normally be authorized
- Adaptive behavioral risk scoring from LOW to MEDIUM to HIGH to CRITICAL
- Risk-based restriction of write capabilities at HIGH risk
- Automatic quarantine and access revocation at CRITICAL risk
- 28 automated security tests passing across identity, policy, gateway, telemetry, detection, containment, and adaptive-risk controls

Current control loop:

```text
Prevent -> Observe -> Detect -> Correlate -> Contain -> Adapt -> Audit
```

### Phase 3: Approval workflows and stronger enterprise controls — PLANNED

The next phase will explore controls for sensitive operations that should not be fully autonomous, including human approval boundaries and additional enterprise policy enforcement. Phase 3 capabilities will be documented here only after they are implemented and validated.

## Experiments and Evidence

The project is being developed as an engineering case study, so successful controls and useful failures are both retained as evidence.

Evidence captured so far includes:

1. Automated security test suite validating the initial control plane
2. Live LLM tool invocation authorized through the security gateway
3. Prompt-injection attempt recognized without tool execution
4. Compromised-agent production write blocked by external authorization
5. Repeated malicious behavior correlated into a critical detection
6. Automated quarantine with post-containment access denial
7. Adaptive risk progression causing dynamic restriction and quarantine
8. Regression suite reaching 28 passing security tests

Sensitive information such as API keys, signing secrets, payment information, and account identifiers is intentionally excluded from project evidence.

## Current Learning

A recurring design principle from the experiments so far is that model behavior alone is not a sufficient security boundary. Prompt-injection resistance is useful, but authorization, identity verification, telemetry, detection, and containment need to exist outside the model so that a manipulated or compromised agent cannot directly convert intent into privileged action.

## Next Milestone

Introduce a human-in-the-loop authorization state for sensitive operations so the control plane can distinguish among actions that can be automatically allowed, automatically denied, or held for explicit approval.
