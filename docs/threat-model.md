# AI Agent Security Control Plane Threat Model

## Scope

This threat model covers the security boundary between an AI agent and enterprise-style tools exposed through the prototype MCP security gateway.

The primary assumption is deliberately pessimistic:

> The LLM may be manipulated, prompt-injected, compromised, or simply make an unsafe decision.

The control plane therefore does not rely on model alignment or prompt instructions as the final authorization mechanism.

## Protected Assets

The architecture is designed to protect:

- privileged tool execution
- production environments
- repository and configuration integrity
- trusted agent identity and role claims
- human approval authority
- authorization policy integrity
- audit evidence
- containment state
- enterprise credentials that a production tool connector would hold

## Actors

### Legitimate AI Agent

An agent operating with a valid signed identity and expected role.

### Compromised AI Agent

A valid agent whose model behavior has been manipulated or compromised. This is the central adversarial assumption used in the final integrated test.

### Malicious Caller

A caller attempting to forge identity, escalate role, request an unregistered tool, tamper with an approved action, or replay authorization.

### Authorized Reviewer

A human identity permitted to approve sensitive or critical actions. Reviewers must remain independent from the requesting actor.

### Security Operator

A defender or automated response process able to act on detections and quarantine an actor.

## Trust Boundaries

```text
Untrusted / Semi-trusted                    Trusted Security Controls

LLM / Agent Intent
       |
       | TB1
       v
Signed Identity Verification
       |
       | TB2
       v
MCP Security Gateway
       |
       | TB3
       +--------> OPA / Rego PDP
       |
       | TB4
       +--------> Human Approval
       |
       | TB5
       v
Approved Tool Registry / Tool Handler
       |
       | TB6
       v
Audit / Detection / Risk / Containment
```

## Threats and Mitigations

| ID | Threat | Attack Example | Primary Mitigation | Validated Result |
|---|---|---|---|---|
| T01 | Prompt injection | Untrusted content influences the model to request an unsafe action | Authorization remains outside the model | External controls remain authoritative |
| T02 | Compromised model | Model intentionally requests privileged production actions | Gateway + OPA + risk + containment | Production action denied |
| T03 | Identity tampering | Modify actor or role after token issuance | HMAC signature verification | Tampered identity rejected |
| T04 | Expired identity replay | Reuse an old signed identity | Token expiration validation | Expired identity rejected |
| T05 | Role escalation | Auditor attempts developer/write capability | OPA role permissions | Denied |
| T06 | Unknown tool execution | Request attacker-supplied tool name | Explicit tool registry | Denied before handler execution |
| T07 | Unknown classification | Tool exists without security classification | OPA default deny | Denied |
| T08 | Production write | Developer requests sensitive/critical production action | Environment-aware Rego policy | Denied before approval creation |
| T09 | Policy engine outage | OPA executable unavailable | Fail-closed OPA adapter | Denied |
| T10 | Broken policy | Invalid Rego policy | Fail-closed OPA adapter | Denied |
| T11 | Malformed PDP response | OPA returns unexpected response shape | Response validation | Denied |
| T12 | Approval bypass | Sensitive action submitted without approval | Gateway approval enforcement | Held / denied |
| T13 | Approval tampering | Change arguments after human approval | SHA-256 argument binding | Denied |
| T14 | Approval replay | Reuse consumed approval | Single-use consumption | Denied |
| T15 | Stale approval | Execute after approval TTL | Expiration check | Denied |
| T16 | Unauthorized reviewer | Fabricated/non-authorized reviewer approves | Reviewer allowlist | Denied |
| T17 | Self approval | Requesting actor approves own action | Separation of duties | Denied |
| T18 | Four-eyes bypass | Critical action receives only one approval | Dual-control workflow | Denied |
| T19 | Duplicate reviewer | Same reviewer attempts both critical approvals | Distinct reviewer enforcement | Denied |
| T20 | Post-approval mutation | Critical action changed after two approvals | Action digest binding | Denied |
| T21 | Repeated malicious behavior | Compromised agent repeatedly requests forbidden writes | Detection correlation + adaptive risk | AI-003 + CRITICAL risk |
| T22 | Continued access after compromise | Agent attempts safe-looking action after malicious sequence | Quarantine checked first by gateway | Denied |
| T23 | Audit repudiation | Caller disputes why an action was blocked/allowed | Structured audit event with actor, context, decision, reason | Evidence generated |

## STRIDE View

### Spoofing

Threats:

- forged actor identity
- forged role
- fabricated reviewer

Controls:

