#!/usr/bin/env bash
# setup.sh — one-command setup for Lenny Growth Assistant
set -e

echo "=== Lenny Growth Assistant Setup ==="

# 1. Copy env if not present
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo "✓ Created backend/.env from .env.example"
  echo "  → Edit backend/.env to set your API keys if using cloud LLMs"
fi

# 2. Create transcript directory
mkdir -p data/transcripts
echo "✓ data/transcripts/ ready"
echo "  → Add .txt transcript files here (one per episode)"
echo "  → Optional first line format: # URL: https://www.lennyspodcast.com/..."

# 3. Build and start services
echo ""
echo "Starting services with Docker Compose..."
docker compose up -d --build

# 4. Wait for backend
echo "Waiting for backend to be ready..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend is up"
    break
  fi
  sleep 2
done

# 5. Pull Ollama model
echo "Pulling Ollama model (llama3.2)..."
docker compose exec ollama ollama pull llama3.2 || echo "  ⚠ Could not pull model automatically. Run: docker compose exec ollama ollama pull llama3.2"

echo ""
echo "=== Setup complete ==="
echo "  Frontend: http://localhost:3000"
echo "  API:      http://localhost:8000"
echo "  Health:   http://localhost:8000/health"
echo "  API docs: http://localhost:8000/docs"
