# Prometheus config (added in Phase 8)

Mounted at `/etc/prometheus`. Phase 0 ships no scrape config — observability is
Phase 8's deliverable. In Phase 8 add `prometheus.yml` with a scrape job for the
FastAPI backend (`api:8000`, `metrics_path: /metrics`) and for Caddy
(`caddy:2019` / metrics endpoint), following the project-4-workspace pattern:

```yaml
global:
  scrape_interval: 30s
scrape_configs:
  - job_name: nextup-api
    metrics_path: /metrics
    static_configs:
      - targets: ["api:8000"]
```
