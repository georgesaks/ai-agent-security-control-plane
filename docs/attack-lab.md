# Phase 2 Attack Lab

## Purpose

I added this attack lab to test whether the control plane behaves the way I expect when an agent or caller attempts to cross a security boundary. The scenarios are intentionally local and do not target real infrastructure, credentials, repositories, or production systems.

The goal is not just to show that controls exist. I want to verify that the controls fail safely when the inputs are hostile or untrusted.

## Scenario 1: Identity spoofing

**Attempt:** Modify a signed identity token after it has been issued.

**Expected result:** The signature no longer matches the claims and identity verification fails before authorization is evaluated.

**Control being tested:** Signed identity claims and fail-closed verification.

## Scenario 2: Privilege escalation

**Attempt:** An agent whose verified role is `auditor` tries to invoke the write-oriented `create_issue_draft` tool.

**Expected result:** The verified role is passed to the authorization layer and the request is denied. The caller cannot replace the trusted role with a self-asserted developer or administrator role.

**Control being tested:** Separation of authentication from authorization and use of trusted identity attributes.

## Scenario 3: Unregistered MCP tool

**Attempt:** A developer agent requests a tool named `read_secrets` that is not registered with the MCP security gateway.

**Expected result:** Default deny. The request is rejected before any tool implementation can execute.

**Control being tested:** Explicit tool registration and default-deny dispatch.

## Scenario 4: Production write attempt

**Attempt:** A verified developer agent tries to invoke `create_issue_draft` while the target environment is production.

**Expected result:** The request is denied by environment-aware authorization policy.

**Control being tested:** Context-aware authorization.

## What I learned

A tool allowlist by itself is not enough. The control plane also needs to know who is requesting the action, whether those identity claims can be trusted, what environment is being targeted, and whether the requested operation is appropriate in that context.

The next attack class I want to explore is different: prompt injection. Instead of directly forging identity or requesting a forbidden tool, the attacker will try to influence the model into choosing an unsafe action. The security objective will be to show that model behavior can change while the external authorization boundary still holds.
