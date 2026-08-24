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

Introduced human-in-the-loop authorization boundaries for sensitive and critical AI-agent operations that should not execute autonomously.

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
- Time-bounded approvals introduced with a default 300-second TTL
- Fresh approval remains valid inside the approved time window
- Approved but stale requests are denied after expiration
- Expired approval retries remain denied
- Pending approval requests cannot be approved after expiration
- Sensitive approvals restricted to an explicit authorized-reviewer set
- Unauthorized and fabricated reviewers are denied
- Requesters cannot approve their own sensitive actions
- Failed unauthorized review attempts do not destroy legitimate pending requests
- Authorized security reviewer can approve and execute the exact reviewed action
- Dual-control approval primitive introduced for highest-impact actions
- One reviewer is insufficient for critical action execution
- Same reviewer cannot satisfy both approval slots
- Unauthorized second reviewer is denied
- Requester cannot participate as a reviewer for its own critical action
- Critical approval remains bound to the exact action and is time-bounded and single-use
- Two distinct authorized reviewers successfully satisfy four-eyes authorization
- `critical_configuration_change` classified as an authorized developer capability subject to critical controls
- MCP gateway now returns `REQUIRE_DUAL_APPROVAL` before critical execution
- MCP gateway denies critical execution after only one approval
- MCP gateway executes the exact critical action only after two distinct authorized approvals
- MCP gateway denies post-approval argument tampering
- MCP gateway denies replay after successful critical execution
- Regression suite increased to 57 passing automated security tests

Validated approval flow:

```text
Sensitive action
      |
      v
REQUIRE_APPROVAL
      |
Authorized independent reviewer
      |
Exact action + valid TTL + unused
      |
      v
    ALLOW

Critical action
      |
      v
MCP Security Gateway
      |
      v
REQUIRE_DUAL_APPROVAL
      |
      +--> Reviewer A authorized and independent?
      |
      +--> Reviewer B authorized and independent?
      |
      +--> Reviewer A != Reviewer B?
      |
      +--> Exact action match?
      |
      +--> Approval still fresh and unused?
      |
      v
    EXECUTE
      |
      v
Consume authorization
      |
      +--> Replay -> DENY
```

Approval attack validation:

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
16. Time-bounded approval validation shows a fresh approval allowed at 60 seconds
17. Stale approval denied after 301 seconds with an explicit expiration reason
18. Expired approval retry and late human review both denied
19. Regression suite reaching 39 passing security tests after approval-expiration controls
20. Reviewer authorization attack suite blocks unauthorized and fabricated reviewers
21. Separation-of-duties test blocks requester self-approval
22. Authorized security reviewer successfully approves the reviewed action
23. Regression suite reaches 44 passing security tests after reviewer-authorization controls
24. Dual-approval attack suite validates one-reviewer, duplicate-reviewer, unauthorized-reviewer, tampering, and replay denial paths
25. Two distinct authorized reviewers satisfy the isolated four-eyes approval primitive
26. Regression suite reaches 52 passing tests after dual-approval primitive validation
27. Critical action integrated into the real MCP security gateway with `REQUIRE_DUAL_APPROVAL`
28. Gateway blocks execution with only one reviewer and after action tampering
29. Gateway executes only after two distinct authorized reviewers and consumes the authorization
30. Regression suite reaches 57 passing tests after four-eyes gateway integration

Sensitive information such as API keys, signing secrets, payment information, and account identifiers is intentionally excluded from project evidence.

## Current Learning

A recurring design principle from the experiments so far is that model behavior alone is not a sufficient security boundary. Prompt-injection resistance is useful, but authorization, identity verification, telemetry, detection, containment, adaptive risk, and approval controls need to exist outside the model so that a manipulated or compromised agent cannot directly convert intent into privileged action.

The approval experiments add another principle: human approval should not be treated as a reusable boolean. Authorization needs to be bound to the exact action that was reviewed, consumed after execution, limited in time, and granted only by authorized reviewers who are independent of the requester. For critical operations, the gateway now requires two distinct authorized reviewers before the tool handler is reachable. The negative-path, expiration, reviewer-authorization, dual-control, and gateway-integration tests demonstrate fail-closed behavior across missing, rejected, altered, replayed, stale, self-approved, partially approved, and unauthorized approval states.

## Next Milestone

Move approval requirements out of hard-coded gateway conditions into a centralized policy classification model so the policy layer can determine whether an action is READ_ONLY, SENSITIVE, or CRITICAL and the gateway can enforce the corresponding authorization workflow consistently. This prepares the project for a later transition to an external policy engine such as OPA/Rego.
