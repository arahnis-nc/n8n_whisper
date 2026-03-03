# Gateway Configuration Source of Truth

- Canonical Kong declarative config: `infrastructure/supabase/volumes/api/kong.yml`
- Runtime mounts in compose files must always reference this file.
- Legacy draft config location: `infrastructure/gateway/kong/kong.legacy.yml`
