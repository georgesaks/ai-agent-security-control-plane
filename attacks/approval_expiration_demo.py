"""Demonstrate time-bounded human approval and stale-approval denial."""

from datetime import datetime, timedelta, timezone

from approval.workflow import clear_approvals, consume_approval, create_approval_request, review_approval


BASE = datetime(2026, 8, 24, 22, 0, tzinfo=timezone.utc)
ACTION = dict(
    actor="llm-agent-jit-approval-lab",
    role="developer",
    environment="development",
    tool_name="create_issue_draft",
    arguments={"title": "Time-bounded change", "body": "Reviewed exact content"},
)


def main():
    clear_approvals()
    print("TIME-BOUNDED APPROVAL ATTACK TESTS")
    print("DEFAULT ENTERPRISE PROTOTYPE TTL: 300 seconds")
    print()

    fresh = create_approval_request(**ACTION, ttl_seconds=300, now=BASE)
    review_approval(fresh.request_id, reviewer="security-reviewer-saki", approve=True,
                    now=BASE + timedelta(seconds=10))
    allowed, detail = consume_approval(fresh.request_id, **ACTION,
                                       now=BASE + timedelta(seconds=60))
    print(f"FRESH APPROVAL (60s): {'ALLOW' if allowed else 'DENY'}")
    print(f"DETAIL: {detail}")
    print()

    stale = create_approval_request(**ACTION, ttl_seconds=300, now=BASE)
    review_approval(stale.request_id, reviewer="security-reviewer-saki", approve=True,
                    now=BASE + timedelta(seconds=10))
    allowed, detail = consume_approval(stale.request_id, **ACTION,
                                       now=BASE + timedelta(seconds=301))
    print(f"STALE APPROVAL (301s): {'ALLOW' if allowed else 'DENY'}")
    print(f"DETAIL: {detail}")
    print()

    allowed, detail = consume_approval(stale.request_id, **ACTION,
                                       now=BASE + timedelta(seconds=302))
    print(f"EXPIRED APPROVAL RETRY: {'ALLOW' if allowed else 'DENY'}")
    print(f"DETAIL: {detail}")
    print()

    pending = create_approval_request(**ACTION, ttl_seconds=300, now=BASE)
    try:
        review_approval(pending.request_id, reviewer="security-reviewer-saki", approve=True,
                        now=BASE + timedelta(seconds=301))
        print("LATE HUMAN REVIEW: ALLOW")
    except ValueError as exc:
        print("LATE HUMAN REVIEW: DENY")
        print(f"DETAIL: {exc}")


if __name__ == "__main__":
    main()
