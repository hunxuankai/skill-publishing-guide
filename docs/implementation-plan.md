# Skill Publishing Guide Implementation Plan

**Goal:** Create, validate and locally install an independently maintained skill-publishing-guide 1.0.0.

**Spec:** [Design](design.md)

**Execution:** Author the coupled guide and maintenance package in one isolated development worktree. Independent agents may verify public sources, perform controlled usage evaluations and review the completed change. They do not publish or mutate reference repositories.

## Stages

- [x] Preserve a controlled baseline using a multi-skill fixture, recorded responses and an explicit prepare-only task. Save actual artifacts and decisions before authoring the new entrypoint.
- [x] Refresh decisive primary-source facts for the named platforms. Store retrieval evidence outside the installable package, and record dates/limits in the guide.
- [x] Write `SKILL.md`, `agents/openai.yaml`, platform references, packaging guidance, a result-record template and source/maintenance notes. Keep each reference self-contained within the package and avoid unsupported universal rules.
- [x] Adapt the reviewed `tools/check_skill.py` and `tools/install-local.ps1` from software-testing-router, preserving their safeguards. Add pinned maintenance/test dependencies and human README/maintenance instructions.
- [x] Run meaningful temporary-directory checks for the new package name, preview, complete copy, no-op and backup/extra-file behavior. Use the existing reviewed implementation rather than adding a second parser or upload engine.
- [x] Have a fresh agent use the completed skill on the controlled cases, inspect actual output ZIPs and status records, and address demonstrated gaps. Retain baseline and candidate evidence separately.
- [x] Perform independent review and relevant checks. Commit, install the validated source locally, and verify every installed file hash.
- [x] Merge into `main`, validate the local v1.0.0 ZIP/tag/sidecars against committed bytes, archive evidence and remove the clean fully merged development worktree/branch.

## Expected maintenance commands

```powershell
python tools/check_skill.py
pwsh -NoProfile -File tools/install-local.ps1 -Python python -DryRun
pwsh -NoProfile -File tools/install-local.ps1 -Python python
python -m pytest tests -q
git diff --check
```

The controller selects the prepared maintenance interpreter explicitly when the shell's default Python lacks these dependencies. All test users, backup paths, publishing receipts and remote identifiers are controlled fixtures; no live submission is an evaluation prerequisite.
