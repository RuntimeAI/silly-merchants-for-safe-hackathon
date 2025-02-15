#!/bin/bash

# Create networks if they don't exist
docker network create game_network 2>/dev/null || true

# Start backend
docker-compose -f docker-compose.backend.yml up -d

# Start frontend
docker-compose -f docker-compose.frontend.yml up -d

# Show logs
docker-compose -f docker-compose.backend.yml -f docker-compose.frontend.yml logs -f 