- signed identity claims
- signature verification
- short-lived identity token
- reviewer allowlist
- requester/reviewer separation

### Tampering

Threats:

- modify identity claims
- alter tool arguments after approval
- change a critical action after dual approval
- manipulate policy output

Controls:

- signed identity payload
- SHA-256 action binding
- validated OPA response shape
- fail-closed policy behavior

### Repudiation

Threats:

- agent or operator cannot explain why an action executed or was blocked

Controls:

- structured audit telemetry
- explicit decision reasons
- actor, role, environment, tool, timestamp, and decision recorded

### Information Disclosure

Threats:

- unauthorized tool access could expose repository or enterprise data
- unregistered tool could bypass intended access controls

Controls:

- least privilege role policy
- explicit tool registry
- default deny
- quarantine

This prototype focuses more heavily on authorization and integrity than data-loss prevention. Production extensions should add data classification, output filtering, and egress controls.

### Denial of Service

Threats:

- repeated malicious requests consume policy, approval, or tool resources
- policy service failure disrupts authorization

Controls:

- adaptive behavioral risk
- repeated-denial correlation
- quarantine
- bounded OPA evaluation timeout
- fail-closed policy behavior

Production extensions should add rate limiting, circuit breaking, capacity controls, and HA for the policy decision point.

### Elevation of Privilege

Threats:

- auditor attempts developer action
- developer attempts prohibited production write
- critical action bypasses four-eyes approval
- high-risk actor retains write access

Controls:

- OPA role/environment policy
- sensitivity classification
- adaptive-risk restrictions
- single and dual approval boundaries
- containment state checked before policy execution

## Abuse Cases

### Abuse Case A: Prompt Injection Leads to Unsafe Tool Intent

1. Agent consumes attacker-controlled content.
2. Model decides to request a privileged action.
3. Security objective: the model's decision must not be sufficient to execute the action.
4. Gateway evaluates trusted context and OPA policy.
5. Unauthorized action is denied and audited.

### Abuse Case B: Valid Agent Becomes Compromised

1. Agent still has a valid identity.
2. Agent repeatedly requests production writes.
3. OPA denies each request.
4. Audit events trigger `AI-001` and `AI-002`.
5. Risk escalates from MEDIUM to HIGH to CRITICAL.
6. Repeated denials correlate into `AI-003`.
7. Actor is quarantined.
8. Subsequent normally allowed read access is denied.

This is the final integrated adversarial scenario validated by the project.

### Abuse Case C: Human Approval Is Treated as a Reusable Token

1. Sensitive action receives legitimate approval.
2. Caller modifies the action or attempts to replay the approval.
3. Action digest, TTL, and consumption state are validated.
4. Modified, expired, or replayed approval is denied.

### Abuse Case D: Critical Action Uses Colluding or Duplicate Approval Identity

1. Critical action requires two reviewers.
2. Same reviewer attempts to approve twice, or requester attempts to participate.
3. Distinct-reviewer and separation-of-duties checks fail.
4. Tool handler remains unreachable.

## Security Invariants

The project is designed around the following invariants:

1. The LLM cannot authorize itself.
2. Caller-supplied role data is not trusted without identity verification.
3. Unknown tools do not execute.
4. Unknown classifications do not execute.
5. OPA failure never becomes implicit allow.
6. Sensitive actions cannot execute without valid independent approval.
7. Critical actions cannot execute without two distinct authorized reviewers.
8. Approval cannot authorize different arguments than those reviewed.
9. Approval cannot be reused indefinitely.
10. Quarantine overrides otherwise-valid authorization.
11. Security decisions produce audit evidence.
12. Repeated malicious behavior can change future authorization through adaptive risk and containment.

## Residual Risk and Prototype Limitations

The prototype intentionally leaves several production concerns outside the core scope:

- identity uses a local shared HMAC secret rather than external workload identity
- approval and containment state are in-memory
- reviewer authorization is a local allowlist
- OPA is invoked locally rather than deployed as an HA policy service
- audit events are not shipped to a production SIEM
- tool connectors are limited prototypes rather than full enterprise integrations
- no dedicated data-loss prevention or semantic output inspection layer
- no distributed rate limiting
- no durable policy signing/version attestation workflow

These are implementation limitations rather than changes to the core security model.

## Final Threat-Model Conclusion

The project assumes the model can fail. The primary defense is therefore not a stronger prompt. The defense is an external security control plane that independently verifies identity, evaluates policy, requires human authorization where appropriate, restricts risky actors, records evidence, detects repeated abuse, and revokes access through containment.