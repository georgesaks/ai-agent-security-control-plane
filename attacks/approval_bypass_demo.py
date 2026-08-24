"""Negative-path tests against the human approval boundary."""

from approval.workflow import (
    clear_approvals,
    consume_approval,
    create_approval_request,
    review_approval,
)


ACTOR = "llm-agent-approval-attack-lab"
ROLE = "developer"
ENVIRONMENT = "development"
TOOL = "create_issue_draft"
ORIGINAL = {"title": "Approved change", "body": "Reviewed content"}
MODIFIED = {"title": "Approved change", "body": "UNREVIEWED modified content"}


def check(label: str, allowed: bool, detail: str) -> None:
    print(f"{label}: {'ALLOW' if allowed else 'DENY'}")
    print(f"DETAIL: {detail}")
    print()


def main() -> None:
    clear_approvals()
    print("APPROVAL BOUNDARY NEGATIVE-PATH TESTS")
    print()

    # 1. Fabricated / nonexistent approval identifier.
    allowed, detail = consume_approval(
        "apr_fabricated",
        actor=ACTOR,
        role=ROLE,
        environment=ENVIRONMENT,
        tool_name=TOOL,
        arguments=ORIGINAL,
    )
    check("NO VALID APPROVAL", allowed, detail)

    # 2. Human explicitly rejects the requested action.
    rejected = create_approval_request(
        actor=ACTOR, role=ROLE, environment=ENVIRONMENT,
        tool_name=TOOL, arguments=ORIGINAL,
    )
    review_approval(rejected.request_id, reviewer="security-reviewer-saki", approve=False)
    allowed, detail = consume_approval(
        rejected.request_id,
        actor=ACTOR, role=ROLE, environment=ENVIRONMENT,
        tool_name=TOOL, arguments=ORIGINAL,
    )
    check("REJECTED APPROVAL", allowed, detail)

    # 3. Human approves exact content, then agent changes the arguments.
    approved = create_approval_request(
        actor=ACTOR, role=ROLE, environment=ENVIRONMENT,
        tool_name=TOOL, arguments=ORIGINAL,
    )
    review_approval(approved.request_id, reviewer="security-reviewer-saki", approve=True)
    allowed, detail = consume_approval(
        approved.request_id,
        actor=ACTOR, role=ROLE, environment=ENVIRONMENT,
        tool_name=TOOL, arguments=MODIFIED,
    )
    check("MODIFIED ACTION AFTER APPROVAL", allowed, detail)

    # The mismatch must not consume the legitimate approval. The exact action
    # reviewed by the human can still be presented and consumed once.
    allowed, detail = consume_approval(
        approved.request_id,
        actor=ACTOR, role=ROLE, environment=ENVIRONMENT,
        tool_name=TOOL, arguments=ORIGINAL,
    )
    check("EXACT APPROVED ACTION", allowed, detail)

    # 4. Replay the now-consumed approval.
    allowed, detail = consume_approval(
        approved.request_id,
        actor=ACTOR, role=ROLE, environment=ENVIRONMENT,
        tool_name=TOOL, arguments=ORIGINAL,
    )
    check("CONSUMED APPROVAL REPLAY", allowed, detail)


if __name__ == "__main__":
    main()
