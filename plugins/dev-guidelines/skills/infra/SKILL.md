---
name: infra
description: Infrastructure and deployment decision tree — Kubernetes+Helm vs Docker Compose vs Serverless vs ArgoCD GitOps — with trade-offs and when to use each. Routes to implementation conventions for the chosen approach. Load after dev-guidelines.
license: MIT
compatibility: claude-code
metadata:
  audience: developers
  workflow: infrastructure
---

## What I do

I help choose the right deployment infrastructure and routing to its conventions. I cover the decision and general patterns — org-specific cluster names, registries, and deploy workflows are in the `org` skill.

## When to use me

Load when setting up deployment infrastructure for a new service, or when reviewing/modifying existing deployment configuration.

---

## Deployment Model Decision Tree

```
How many services? What scale?
├── Single service, simple needs → Docker Compose  ← local dev / small deployments
├── Multiple services, production scale, HA required → Kubernetes + Helm
│   └── How are deployments triggered?
│       ├── Pipeline pushes to cluster → Helm via CI/CD pipeline
│       └── Git is source of truth, cluster syncs itself → ArgoCD GitOps
└── Stateless workload, no infra management → Serverless
    ├── Azure → Azure Functions / Container Apps
    ├── AWS → Lambda / ECS Fargate
    └── GCP → Cloud Run
```

**Trade-offs:**

| Approach | Best for | Watch out for |
|---|---|---|
| **Docker Compose** | Local dev, single-server, small teams, quick prototypes | No HA, no auto-scaling, no rolling updates |
| **Kubernetes + Helm** | Production, multi-service, HA, auto-scaling, rolling deployments | Operational complexity; steep learning curve; requires cluster management |
| **ArgoCD GitOps** | Auditable deployments, self-healing clusters, team-scale K8s | Adds ArgoCD as a dependency; sync loops if not configured carefully |
| **Serverless** | Stateless workloads, event-driven, pay-per-use | Cold starts; vendor lock-in; limited runtime control; debugging is harder |

---

## Docker Compose Conventions

Use for local development environments and simple single-server deployments.

### Key patterns

```yaml
# docker-compose.yaml — named volumes, explicit networks, health checks
version: "3.9"
services:
  api:
    build: .
    ports:
      - "3000:3000"
    env_file: .env.local          # gitignored decrypted env
    depends_on:
      db:
        condition: service_healthy
    networks: [app-net]

  db:
    image: postgres:16-alpine
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 5s
      retries: 5
    networks: [app-net]

volumes:
  db-data:

networks:
  app-net:
```

- Always use `env_file: .env.local` (decrypted, gitignored) — never hardcode values.
- Always define health checks for dependencies; use `depends_on: condition: service_healthy`.
- Named volumes for persistent data; never bind-mount DB data directories.
- Explicit networks — do not rely on the default bridge.
- For local dev, override with `docker-compose.override.yaml` (hot-reload, debug ports, etc.).

---

## Kubernetes + Helm Conventions

Use for production multi-service deployments requiring HA, rolling updates, and auto-scaling.

### Chart structure

```
charts/<service-name>/
  Chart.yaml            ← name, version, appVersion
  values.yaml           ← defaults (no env-specific values here)
  values-staging.yaml   ← staging overrides
  values-production.yaml← production overrides
  templates/
    deployment.yaml
    service.yaml
    ingress.yaml
    configmap.yaml
    externalsecret.yaml ← ExternalSecrets for Key Vault / Secrets Manager
```

### Image tagging convention

```
<registry>/<service-name>:<YYYYMMDD>.<build-number>-<git-short-sha>-<branch>-<SNAPSHOT|RELEASE>
```

Special tags:
- `staging-latest` — rolling tag for staging; always points to the latest staging build
- `last-good` — manually promoted tag; used for infra/utility images
- `buildcache` / `buildcache-staging` — Docker layer cache in registry

### Deployment strategies

| Environment | Strategy | Rationale |
|---|---|---|
| Dev / staging | `Recreate` | Simpler, faster; downtime acceptable |
| Production | `RollingUpdate` or ArgoCD `BlueGreen` | Zero downtime; safe rollback |

### Resource limits — always set

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```
Pods without resource limits can starve other pods on the node.

### Health checks — always define

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 15

readinessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 10
```

### Secrets — never in Helm values

```yaml
# ✅ Correct — ExternalSecrets pulls from Key Vault / Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: my-service-secrets
spec:
  secretStoreRef:
    name: <vault-store-name>
    kind: SecretStore
  target:
    name: my-service-secrets
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: my-service-database-url

# ❌ Wrong — secrets in values.yaml or hardcoded in templates
env:
  - name: DATABASE_URL
    value: "postgresql://user:password@host/db"
```

