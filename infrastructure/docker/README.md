# Dockerfiles (added in Phase 1)

Application Dockerfiles live alongside their apps (`apps/api/Dockerfile`,
`apps/web/Dockerfile`) and are added in Phase 1. This directory holds any shared
or infrastructure-specific Docker assets if they become necessary. Containers run
as non-root where practical (spec §13).
