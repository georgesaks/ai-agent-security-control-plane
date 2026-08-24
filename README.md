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
- Require explicit human authorization for selected sensitive operations
- Prevent approval reuse and bind authorization to the reviewed action

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
      +--> Human Approval Boundary
      |         |
      |         +--> APPROVE / REJECT
      |         +--> Action-bound, single-use approval
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
- 28 automated security tests passing at the adaptive-risk milestone

Current control loop:

```text
Prevent -> Observe -> Detect -> Correlate -> Contain -> Adapt -> Audit
```

### Phase 3: Human approval and stronger enterprise controls — ACTIVE

Introduced a human-in-the-loop authorization boundary for sensitive AI-agent operations that should not execute autonomously.

Validated milestones:

- New `REQUIRE_APPROVAL` authorization outcome for sensitive actions
- Sensitive `create_issue_draft` request held before tool execution
- Explicit human reviewer approval required before execution
- Approval bound to actor, role, environment, tool, and exact action arguments
- SHA-256 digest used to bind approval to the reviewed arguments
- Approved action executed only after the gateway validates the approval
- Approval consumed after successful use
- Replay of the consumed approval denied
- Audit telemetry records `REQUIRE_APPROVAL` and post-approval `ALLOW` decisions
- Demonstration uses a local issue draft and performs no GitHub write
- Negative-path attack suite validates fail-closed approval behavior
- Fabricated or nonexistent approval identifiers are denied
- Explicitly rejected human approvals are denied
- Post-approval argument modification is detected and denied
- Exact human-reviewed action remains valid after a failed tampering attempt
- Consumed approval replay is denied
- Regression suite increased to 35 passing automated security tests

Validated approval flow:

```text
Agent requests sensitive action
            |
            v
     Security Gateway
            |
            v
     REQUIRE_APPROVAL
            |
            v
       Human Review
        /        \
    REJECT      APPROVE
      |            |
     DENY          v
              Execute exact
             approved action
                  |
                  v
           Consume approval
                  |
                  v
          Replay attempt -> DENY
```

Approval attack validation:

```text
No valid approval             -> DENY
Human rejects                 -> DENY
Approved action is modified   -> DENY
Exact reviewed action         -> ALLOW
Consumed approval is replayed -> DENY
```

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
8. Regression suite reaching 28 passing security tests at the adaptive-risk milestone
9. Sensitive agent action intercepted with `REQUIRE_APPROVAL`
10. Human reviewer approval allowing only the reviewed action
11. Consumed approval replay attempt denied
12. Regression suite reaching 31 passing security tests after initial approval controls
13. Approval bypass attack suite validates missing, rejected, modified, and replayed approval denial paths
14. Exact reviewed action remains executable while modified arguments fail integrity validation
15. Regression suite reaching 35 passing security tests after approval negative-path validation

Sensitive information such as API keys, signing secrets, payment information, and account identifiers is intentionally excluded from project evidence.

## Current Learning

A recurring design principle from the experiments so far is that model behavior alone is not a sufficient security boundary. Prompt-injection resistance is useful, but authorization, identity verification, telemetry, detection, containment, adaptive risk, and approval controls need to exist outside the model so that a manipulated or compromised agent cannot directly convert intent into privileged action.

The approval experiments add another principle: human approval should not be treated as a reusable boolean. Authorization needs to be bound to the exact action that was reviewed and consumed after execution. The negative-path tests demonstrate that the control fails closed when an approval is absent, rejected, altered, or replayed.

## Next Milestone

Add time-bounded approvals and approval expiration so a previously approved sensitive action cannot remain executable indefinitely, then validate expiration and stale-approval denial paths before progressing to broader enterprise controls.
