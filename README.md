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
- Expire stale approvals so authorization is time-bounded
- Restrict sensitive approvals to authorized reviewer identities
- Enforce separation of duties between requester and approver
- Require two distinct authorized reviewers for highest-impact actions
- Enforce four-eyes authorization at the MCP gateway before critical tool execution
- Centralize action sensitivity classification in policy rather than hard-coding tool behavior in the gateway
- Externalize authorization decisions into OPA/Rego policy-as-code
- Fail closed when the external policy decision point is unavailable or invalid

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
      +--> OPA / Rego Authorization Policy
      |         |
      |         +--> READ_ONLY
      |         +--> SENSITIVE
      |         +--> CRITICAL
      |         +--> UNKNOWN -> DENY
      |         +--> Policy failure -> DENY
      |
      +--> Human Approval Boundary
      |         |
      |         +--> Sensitive action: single authorized reviewer
      |         +--> Critical action: two distinct authorized reviewers
      |         +--> Requester != reviewer(s)
      |         +--> Action-bound approval
      |         +--> Single-use consumption
      |         +--> Time-bounded expiration
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
Adaptive Risk Escalation
      |
      v
Containment / Dynamic Access Revocation
```

The model can request an action, but it does not make the final authorization decision. OPA/Rego evaluates authorization and classifies the action, while the MCP security gateway enforces the resulting runtime control.

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

### Phase 2: Live agent security control plane — COMPLETE

Connected a live LLM agent to the security boundary and tested how the system behaves under normal and adversarial conditions.

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

### Phase 3: Human approval and stronger enterprise controls — COMPLETE

Introduced human-in-the-loop authorization boundaries for sensitive and critical AI-agent operations that should not execute autonomously.

Validated milestones:

- `REQUIRE_APPROVAL` authorization outcome for sensitive actions
- Sensitive requests held before tool execution
- Explicit human reviewer approval required before execution
- Approval bound to actor, role, environment, tool, and exact action arguments
- SHA-256 digest binds approval to reviewed arguments
- Approval consumed after successful use and replay denied
- Time-bounded approvals with a default 300-second TTL
- Sensitive approvals restricted to an explicit authorized-reviewer set
- Separation of duties prevents requester self-approval
- Dual-control approval for highest-impact actions
- One reviewer is insufficient for critical execution
- Same reviewer cannot satisfy both approval slots
- Two distinct authorized reviewers satisfy four-eyes authorization
- Critical approval remains action-bound, time-bounded, and single-use
- Gateway denies post-approval argument tampering and execution replay
- Centralized policy classification with `READ_ONLY`, `SENSITIVE`, `CRITICAL`, and `UNKNOWN`
- Approval workflow selection driven by policy classification rather than hard-coded tool names
- HIGH adaptive risk restriction applies generically to `SENSITIVE` and `CRITICAL` actions
- Production policy denies `SENSITIVE` and `CRITICAL` actions in this prototype
- Regression suite reached 64 passing automated security tests

### Phase 4: OPA/Rego policy-as-code — COMPLETE

Externalized the authorization decision point from the Python policy implementation into Open Policy Agent using Rego.

Validated milestones:

- Rego policy created for role permissions, environment restrictions, and action classification
- Manual OPA evaluations validated `READ_ONLY`, `SENSITIVE`, and `CRITICAL` decisions
- Python and Rego engines executed in shadow/parity mode before migration
- Eight automated parity scenarios validated matching allow/deny, classification, and reason behavior
- Regression suite reached 72 passing tests during policy parity validation
- Fail-closed OPA adapter introduced between the gateway and policy decision point
- Missing OPA executable produces DENY rather than permissive fallback
- Invalid or broken Rego policy produces DENY
- Malformed or invalid OPA response produces DENY
- Regression suite reached 78 passing tests before enforcement migration
- MCP gateway migrated from embedded Python authorization to OPA/Rego decisions
- Existing 78-test security suite remained green after OPA became the enforcement decision source
- Dedicated OPA enforcement-boundary attack suite added
- Unknown role escalation denied by OPA at the gateway
- Auditor-to-sensitive privilege escalation denied
- Production sensitive and critical actions denied before approval workflows are created
- Unregistered attacker-supplied tools denied before policy evaluation
- Simulated OPA unavailability prevents tool execution
- Invalid policy decision prevents tool execution
- Audit telemetry records fail-closed gateway denials
- Regression and adversarial suite reached 85 passing automated security tests

### Phase 5: Integrated adversarial validation — COMPLETE

Executed the complete security control plane as one adversarial scenario rather than as isolated controls.

Validated sequence:

- Assumed the AI agent was already compromised
- Compromised developer agent attempted a `SENSITIVE` production action three times
- OPA/Rego denied every production write before any human approval workflow could be created
- Each denial generated structured audit telemetry
- `AI-001` detected denied production activity
- `AI-002` detected blocked write-oriented activity
- Adaptive risk increased from 30/MEDIUM to 60/HIGH to 90/CRITICAL
- Three denied actions correlated into `AI-003` with CRITICAL severity
- Actor was moved to `QUARANTINED`
- A normally authorized `READ_ONLY` development action was attempted after containment
- Quarantine overrode the otherwise-valid OPA authorization path and denied access
- Final demonstration completed with `FINAL RESULT: PASS`
- Compromised model intent never became privileged tool execution

Integrated attack path:

```text
Compromised AI Agent
        |
        v
Production SENSITIVE request
        |
        v
OPA / Rego -> DENY
        |
        +--> No approval request created
        |
        v
Structured Audit Event
        |
        v
AI-001 + AI-002
        |
        v
