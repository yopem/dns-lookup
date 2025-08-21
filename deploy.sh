#!/bin/bash

# DNS Lookup Tool - Deployment Script
# This script helps deploy the DNS lookup tool using Docker

set -e

echo "🔍 DNS Lookup Tool - Docker Deployment Script"
echo "=============================================="

# Check if Docker is installed
if ! command -v docker &>/dev/null; then
  echo "❌ Docker is not installed. Please install Docker first."
  echo "📖 Visit: https://docs.docker.com/get-docker/"
  exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &>/dev/null; then
  echo "⚠️  Docker Compose not found. Trying with 'docker compose'..."
  COMPOSE_CMD="docker compose"
else
  COMPOSE_CMD="docker-compose"
fi

echo "🐳 Building DNS Lookup Tool container..."

# Build and start the container
if $COMPOSE_CMD up -d; then
  echo "✅ DNS Lookup Tool deployed successfully!"
  echo "🌐 Access the web interface at: http://localhost:7001"
  echo ""
  echo "📊 Container status:"
  docker ps | grep dns-lookup || echo "Container not found in running processes"
  echo ""
  echo "🛠️  Useful commands:"
  echo "   View logs: $COMPOSE_CMD logs -f"
  echo "   Stop:      $COMPOSE_CMD down"
  echo "   Rebuild:   $COMPOSE_CMD up -d --build"
else
  echo "❌ Failed to deploy DNS Lookup Tool"
  echo "🔍 Check the error messages above"
  exit 1
fi

