# Agent Guardrail Rule: Autonomous Agent Execution Boundaries

- **Tool Call Wrapping**: Autonomous subagents and automation tools MUST execute commands through `mise` task wrappers (`mise run <task>`).
- **State Audit**: Agents MUST run `/verify-state` or `python3 .gemini/hooks/verify_environment.py` before completing turns to guarantee environment cleanliness.
- **No Swallowed Errors**: System or command execution errors must be diagnosed empirically without silent fallback masking.