### Ingress conventions

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-service
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  rules:
    - host: "{{ .Values.ingress.host }}"
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-service
                port:
                  number: 3000
  tls:
    - hosts:
        - "{{ .Values.ingress.host }}"
      secretName: "{{ .Values.ingress.host }}-tls"
```

---

## Helmfile Multi-Chart Orchestration

Use when deploying multiple related charts together with dependency ordering.

```yaml
# helmfile.yaml
releases:
  - name: postgres
    chart: bitnami/postgresql
    values:
      - values/postgres.yaml

  - name: backend
    chart: ./charts/backend
    needs: [postgres]           # deploy after postgres is ready
    values:
      - values/backend-{{ .Environment.Name }}.yaml

environments:
  dev:
    values: [environments/dev.yaml]
  prod:
    values: [environments/prod.yaml]
```

**Key commands:**
```bash
helmfile -e dev sync                           # deploy all releases
helmfile -e dev diff                           # preview changes before apply
helmfile -e dev write-values                   # debug: show resolved values
helmfile -e dev -l name=backend sync \
  --include-transitive-needs                   # deploy specific release + deps
```

**Patterns:**
- `needs:` declares deployment order — always explicit, never rely on implicit ordering
- `.gotmpl` files use Go templating for env-specific values composition
- `diff` before every `sync` in production

---

## ArgoCD GitOps Conventions

Use when Git is the source of truth for cluster state. No manual `helm upgrade` in pipelines.

```
Git commit → ArgoCD detects diff (poll: 3 min) → syncs to cluster
```

### Application manifest

```yaml
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-service
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io    # always include — enables prune on delete
  annotations:
    notifications.argoproj.io/subscribe.on-sync-failed.slack: argocd-alerts
spec:
  project: default
  destination:
    server: https://kubernetes.default.svc
    namespace: my-namespace
  syncPolicy:
    automated:
      prune: true        # delete resources removed from git
      selfHeal: true     # revert manual cluster changes
  sources:               # multi-source (modern ArgoCD pattern)
    - repoURL: https://github.com/org/helm-repo
      targetRevision: HEAD    # use branch name during development; switch to HEAD before merge
      path: charts/my-service
      helm:
        valueFiles:
          - values-prod.yaml
```

**`targetRevision` pattern:**
- During development on a branch: set to branch name for live testing
- Before merging: change back to `HEAD`
- Leave a comment: `# TODO: Change to HEAD before merging`

### Sync policies

| Policy | Use when |
|---|---|
| `automated: {prune: true, selfHeal: true}` | Full GitOps — git is authoritative, drift is forbidden |
| `automated: {}` only | Dev/staging — auto-sync but allow manual cluster experiments |
| No `automated:` | Production gates requiring human approval before sync |

### CI/CD integration — pipeline updates git, ArgoCD syncs

```bash
# Pipeline after building a new image:
yq eval -i '.spec.source.helm.parameters[] |= select(.name == "image.tag").value = "'$NEW_TAG'"' \
  argo/applications/prod/my-service.yaml
git commit -m "📦 chore(my-service): deploy $NEW_TAG to prod"
git push
# ArgoCD auto-syncs within 3 minutes
```

### Rollback

```bash
argocd app history my-service          # list revisions
argocd app rollback my-service 5       # rollback to revision 5

# Or via git (preferred — keeps history clean):
git revert <deploy-commit-hash>
git push                               # ArgoCD syncs to previous state
```

---

## Serverless Conventions

Use for stateless, event-driven workloads where you want zero infra management.

### When serverless is appropriate

- Function runs < 15 minutes
- Workload is event-driven (HTTP trigger, queue, schedule)
- Traffic is spiky — cost scales to zero at idle
- No persistent connections needed (no long-lived DB connections)

### When serverless is NOT appropriate

- Workload needs persistent connections (connection pooling works around this but adds complexity)
- Cold start latency is unacceptable (< 100ms response required)
- Need full control over runtime (custom binary, native extensions)
- Stateful processing or long-running jobs

### Pattern (Azure Container Apps — preferred over Functions for containerized workloads)

```yaml
# containerapp.yaml
properties:
  template:
    containers:
      - name: my-service
        image: <registry>/<image>:<tag>
        env:
          - name: DATABASE_URL
            secretRef: database-url    # from Container App secrets
    scale:
      minReplicas: 0                   # scale to zero when idle
      maxReplicas: 10
      rules:
        - name: http-scaling
          http:
            metadata:
              concurrentRequests: "10"
```

---

## What not to do

- Do not hardcode image tags in manifests — always parameterize via Helm values or ArgoCD.
- Do not store secrets in Helm values files — use ExternalSecrets or sealed secrets.
- Do not run containers as root — set `runAsNonRoot: true` in pod security context.
- Do not skip resource limits — unguarded pods cause node resource exhaustion.
- Do not use `latest` tag in production — it is not reproducible and breaks rollback.
- Do not bind-mount host paths for persistent data — use named volumes or PVCs.
