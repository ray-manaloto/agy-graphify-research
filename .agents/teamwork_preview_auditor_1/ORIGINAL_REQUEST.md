## 2026-07-30T19:09:25Z
<USER_REQUEST>
You are a teamwork_preview_auditor (Forensic Integrity Auditor) for agy-graphify-research.
Your task is to perform a rigorous forensic integrity audit of the agy-graphify-research codebase and verification results to detect any cheating, hardcoded test outputs, facade/mock implementations, prohibited shell scripts (*.sh), or artificial assertions.

Working Directory: /Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_auditor_1
Codebase Directory: /Users/rmanaloto/agy-graphify-research

Forensic Integrity Audit Instructions:
1. Initialize your working directory with ORIGINAL_REQUEST.md, BRIEFING.md, and progress.md.
2. Examine source code (`src/agy_graphify/*.py`), tests (`tests/*.py`), and configuration files (`.mise.toml`, `pyproject.toml`, `hk.pkl`, `.gemini/plugins/orchestration_plugin/plugin.json`).
3. Check for integrity violations:
   a. Hardcoded test results, expected outputs, or artificial success signals.
   b. Dummy or facade implementations that return pre-cooked JSON without real logic.
   c. Fabrication of verification outputs, logs, or attestation artifacts.
   d. Prohibited shell scripts (*.sh files outside vendor directories).
   e. Circumvention of core logic via external mocks or prohibited tools.
4. Perform dynamic runtime checks by executing the verification suite to ensure code actually executes genuine logic during testing.
5. Produce a binary verdict: CLEAN or INTEGRITY VIOLATION.
6. Write `forensic_audit_report.md` in your working directory detailing all static and dynamic audit findings, evidence chains, and your binary verdict.
7. Write `handoff.md` in your working directory following the Handoff Protocol.
8. Send a message back to the orchestrator parent with your forensic verdict and summary evidence.
</USER_REQUEST>
