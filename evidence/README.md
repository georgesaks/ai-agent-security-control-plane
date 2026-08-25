# Evidence Package

This directory is for a small, curated set of portfolio-ready screenshots and supporting evidence from the AI Agent Security Control Plane project.

Do not add every development screenshot. The goal is to make the evidence easy to review quickly.

## Recommended Files

Use the following names when adding screenshots:

```text
S01-85-tests-passing.png
S02-opa-version.png
S03-opa-read-only-decision.png
S04-opa-sensitive-or-critical-classification.png
S05-four-eyes-approval-milestone.png
S06-final-integrated-adversarial-pass.png
```

## Required Content

### S01: 85 Tests Passing

The screenshot should clearly show:

```text
Ran 85 tests
OK
```

Purpose: proves the final regression and adversarial test suite passes.

### S02: OPA Version

The screenshot should show `opa version`, including the OPA version, Windows platform, and Rego version.

Purpose: proves the real OPA CLI used during policy validation.

### S03: READ_ONLY Rego Decision

The screenshot should show a manual OPA evaluation returning:

```text
"allowed": true
"classification": "READ_ONLY"
"reason": "policy requirements satisfied"
```

Purpose: proves Rego is making a real authorization decision.

### S04: SENSITIVE or CRITICAL Classification

The screenshot should show either:

```text
"classification": "SENSITIVE"
```

or:

```text
"classification": "CRITICAL"
```

Purpose: proves the approval workflow is selected from policy classification.

### S05: Four-Eyes Approval Milestone

Use either the dual-approval test output or the regression milestone where the four-eyes gateway controls were confirmed.

Purpose: demonstrates that critical operations require two distinct authorized reviewers.

### S06: Final Integrated Adversarial PASS

This is the most important screenshot.

It should visibly include as much of the following as possible:

```text
GATEWAY: DENY
DETECTIONS: AI-001, AI-002
ADAPTIVE RISK: 90 / CRITICAL
AI-003
CONTAINMENT: QUARANTINED
RESULT: DENY
FINAL RESULT: PASS
```

Purpose: proves the complete control plane works as one integrated security system.

## Screenshot Quality Guidance

Keep terminal text readable. Crop out unrelated applications, notifications, personal browser tabs, and other distractions. Do not over-crop away the command prompt or enough context to understand what was executed.

For terminal screenshots, a width around 1400 to 1800 pixels is usually enough for readable GitHub display without excessive file size.

## Security Review Before Commit

Before adding any screenshot, verify that it does not contain:

- OpenAI API keys
- signing secrets
- access tokens
- billing or payment information
- email addresses that do not need to be public
- unrelated personal data
- private enterprise repository names or credentials
- sensitive local files or environment-variable values

A local Windows username or repository folder path is generally low risk, but it can be cropped if it adds no value.

## Portfolio Use

The preferred order when presenting screenshots is:

```text
Architecture / problem statement
        ↓
OPA policy decision
        ↓
Four-eyes control
        ↓
85-test validation
        ↓
Final integrated adversarial PASS
```

The final integrated screenshot should be the strongest visual proof and should normally appear in the README or portfolio case study.

For the complete evidence map, see:

```text
docs/evidence-catalog.md
```
