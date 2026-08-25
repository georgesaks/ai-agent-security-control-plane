# AI Agent Security Control Plane Evidence Catalog

## Purpose

This catalog organizes the engineering evidence generated while building and attacking the AI Agent Security Control Plane. The goal is to make the project easy to review in an interview, portfolio walkthrough, or security design discussion without requiring a reviewer to inspect every source file.

The catalog focuses on evidence that proves a control was implemented, exercised, attacked, and validated.

## Evidence Summary

The project currently includes:

- 85 passing automated regression and adversarial tests
- live LLM invocation through a security gateway
- signed agent identity validation
- OPA/Rego policy-as-code enforcement
- sensitive and critical action classification
- single-person approval for sensitive operations
- four-eyes approval for critical operations
- approval tamper, expiry, and replay resistance
- structured audit telemetry
- AI-specific detections and correlation
- adaptive behavioral risk
- automated quarantine and post-containment denial
- a final integrated compromised-agent scenario that ends in `FINAL RESULT: PASS`

## Milestone Evidence

| Evidence ID | Milestone | What It Proves | Primary Artifact | Result |
|---|---|---|---|---|
| E01 | Initial gateway controls | Unregistered tools and unauthorized actions fail closed | test suite / attack lab | PASS |
| E02 | Signed identity | Actor and role claims cannot be modified without detection | identity tests | PASS |
| E03 | Live model integration | A real LLM can request a tool through the controlled path | live agent demo | PASS |
| E04 | Prompt injection experiment | Unsafe model intent does not itself authorize tool execution | prompt injection demo | PASS |
| E05 | Compromised-agent simulation | External policy still blocks production writes when model behavior is assumed compromised | compromised agent demo | PASS |
| E06 | Security telemetry | Gateway decisions produce structured audit evidence | audit module / demos | PASS |
| E07 | Detection rules | Denied production and write actions produce `AI-001` and `AI-002` | detection demo | PASS |
| E08 | Correlation | Repeated denials generate `AI-003` CRITICAL detection | detection / containment demo | PASS |
| E09 | Containment | Critical behavior can move an actor to `QUARANTINED` | containment demo | PASS |
| E10 | Post-containment denial | A normally allowed read is denied after quarantine | containment demo | PASS |
| E11 | Adaptive risk | Risk progresses LOW → MEDIUM → HIGH → CRITICAL based on observed behavior | adaptive risk demo | PASS |
| E12 | Sensitive approval | `SENSITIVE` action requires explicit human approval | approval demo | PASS |
| E13 | Approval action binding | Human approval is valid only for the exact reviewed arguments | approval bypass tests | PASS |
| E14 | Approval replay defense | Consumed approval cannot be reused | approval tests | PASS |
| E15 | Approval expiration | Stale approvals fail after TTL | approval expiration demo | PASS |
| E16 | Reviewer authorization | Unauthorized reviewer identities cannot approve actions | reviewer authorization demo | PASS |
| E17 | Separation of duties | Requesting actor cannot approve its own action | reviewer authorization tests | PASS |
| E18 | Dual approval primitive | One reviewer is insufficient for critical actions | dual approval tests | PASS |
| E19 | Four-eyes enforcement | Two distinct authorized reviewers are required at the actual gateway | gateway dual approval tests | PASS |
| E20 | Critical tamper defense | Critical action modification after approval is denied | gateway dual approval tests | PASS |
| E21 | Policy classification | Actions are classified `READ_ONLY`, `SENSITIVE`, `CRITICAL`, or `UNKNOWN` | policy classification tests | PASS |
| E22 | Python/Rego parity | Rego behavior matched the working Python policy before migration | OPA parity tests | PASS |
| E23 | Fail-closed OPA adapter | Missing or invalid OPA execution returns DENY | OPA adapter tests | PASS |
| E24 | OPA enforcement migration | Gateway uses OPA/Rego as the actual authorization decision source | gateway regression suite | PASS |
| E25 | OPA boundary attacks | Unknown role, production escalation, invalid policy, and unavailable OPA all fail closed | OPA enforcement tests | PASS |
| E26 | Integrated adversarial scenario | Compromised agent is denied, detected, risk-escalated, correlated, quarantined, and blocked after containment | final control plane demo | PASS |

## Automated Test Progression

The test count grew as each control was added and then attacked.

| Test Milestone | Security Capability Added |
|---:|---|
| 28 | Adaptive risk and containment baseline |
| 31 | Initial sensitive approval workflow |
| 35 | Approval bypass negative-path testing |
| 39 | Approval expiration controls |
| 44 | Reviewer authorization and separation of duties |
| 52 | Dual approval primitive |
| 57 | Four-eyes enforcement at the gateway |
| 64 | Centralized action classification |
| 72 | Python ↔ OPA/Rego parity |
| 78 | Fail-closed OPA adapter and enforcement readiness |
| 78 | Gateway migrated to OPA/Rego with no regression |
| 85 | OPA enforcement boundary adversarial testing |

Current validation command:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 85 tests
OK
```

## Final Integrated Scenario Evidence

The most important single portfolio artifact is the final compromised-agent demonstration.

Command:

```powershell
python -m attacks.final_control_plane_demo
```

Validated sequence:

```text
Compromised agent
    ↓
Production SENSITIVE action
    ↓
OPA DENY
    ↓
No approval created
    ↓
AI-001 + AI-002
    ↓
Risk 30 / MEDIUM
    ↓
Second denial
    ↓
Risk 60 / HIGH
    ↓
Third denial
    ↓
Risk 90 / CRITICAL
    ↓
AI-003 correlation
    ↓
QUARANTINED
    ↓
Normally allowed READ_ONLY action
    ↓
DENY because actor is quarantined
    ↓
