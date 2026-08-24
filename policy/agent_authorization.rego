package agent.authz

# Default deny: an action is only allowed when an explicit rule matches.
default allow := false

# Developers can read the approved repository summary in any environment.
allow if {
  input.role == "developer"
  input.tool_name == "read_repository_summary"
}

# Developers can create an issue draft only outside production.
allow if {
  input.role == "developer"
  input.tool_name == "create_issue_draft"
  input.environment != "production"
}

# Auditors are read-only in this prototype.
allow if {
  input.role == "auditor"
  input.tool_name == "read_repository_summary"
}

reason := "policy requirements satisfied" if allow

reason := sprintf("role '%s' is not allowed to use '%s' in environment '%s'", [
  input.role,
  input.tool_name,
  input.environment,
]) if not allow
