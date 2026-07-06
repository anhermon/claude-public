---
name: ci-azure-devops
description: Azure DevOps Pipelines conventions — task invocation, pre-commit in CI, stage structure, variable groups, secrets management, and agent pool patterns. Load after ci (which covers the platform decision). For org-specific pool names, service connections, and variable groups, also load the org skill.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: ci-cd
---

## What I do

I provide conventions for Azure DevOps Pipelines: how to structure stages, invoke tasks, run quality checks, manage secrets, and keep local and CI execution identical.

## When to use me

Load when writing or modifying Azure DevOps pipeline YAML, adding stages, or debugging CI failures.

---

## Core Principle

**Local and CI execution must be identical.** Pipelines invoke the same `task` commands and `pre-commit` hooks that developers run locally. Never reimplement commands inline in pipeline YAML.

```yaml
# ✅ Correct — delegates to the Taskfile
- script: task test:backend
  displayName: 'Run backend tests'

# ❌ Wrong — duplicates what the Taskfile already defines
- script: |
    cd backend
    pytest tests/ --cov=src
  displayName: 'Run backend tests'
```

If a pipeline step needs something not covered by a Taskfile task, **add the task first**, then invoke it from the pipeline.

---

## Pipeline Structure

### Standard stage order

```
Quality (lint, format, type-check, security scan)
  ↓
Unit Tests
  ↓
Integration Tests
  ↓
Build (Docker image / artifact)
  ↓
Deploy (staging → production with approval gate)
```

### Minimal PR pipeline template

```yaml
trigger:
  branches:
    include:
      - main
      - 'feature/*'

pool:
  vmImage: ubuntu-latest        # Microsoft-hosted; replace with self-hosted pool name if needed

stages:
  - stage: Quality
    jobs:
      - job: Checks
        steps:
          - script: pip install pre-commit
            displayName: 'Install pre-commit'
          - script: pre-commit run --all-files --hook-stage commit
            displayName: 'Commit-stage hooks (lint, format)'
          - script: pre-commit run --all-files --hook-stage push
            displayName: 'Push-stage hooks (type-check, security scan)'

  - stage: Test
    dependsOn: Quality
    jobs:
      - job: UnitTests
        steps:
          - script: task test:unit
            displayName: 'Unit tests'
      - job: IntegrationTests
        steps:
          - script: task test:integration
            displayName: 'Integration tests'

  - stage: Build
    dependsOn: Test
    jobs:
      - job: BuildImage
        steps:
          - script: task build
            displayName: 'Build artifact / Docker image'

  - stage: Deploy
    dependsOn: Build
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployStaging
        environment: staging          # environment with optional approval gate
        strategy:
          runOnce:
            deploy:
              steps:
                - script: task deploy:staging
                  displayName: 'Deploy to staging'
```

---

## Pre-commit in Pipelines

Run pre-commit as a dedicated pipeline step against the full codebase on every PR build. This catches anything that slipped through without hooks installed locally.

```yaml
- script: |
    pip install pre-commit
    pre-commit run --all-files --hook-stage commit
    pre-commit run --all-files --hook-stage push
  displayName: 'pre-commit checks'
```

This is the **single source of truth** for lint, format, type-check, and security scan. Do not add separate ESLint, ruff, or mypy steps alongside it.

---

## Variables and Secrets

**Never store secrets in pipeline YAML.** Use variable groups or Key Vault-linked variables.

```yaml
variables:
  - group: my-service-secrets        # variable group linked to Key Vault or manually managed
  - name: BUILD_CONFIGURATION
    value: Release                   # non-secret build-time config is fine inline

steps:
  - script: task deploy
    displayName: 'Deploy'
    env:
      DATABASE_URL: $(DATABASE_URL)   # maps variable group value to env var
      API_KEY: $(API_KEY)             # from Key Vault link
```

**Variable group patterns:**
- `my-service-<env>` — per-service, per-environment secrets
- Shared infra variables (ARM credentials, ACR credentials) — in a shared group referenced by name

**Pipeline-level vs step-level secrets:**
- Map secrets to environment variables at the **step level** — only the steps that need them receive them.
- Never map all variable group vars globally at the pipeline level.

---

## Agent Pools

```yaml
pool:
  vmImage: ubuntu-latest         # Microsoft-hosted — no setup, limited customization

# OR self-hosted:
pool:
  name: my-vmss-pool             # VMSS auto-scale pool name (replace with actual pool name)
  demands:
    - docker                     # optional: declare tool requirements
```

**When to use self-hosted:**
- Need private network access (on-prem DB, internal services)
- Need custom tooling not available on Microsoft-hosted agents
- Require faster builds via caching on persistent agents
- Azure VMSS pools are preferred over static self-hosted agents for cost and scale

---

## Container Jobs (for reproducible build environments)

```yaml
jobs:
  - job: Build
    container:
      image: my-registry/my-build-image:1.0.0
      endpoint: my-registry-service-connection   # service connection name for private registry
    steps:
      - script: task build
```

Use container jobs when the build environment must be exactly reproducible (matching local dev container or a specific tool version).

---

## Pinning Versions

Always pin task versions (`@0`, `@1`, `@2`) on all pipeline tasks to prevent silent breakage:

```yaml
# ✅ Pinned
- task: Docker@2
  inputs:
    command: push

# ❌ Unpinned — breaks silently when the task is updated
- task: Docker
  inputs:
    command: push
```

---

## Environments and Approval Gates

Use Azure DevOps Environments for deployment stages that require approval before proceeding:

```yaml
- deployment: DeployProduction
  environment:
    name: production
    resourceType: VirtualMachine    # or Kubernetes
  strategy:
    runOnce:
      deploy:
        steps:
          - script: task deploy:production
```

Configure approval gates in the Azure DevOps UI under Pipelines → Environments → Approvals and Checks.

---

## Multi-stage YAML Templates

Extract repeated job patterns into YAML templates to avoid duplication:

```yaml
# templates/jobs/run-tests.yaml
parameters:
  - name: testTask
    type: string

jobs:
  - job: RunTests
    steps:
      - script: task ${{ parameters.testTask }}
        displayName: 'Run ${{ parameters.testTask }}'

# azure-pipelines.yaml
stages:
  - stage: Test
    jobs:
      - template: templates/jobs/run-tests.yaml
        parameters:
          testTask: test:integration
```

---

## Caching

Cache dependencies to speed up builds:

```yaml
- task: Cache@2
  inputs:
    key: '"pip" | "$(Agent.OS)" | requirements.txt'
    restoreKeys: |
      "pip" | "$(Agent.OS)"
    path: $(PIP_CACHE_DIR)
  displayName: 'Cache pip packages'
```

Cache keys should include OS, lock file content, and a category prefix. Restore keys provide fallback matches.

---

## What not to do

- Do not inline commands that duplicate Taskfile logic.
- Do not store secrets in pipeline YAML — use variable groups or Key Vault.
- Do not use unpinned task versions.
- Do not run all stages unconditionally — add `dependsOn` and `condition` to fail fast.
- Do not put environment-specific logic in pipeline YAML — put it in the Taskfile or application config.
- Do not run integration tests before unit tests pass.
- Do not deploy to production without an approval gate or environment protection.
