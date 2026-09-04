# Health check for the AegisPay stack (Windows). Mirrors `make health`.
Write-Output "== backend =="
try { "health: " + (Invoke-WebRequest -Uri http://localhost:8000/v1/health -UseBasicParsing).Content } catch { "health: FAIL" }
try { "readyz: " + (Invoke-WebRequest -Uri http://localhost:8000/v1/readyz -UseBasicParsing).Content } catch { "readyz: FAIL" }
Write-Output "== ai runtime =="
try { "openapi: " + (Invoke-WebRequest -Uri http://localhost:8001/openapi.json -UseBasicParsing).StatusCode } catch { "openapi: FAIL" }
Write-Output "== frontend =="
try { "web: " + (Invoke-WebRequest -Uri http://localhost:3002/ -UseBasicParsing).StatusCode } catch { "web: FAIL" }
Write-Output "== containers =="
docker compose -f deploy/compose/docker-compose.yml ps --format "table {{.Service}}\t{{.Status}}" 2>&1
