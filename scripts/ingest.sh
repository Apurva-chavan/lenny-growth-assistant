#!/usr/bin/env bash
# ingest.sh — rebuild the vector index from transcripts
set -e

echo "Rebuilding vector index..."
docker compose exec backend python -c "
from app.knowledge.retriever import build_index
build_index(force=True)
print('Index rebuilt successfully')
"
echo "Done. Restart backend to use new index: docker compose restart backend"
