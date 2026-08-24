package agent.authz

import rego.v1

test_developer_can_read_repository if {
  allow with input as {
    "actor": "agent-001",
    "role": "developer",
    "environment": "development",
    "tool_name": "read_repository_summary",
  }
}

test_developer_can_create_issue_draft_in_development if {
  allow with input as {
    "actor": "agent-001",
    "role": "developer",
    "environment": "development",
    "tool_name": "create_issue_draft",
  }
}

test_developer_cannot_create_issue_draft_in_production if {
  not allow with input as {
    "actor": "agent-001",
    "role": "developer",
    "environment": "production",
    "tool_name": "create_issue_draft",
  }
}

test_auditor_is_read_only if {
  allow with input as {
    "actor": "agent-002",
    "role": "auditor",
    "environment": "development",
    "tool_name": "read_repository_summary",
  }

  not allow with input as {
    "actor": "agent-002",
    "role": "auditor",
    "environment": "development",
    "tool_name": "create_issue_draft",
  }
}

test_unknown_role_is_denied_by_default if {
  not allow with input as {
    "actor": "agent-003",
    "role": "unknown-role",
    "environment": "development",
    "tool_name": "read_repository_summary",
  }
}