FINAL RESULT: PASS
```

This scenario is the best evidence that the project works as a coherent security control plane rather than as a collection of disconnected features.

## Recommended Screenshot Set

For portfolio use, keep a small curated set rather than every screenshot captured during development.

### Screenshot S01: Clean 85-Test Regression Run

Capture the terminal showing:

```text
Ran 85 tests
OK
```

Why it matters: proves the final control plane passes the complete automated suite.

### Screenshot S02: OPA CLI Installed and Working

Capture:

```text
opa version
```

plus the OPA version and `Rego Version: v1` output.

Why it matters: establishes the real policy engine used during validation.

### Screenshot S03: Manual READ_ONLY Rego Decision

Capture the manual policy evaluation returning:

```text
"allowed": true
"classification": "READ_ONLY"
"reason": "policy requirements satisfied"
```

Why it matters: visually demonstrates Rego making the policy decision.

### Screenshot S04: Sensitive / Critical Policy Classification

Capture either the `SENSITIVE` or `CRITICAL` OPA evaluation output.

Why it matters: demonstrates that approval level comes from policy classification rather than gateway hard-coding.

### Screenshot S05: Four-Eyes Approval Test Milestone

Capture the terminal showing the gateway dual-approval tests passing or the 57-test milestone.

Why it matters: shows critical actions require two authorized reviewers.

### Screenshot S06: Final Integrated Adversarial Scenario

Capture the full terminal output from:

```powershell
python -m attacks.final_control_plane_demo
```

The screenshot should visibly include:

- `GATEWAY: DENY`
- `DETECTIONS: AI-001, AI-002`
- `ADAPTIVE RISK: 90 / CRITICAL`
- `AI-003`
- `CONTAINMENT: QUARANTINED`
- post-quarantine `RESULT: DENY`
- `FINAL RESULT: PASS`

Why it matters: this is the strongest single demonstration in the project.

## Code Evidence Map

| Control Area | Primary Files |
|---|---|
| Agent identity | `identity/agent_identity.py` |
| MCP enforcement | `mcp_server/gateway.py` |
| Tool registry | `mcp_server/server.py` |
| Rego policy | `policy/opa/agent_policy.rego` |
| OPA adapter | `policy/opa_engine.py` |
| Sensitive approval | `approval/workflow.py` |
| Dual approval | `approval/dual_workflow.py` |
| Audit telemetry | `telemetry/audit.py` |
| Detection rules | `telemetry/detection.py` |
| Adaptive risk | `risk/adaptive_risk.py` |
| Containment | `response/containment.py` |
| Final adversarial demo | `attacks/final_control_plane_demo.py` |
| Architecture | `docs/architecture.md` |
| Threat model | `docs/threat-model.md` |

## Attack Evidence Map

| Attack / Failure Mode | Expected Security Result |
|---|---|
| Identity token tampering | Verification failure |
| Expired identity | Verification failure |
| Auditor requests sensitive tool | DENY |
| Unknown tool | DENY before execution |
| Prompt injection changes model intent | External controls still authoritative |
| Production sensitive action | DENY before approval |
| Production critical action | DENY before dual approval |
| Missing approval | DENY |
| Rejected approval | DENY |
| Changed approved arguments | DENY |
| Expired approval | DENY |
| Replayed approval | DENY |
| Unauthorized reviewer | DENY |
| Self approval | DENY |
| One reviewer for critical action | DENY |
| Same reviewer twice | DENY |
| Critical action tampering | DENY |
| OPA unavailable | DENY |
| Broken Rego policy | DENY |
| Invalid OPA decision | DENY |
| Repeated forbidden actions | Risk escalation + correlation |
| Access after quarantine | DENY |

## Interview Walkthrough Order

A concise interview walkthrough should follow this sequence:

1. **Problem:** LLMs are not trustworthy authorization boundaries.
2. **Architecture:** Put a deterministic MCP security gateway between agent intent and enterprise tools.
3. **Identity:** Verify short-lived signed workload identity outside the model.
4. **Authorization:** Externalize policy to OPA/Rego.
5. **Classification:** Map actions to `READ_ONLY`, `SENSITIVE`, and `CRITICAL`.
6. **Human control:** Require one reviewer for sensitive actions and two for critical actions.
7. **Integrity:** Bind approvals to exact arguments, TTL, reviewer identity, and single-use state.
8. **Detection:** Generate structured audit events and AI-specific detections.
9. **Adaptive response:** Raise behavioral risk and quarantine compromised agents.
10. **Proof:** Show 85 passing tests and the final integrated adversarial scenario.

## What Not to Include in Public Evidence

Do not publish:

- OpenAI API keys
- signing secrets
- payment or billing screenshots
- personal account identifiers
- local machine secrets
- real enterprise credentials
- private tokens
- screenshots that expose unrelated personal information

Sanitize terminal screenshots before adding them to a public portfolio if they contain sensitive paths, tokens, or account information.

## Portfolio Claim Supported by the Evidence

A defensible summary of the project is:

> Designed and validated an AI Agent Security Control Plane that keeps authorization outside the LLM, enforces MCP tool access through signed workload identity and OPA/Rego policy-as-code, applies human and four-eyes approval controls for sensitive and critical actions, generates security telemetry, correlates malicious behavior, adapts authorization based on runtime risk, and automatically quarantines compromised agents. Validated through 85 automated regression/adversarial tests and a final integrated compromised-agent scenario.

## Evidence Status

Core engineering evidence: **COMPLETE**

Automated regression evidence: **85 tests passing**

Integrated attack evidence: **PASS**

Architecture documentation: **COMPLETE**

Threat model: **COMPLETE**

Screenshot curation: **IN PROGRESS**

Portfolio presentation: **NEXT**
