---
name: ci
description: CI/CD pipeline decision tree — Azure DevOps vs GitHub Actions vs GitLab CI — with trade-offs and when to use each. Routes to the implementation sub-skill for the chosen platform. Load after dev-guidelines.
license: MIT
compatibility: claude-code
metadata:
  audience: developers
  workflow: ci-cd
---

## What I do

I help choose the right CI/CD platform and route to its implementation conventions. I cover the decision, not the implementation — the platform-specific skill covers YAML conventions, stage structure, and integration patterns.

## When to use me

Load when setting up CI/CD for a new project, or when migrating pipelines between platforms.

---

## Platform Decision Tree

```
Where does your source code live?
├── Azure DevOps Repos → Azure DevOps Pipelines  ← natural choice
│   └── Or if already on AzDO for other services → stay consistent
├── GitHub → GitHub Actions  ← natural choice
│   └── Public/OSS repo? → GitHub Actions (free minutes)
├── GitLab → GitLab CI/CD  ← natural choice
└── Mixed / migrating?
    ├── Team already standardized on AzDO → Azure DevOps Pipelines
    ├── Moving to GitHub → GitHub Actions
    └── Enterprise with Azure investment → Azure DevOps
```

**Trade-offs:**

| Platform | Best for | Watch out for |
|---|---|---|
| **Azure DevOps** | Enterprise, Azure ecosystem, Windows builds, private agent pools, variable groups, Environments with approvals | More YAML verbosity; YAML templates can get complex; UI is less polished than GitHub |
| **GitHub Actions** | OSS projects, GitHub-hosted repos, marketplace actions, simpler YAML | Limited artifact storage; secrets management less powerful than AzDO variable groups; no built-in environments with approvals in free tier |
| **GitLab CI/CD** | GitLab repos, Docker-native builds, self-hosted runners, merge request pipelines | Tight GitLab coupling; DAG syntax different from others |

---

## Core Principles (platform-agnostic)

These apply regardless of which platform you choose:

**Local = CI**: Pipeline steps must invoke the same commands developers run locally.
```yaml
# ✅ Correct — invokes local Taskfile
- script: task test:backend

# ❌ Wrong — reimplements what the Taskfile defines
- script: |
    cd backend && pytest tests/ --cov=src
```
If a pipeline step needs something not covered by a Taskfile task, **add the task first**.

**Fail fast**: run quality checks and unit tests before integration tests, build, or deploy.

**Stage order** (standard):
```
Quality (lint, type-check, security) → Unit Tests → Integration Tests → Build → Deploy
```

**Secrets**: never store secrets in pipeline YAML. Use the platform's secrets management:
- Azure DevOps: variable groups + Key Vault-linked variables
- GitHub Actions: repository/org secrets + OIDC for cloud auth
- GitLab CI: CI/CD variables (masked + protected)

**Pin versions**: pin all tool versions and action/task versions to prevent silent breakage on updates.

**Environment promotion**: use pipeline environments / deployment gates for staging → production promotion. Never deploy to production directly from a feature branch.

---

## Implementation Sub-skills

| Platform | Load |
|---|---|
| Azure DevOps | `ci-azure-devops` |
| GitHub Actions | _(coming soon — apply core principles above + GH Actions docs)_ |
| GitLab CI | _(coming soon — apply core principles above + GitLab CI docs)_ |

---

## Agent/Pool Decision Tree (Azure DevOps only)

```
Do you need custom tooling, private network access, or specific hardware?
├── Yes → Self-hosted agent pool (VMSS or static)
│   └── Azure VMSS pool — auto-scales, cost-effective for burst workloads
└── No  → Microsoft-hosted agents (ubuntu-latest, windows-latest, macos-latest)
    └── ubuntu-latest for most Linux workloads
```

See `ci-azure-devops` for org-specific pool names and conventions.
