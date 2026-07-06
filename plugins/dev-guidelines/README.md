# dev-guidelines

General-purpose development guidelines: decision trees for CI platform and infra choices, testing philosophy, Taskfile conventions, and framework-specific sub-skills (Python/TypeScript backend, frontend, Azure DevOps CI).

These skills are intentionally company-agnostic. Where a real team needs org-specific detail (internal registries, cluster names, secrets workflow), they route to a local `org` skill that you maintain outside this repo — see the "See the `org` skill" pointers inside each SKILL.md.

## Skills

| Skill | Purpose |
|-------|---------|
| `dev-guidelines` | Entry point — universal rules, routes to framework sub-skills |
| `ci` | CI/CD platform decision tree (Azure DevOps / GitHub Actions / GitLab CI) |
| `infra` | Infra decision tree (K8s+Helm / Docker Compose / Serverless / ArgoCD) |
| `testing` | Testing philosophy, TDD/BDD workflow, framework sub-skills |
| `taskfile-patterns` | Taskfile (go-task) best practices and a starter template |
| `interactive-review` | Browser-based interactive review companion for plans/reports |
