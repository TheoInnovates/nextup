# Grafana provisioning (added in Phase 8)

Mounted at `/etc/grafana/provisioning`. Phase 0 ships no datasources or
dashboards — observability is Phase 8's deliverable. In Phase 8 add:

- `datasources/prometheus.yml` — read-only Prometheus datasource
  (`url: http://prometheus:9090`, `isDefault: true`, `editable: false`).
- `dashboards/dashboards.yml` + dashboard JSON — request rate/latency/errors,
  active vs waitlisted registrations, check-ins, background-task failures.
