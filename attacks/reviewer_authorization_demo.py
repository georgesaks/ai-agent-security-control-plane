"""Attack the reviewer authorization and separation-of-duties boundary."""

from approval.workflow import clear_approvals, consume_approval, create_approval_request, review_approval


ACTION = dict(
    actor="llm-agent-reviewer-lab",
    role="developer",
    environment="development",
    tool_name="create_issue_draft",
    arguments={"title": "Sensitive action", "body": "Reviewed content"},
)


def attempt(label, reviewer, action=None):
    selected = action or ACTION
    req = create_approval_request(**selected)
    try:
        review_approval(req.request_id, reviewer=reviewer, approve=True)
        allowed, detail = consume_approval(req.request_id, **selected)
        print(f"{label}: {'ALLOW' if allowed else 'DENY'}")
        print(f"DETAIL: {detail}")
    except PermissionError as exc:
        print(f"{label}: DENY")
        print(f"DETAIL: {exc}")
    print()


def main():
    clear_approvals()
    print("REVIEWER AUTHORIZATION / SEPARATION-OF-DUTIES ATTACK TESTS")
    print()

    attempt("UNAUTHORIZED REVIEWER", "random-developer")
    attempt("FABRICATED REVIEWER", "security-reviewer-fake")

    self_action = dict(ACTION)
    self_action["actor"] = "security-reviewer-saki"
    attempt("SELF APPROVAL", "security-reviewer-saki", self_action)

    attempt("AUTHORIZED SECURITY REVIEWER", "security-reviewer-saki")


if __name__ == "__main__":
    main()
