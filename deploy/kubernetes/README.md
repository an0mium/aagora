# Aragora Kubernetes Deployment

This directory contains Kubernetes manifests for deploying Aragora.

## Quick Start

```bash
# 1. Create namespace and base resources
kubectl apply -k deploy/kubernetes/

# 2. Create secrets (replace with real values)
kubectl create secret generic aragora-secrets \
  --namespace=aragora \
  --from-literal=ANTHROPIC_API_KEY=your-key \
  --from-literal=OPENAI_API_KEY=your-key

# 3. Verify deployment
kubectl get pods -n aragora
kubectl logs -n aragora -l app.kubernetes.io/name=aragora
```

## Architecture

```
                    ┌─────────────────┐
                    │     Ingress     │
                    │   (nginx/ALB)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     Service     │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
    │   Pod   │         │   Pod   │         │   Pod   │
    │ aragora │         │ aragora │         │ aragora │
    └────┬────┘         └────┬────┘         └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │       PVC       │
                    │  (SQLite data)  │
                    └─────────────────┘
```

## Files

| File | Purpose |
|------|---------|
| `namespace.yaml` | Creates the aragora namespace |
| `configmap.yaml` | Non-sensitive configuration |
| `secrets.yaml` | API keys template (don't commit real values!) |
| `deployment.yaml` | Main application deployment |
| `service.yaml` | ClusterIP service + Ingress |
| `pvc.yaml` | Persistent volume for data |
| `hpa.yaml` | Horizontal Pod Autoscaler |
| `pdb.yaml` | Pod Disruption Budget |
| `rbac.yaml` | ServiceAccount and permissions |
| `kustomization.yaml` | Kustomize configuration |

## Configuration

### Required Secrets

At minimum, you need one AI provider API key:

```bash
kubectl create secret generic aragora-secrets \
  --namespace=aragora \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-... \
  --from-literal=ARAGORA_API_TOKEN=your-api-token
```

### Optional Configuration

Edit `configmap.yaml` to customize:
- `ARAGORA_ALLOWED_ORIGINS` - CORS origins
- `LOG_LEVEL` - Logging verbosity
- Rate limiting parameters

## Scaling

The HPA automatically scales between 2-10 replicas based on:
- CPU utilization > 70%
- Memory utilization > 80%

Manual scaling:
```bash
kubectl scale deployment aragora -n aragora --replicas=5
```

## Monitoring

### Health Checks

```bash
# Liveness probe
curl https://aragora.ai/api/health

# Pod status
kubectl get pods -n aragora -w
```

### Logs

```bash
# All pods
kubectl logs -n aragora -l app.kubernetes.io/name=aragora -f

# Specific pod
kubectl logs -n aragora aragora-xxxx-yyyy -f
```

### Metrics

Prometheus metrics available at `/metrics` endpoint.

## Troubleshooting

### Pod not starting

```bash
kubectl describe pod -n aragora aragora-xxxx-yyyy
kubectl logs -n aragora aragora-xxxx-yyyy --previous
```

### Database issues

Currently using SQLite with PVC. For production, migrate to PostgreSQL:
- Use Supabase or RDS
- Update `SUPABASE_URL` and `SUPABASE_KEY` in secrets

### WebSocket issues

Ensure ingress annotations include:
```yaml
nginx.ingress.kubernetes.io/websocket-services: "aragora"
nginx.ingress.kubernetes.io/proxy-http-version: "1.1"
```

## Production Checklist

- [ ] Replace secrets template with real values (use external-secrets or sealed-secrets)
- [ ] Configure TLS certificates (cert-manager recommended)
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure alerting
- [ ] Test HPA scaling
- [ ] Verify PDB during node maintenance
- [ ] Consider migrating to PostgreSQL for multi-replica writes
