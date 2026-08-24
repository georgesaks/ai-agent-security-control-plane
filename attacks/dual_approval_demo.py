"""Attack the four-eyes dual-approval boundary for critical agent actions."""

from approval.dual_workflow import (
    approve_dual_request,
    clear_dual_approvals,
    consume_dual_approval,
    create_dual_approval_request,
)


ACTION = dict(
    actor="llm-agent-critical-lab",
    role="developer",
    environment="development",
    tool_name="critical_configuration_change",
    arguments={"target": "security-control", "mode": "enforced"},
)


def request():
    return create_dual_approval_request(**ACTION)


def main():
    clear_dual_approvals()
    print("DUAL APPROVAL / FOUR-EYES ATTACK TESTS")
    print()

    req = request()
    approve_dual_request(req.request_id, reviewer="security-reviewer-primary")
    allowed, detail = consume_dual_approval(req.request_id, **ACTION)
    print(f"ONE REVIEWER ONLY: {'ALLOW' if allowed else 'DENY'}")
    print(f"DETAIL: {detail}\n")

    req = request()
    approve_dual_request(req.request_id, reviewer="security-reviewer-primary")
    try:
        approve_dual_request(req.request_id, reviewer="security-reviewer-primary")
        print("SAME REVIEWER TWICE: ALLOW")
    except PermissionError as exc:
        print("SAME REVIEWER TWICE: DENY")
        print(f"DETAIL: {exc}\n")

    req = request()
    approve_dual_request(req.request_id, reviewer="security-reviewer-primary")
    try:
        approve_dual_request(req.request_id, reviewer="random-developer")
        print("UNAUTHORIZED SECOND REVIEWER: ALLOW")
    except PermissionError as exc:
        print("UNAUTHORIZED SECOND REVIEWER: DENY")
        print(f"DETAIL: {exc}\n")

    req = request()
    approve_dual_request(req.request_id, reviewer="security-reviewer-primary")
    approve_dual_request(req.request_id, reviewer="security-reviewer-secondary")
    changed = dict(ACTION)
    changed["arguments"] = {"target": "security-control", "mode": "disabled"}
    allowed, detail = consume_dual_approval(req.request_id, **changed)
    print(f"ACTION TAMPERING AFTER TWO APPROVALS: {'ALLOW' if allowed else 'DENY'}")
    print(f"DETAIL: {detail}\n")

    req = request()
    approve_dual_request(req.request_id, reviewer="security-reviewer-primary")
    approve_dual_request(req.request_id, reviewer="security-reviewer-secondary")
    allowed, detail = consume_dual_approval(req.request_id, **ACTION)
    print(f"TWO DISTINCT AUTHORIZED REVIEWERS: {'ALLOW' if allowed else 'DENY'}")
    print(f"DETAIL: {detail}")
    replay, replay_detail = consume_dual_approval(req.request_id, **ACTION)
    print(f"POST-EXECUTION REPLAY: {'ALLOW' if replay else 'DENY'}")
    print(f"DETAIL: {replay_detail}")


if __name__ == "__main__":
    main()
