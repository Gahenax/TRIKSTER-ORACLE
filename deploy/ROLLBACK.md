# Web Viewer Rollback Plan
Generated: 2026-02-11T23:19:21.715631+00:00

## Rollback triggers
- Gate fails post-deploy
- 5xx errors spike
- Signature verification anomalies
- Latency p95 degrades significantly
- Unexpected traffic abuse not mitigated by rate limiting

## Rollback steps (Docker Compose)
1) Stop service:
   docker compose -f deploy/docker-compose.viewer.yml --env-file deploy/.env down

2) Revert to previous image (if you tagged one):
   docker image ls | grep web-viewer
   docker tag web-viewer:<previous> web-viewer:local

3) Bring back previous version:
   docker compose -f deploy/docker-compose.viewer.yml --env-file deploy/.env up -d --build

4) Run post-deploy gate again:
   export VIEWER_BASE_URL=https://<your-domain>
   export VIEWER_API_KEY=<prod>
   ./deploy/run_postdeploy_gate.sh
