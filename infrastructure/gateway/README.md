# Gateway Configuration Source of Truth

- Canonical gateway config: `infrastructure/gateway/nginx/nginx.conf`
- Static UI assets: `infrastructure/gateway/nginx/static/`
- Runtime mounts in `docker-compose.yml` must reference both paths above.
