# Nova Memory Cloud

Cloud-hosted API for AI Agent Memory.

## Quick Start

```bash
# Install dependencies
pip install -r cloud/requirements.txt

# Start the cloud server
python -m cloud.server

# Or with uvicorn
uvicorn cloud.server:app --host 0.0.0.0 --port 8000 --reload
```

## API Key Authentication

All API endpoints (except `/health` and `/docs`) require an API key:

```bash
# Include in header
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v2/memories
```

## Create API Key

```bash
curl -X POST http://localhost:8000/api/cloud/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "tier": "free"}'
```

## Pricing Tiers

| Tier | RPM | Monthly Requests | Monthly Tokens | Features |
|------|-----|------------------|----------------|----------|
| Free | 60 | 10,000 | 100K | Basic |
| Starter | 300 | 100K | 1M | +Collaboration |
| Pro | 1,000 | 1M | 10M | +Workflows |
| Enterprise | 10K | Unlimited | Unlimited | +SLA |

## Environment Variables

```bash
NOVA_MEMORY_DB_PATH=./data/nova_memory.db
NOVA_CLOUD_DB_PATH=./data/api_keys.db
```

## Endpoints

- `POST /api/cloud/keys` - Create API key
- `GET /api/cloud/keys` - List your API keys
- `DELETE /api/cloud/keys/{id}` - Revoke API key
- `GET /api/cloud/usage` - Get usage stats
- `GET /api/cloud/limits` - Get rate limits
- `GET /api/cloud/tiers` - List pricing tiers
