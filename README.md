# Neo4j Sync Microservice

A stateless microservice for ingesting Odoo module dependency data into a Neo4j knowledge graph.

## Overview

This microservice provides a bridge between the Graph Sync service (which collects module dependency data from Odoo instances) and Neo4j AuraDB. It exposes three main endpoints:

- `/health` - Check if the service is running and connected to Neo4j
- `/ingest` - Receive and process module dependency data for storage in Neo4j
- `/analyse` - Detect circular dependencies among modules using Neo4j's APOC library

## Features

- Builds a knowledge graph from module dependency data
- Handles multiple Odoo instances
- Creates unique module nodes with instance information
- Maintains relationships between modules and instances
- Detects circular dependencies using APOC
- Provides a simple control script for easy management

## Requirements

- Docker and Docker Compose
- Neo4j AuraDB or Neo4j instance with APOC plugin installed
- Graph Sync microservice (for providing module dependency data)

## Configuration

### Environment Variables

Configure the service using the following environment variables:

- `NEO4J_URI` - Connection URI for Neo4j (default: neo4j://localhost:7687)
- `NEO4J_USERNAME` - Neo4j username (default: neo4j)
- `NEO4J_PASSWORD` - Neo4j password (default: neo)
- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)

## Running the Service

### Using Docker Compose

Add the following service to your docker-compose.yml:

```yaml
neo4j_sync:
  build:
    context: ./neo4j_sync
    dockerfile: Dockerfile
  ports:
    - "8001:8001"
  environment:
    - NEO4J_URI=${NEO4J_URI:-neo4j://neo4j:7687}
    - NEO4J_USERNAME=${NEO4J_USERNAME:-neo4j}
    - NEO4J_PASSWORD=${NEO4J_PASSWORD:-neo}
    - LOG_LEVEL=DEBUG
  networks:
    - odoo_network
  healthcheck:
    test: [ "CMD", "curl", "-f", "http://localhost:8001/health" ]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 5s
```

Then run:

```bash
docker-compose up -d neo4j_sync
```

### Using the Control Script

A control script is provided for easy management:

```bash
# Start the service
./neo4j_sync.sh start

# Check health
./neo4j_sync.sh healthcheck

# Ingest data (automatically fetches from graph_sync)
./neo4j_sync.sh ingest

# Analyze dependencies for cycles
./neo4j_sync.sh analyse

# View logs
./neo4j_sync.sh logs

# Stop the service
./neo4j_sync.sh stop
```

## API Endpoints

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "service": "neo4j_sync",
  "neo4j_connected": true,
  "timestamp": "2025-05-13T10:15:23.123456"
}
```

### Ingest Data

```
POST /ingest
```

Request Body:
```json
{
  "instances_data": [
    {
      "instance": "odoo1",
      "status": "success",
      "data": {
        "nodes": [
          {
            "id": "module_name",
            "label": "Module",
            "properties": {
              "name": "module_name",
              "version": "1.0",
              "category": "Custom"
            }
          }
        ],
        "edges": [
          {
            "from_node": "module_a",
            "to_node": "module_b",
            "type": "DEPENDS_ON",
            "properties": {
              "required": true
            }
          }
        ]
      }
    }
  ]
}
```

Response:
```json
{
  "status": "success",
  "message": "Data from 1 instances ingested successfully"
}
```

### Analyze Dependencies

```
GET /analyse
```

Response:
```json
{
  "has_cycles": true,
  "cycles": [
    ["module_a", "module_b", "module_c", "module_a"]
  ],
  "affected_instances": ["odoo1", "odoo2"],
  "message": "Found 1 dependency cycles across 2 instances."
}
```

## Neo4j Knowledge Graph Structure

### Nodes

- `Instance`: Represents an Odoo instance
  - Properties: name, updated_at

- `Module`: Represents an Odoo module
  - Properties: name, instance, version, category, updated_at

### Relationships

- `(Instance)-[DEPLOYS]->(Module)`: Shows which instances have a module
- `(Module)-[DEPENDS_ON]->(Module)`: Module dependency relationship

## Integration with GitHub Workflows

This service can be triggered as part of your GitHub workflows to automatically detect dependency issues when branches are merged.

Example workflow:
```yaml
name: Check Module Dependencies

on:
  pull_request:
    branches: [ main ]

jobs:
  check-dependencies:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Trigger dependency analysis
        run: |
          curl -X POST http://your-server:8001/ingest -H "Content-Type: application/json" -d @graph_data.json
          CYCLES=$(curl -s http://your-server:8001/analyse)
          echo "Dependency analysis results: $CYCLES"
          if [[ $(echo $CYCLES | jq .has_cycles) == "true" ]]; then
            echo "Circular dependencies detected!"
            exit 1
          fi
```