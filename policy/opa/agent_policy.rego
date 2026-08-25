package aiagent.authz

# OPA/Rego is the primary authorization decision source for the MCP gateway.
# The policy returns both an allow/deny decision and the action classification
# used by the gateway to select the appropriate runtime control.

default decision := {
  "allowed": false,
  "reason": "denied by default",
  "classification": "UNKNOWN"
}

role_permissions := {
  "developer": {
    "read_repository_summary",
    "create_issue_draft",
    "critical_configuration_change",
  },
  "auditor": {
    "read_repository_summary",
  },
}

classifications := {
  "read_repository_summary": "READ_ONLY",
  "create_issue_draft": "SENSITIVE",
  "critical_configuration_change": "CRITICAL",
}

classification := object.get(classifications, input.tool_name, "UNKNOWN")

role_allowed if {
  input.tool_name in role_permissions[input.role]
}

production_blocked if {
  input.environment == "production"
  classification in {"SENSITIVE", "CRITICAL"}
}

decision := {
  "allowed": false,
  "reason": sprintf("role '%s' is not allowed to use '%s'", [input.role, input.tool_name]),
  "classification": classification,
} if {
  not role_allowed
}

decision := {
  "allowed": false,
  "reason": "tool has no security classification and is denied by default",
  "classification": "UNKNOWN",
} if {
  role_allowed
  classification == "UNKNOWN"
}

decision := {
  "allowed": false,
  "reason": "write-oriented actions are blocked in production in this prototype",
  "classification": classification,
} if {
  role_allowed
  classification != "UNKNOWN"
  production_blocked
}

decision := {
  "allowed": true,
  "reason": "policy requirements satisfied",
  "classification": classification,
} if {
  role_allowed
  classification != "UNKNOWN"
  not production_blocked
}