Adaptive Risk
30 MEDIUM -> 60 HIGH -> 90 CRITICAL
        |
        v
AI-003 Correlation
        |
        v
QUARANTINE
        |
        v
Normally allowed READ_ONLY request
        |
        v
DENY because actor is quarantined
```

## Policy-Driven Enforcement

The gateway no longer decides approval level from specific tool names and no longer owns the primary authorization policy. OPA/Rego returns both authorization and sensitivity classification, and the gateway applies the matching runtime control.

```text
OPA / Rego decision
        |
        +--> READ_ONLY + ALLOW
        |       |
        |       v
        |    Normal execution
        |
        +--> SENSITIVE + ALLOW
        |       |
        |       v
        |    REQUIRE_APPROVAL
        |       |
        |       v
        |    One authorized independent reviewer
        |
        +--> CRITICAL + ALLOW
        |       |
        |       v
        |    REQUIRE_DUAL_APPROVAL
        |       |
        |       v
        |    Two distinct authorized independent reviewers
        |
        +--> DENY / UNKNOWN / POLICY FAILURE
                |
                v
              DENY
```

This separates the policy decision point from the policy enforcement point. Rego owns the authorization policy, while the MCP gateway owns enforcement, approval orchestration, adaptive-risk restrictions, tool dispatch, and audit generation.

## Approval Attack Validation

```text
No valid approval                  -> DENY
Human rejects                      -> DENY
Approved action is modified        -> DENY
Exact reviewed action              -> ALLOW
Consumed approval is replayed      -> DENY
Fresh approval inside TTL          -> ALLOW
Stale approval after TTL           -> DENY
Expired approval retry             -> DENY
Late human review                  -> DENY
Unauthorized reviewer              -> DENY
Fabricated reviewer                -> DENY
Self approval                      -> DENY
Authorized security reviewer       -> ALLOW
One critical reviewer only         -> DENY
Same critical reviewer twice       -> DENY
Unauthorized second reviewer       -> DENY
Critical action tampering          -> DENY
Two authorized critical reviewers  -> ALLOW
Critical execution replay          -> DENY
```

## OPA Enforcement Attack Validation

```text
Unknown role                       -> DENY
Auditor requests sensitive action  -> DENY
Sensitive production action        -> DENY before approval
Critical production action         -> DENY before dual approval
Unregistered tool                  -> DENY before policy evaluation
OPA unavailable                    -> DENY; handler unreachable
Invalid OPA decision               -> DENY; handler unreachable
Broken policy                      -> DENY
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
8. Sensitive agent action intercepted with `REQUIRE_APPROVAL`
9. Human reviewer approval allowing only the reviewed action
10. Consumed approval replay attempt denied
11. Approval bypass attack suite validates missing, rejected, modified, and replayed approval denial paths
12. Time-bounded approval validation denies stale authorization
13. Reviewer authorization attack suite blocks unauthorized and fabricated reviewers
14. Separation-of-duties test blocks requester self-approval
15. Dual-approval attack suite validates one-reviewer, duplicate-reviewer, unauthorized-reviewer, tampering, and replay denial paths
16. Two distinct authorized reviewers satisfy four-eyes authorization
17. Central policy classification validated for READ_ONLY, SENSITIVE, CRITICAL, and UNKNOWN actions
18. Python/Rego shadow-mode parity validated before enforcement migration
19. OPA adapter validated to fail closed on policy-engine failure
20. MCP gateway successfully migrated to OPA/Rego authorization without regression
21. OPA enforcement boundary attacked for role escalation, production escalation, unregistered tools, policy unavailability, and invalid decisions
22. Regression and adversarial suite reaches 85 passing automated security tests
23. Final integrated scenario shows repeated compromised-agent production writes denied by OPA before approval creation
24. Integrated telemetry generates AI-001 and AI-002 findings on each malicious write attempt
25. Adaptive risk escalates 30/MEDIUM -> 60/HIGH -> 90/CRITICAL
26. AI-003 correlates the repeated denials into a CRITICAL finding
27. Actor transitions to QUARANTINED with an explainable containment reason
28. Post-quarantine READ_ONLY access is denied despite otherwise-valid role and environment
29. Final integrated adversarial scenario completes with `FINAL RESULT: PASS`

Sensitive information such as API keys, signing secrets, payment information, and account identifiers is intentionally excluded from project evidence.

## Current Learning

A recurring design principle from the experiments is that model behavior alone is not a sufficient security boundary. Prompt-injection resistance is useful, but authorization, identity verification, telemetry, detection, containment, adaptive risk, and approval controls need to exist outside the model so that a manipulated or compromised agent cannot directly convert intent into privileged action.

The approval experiments show that human approval should not be treated as a reusable boolean. Authorization needs to be bound to the exact action reviewed, consumed after execution, limited in time, and granted only by authorized reviewers independent of the requester. Critical operations require two distinct authorized reviewers before the tool handler is reachable.

The OPA migration adds another architectural lesson: externalizing policy only improves the security boundary if policy-engine failure is handled safely. The gateway therefore treats unavailable, broken, or invalid policy evaluation as a denial and keeps the protected tool handler unreachable.

The final integrated scenario reinforces the core design thesis of the project: a compromised model does not have to be trusted to recover or behave correctly when deterministic controls outside the model remain authoritative. Policy, telemetry, adaptive risk, correlation, and containment can interrupt the path from malicious intent to privileged execution.

## Next Milestone

Core engineering validation is complete. The next phase is packaging and evidence: finalize the architecture diagram, threat model, attack-path documentation, evidence catalog, screenshots, security design narrative, and portfolio presentation. Additional infrastructure integrations are considered future extensions rather than requirements for the core project.
