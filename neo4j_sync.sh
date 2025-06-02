#!/bin/bash

# Neo4j Sync Control Script
# Usage: ./neo4j_sync.sh [start|stop|healthcheck|ingest|analyse]

# Configuration
SERVICE_PORT=8001
CONTAINER_NAME="neo4j_sync"
NETWORK="odoo_network"

function start() {
    echo "Starting Neo4j Sync service..."
    docker-compose up -d neo4j_sync
    echo "Service started!"
}

function stop() {
    echo "Stopping Neo4j Sync service..."
    docker-compose stop neo4j_sync
    echo "Service stopped!"
}

function healthcheck() {
    echo "Checking Neo4j Sync service health..."
    curl -s http://localhost:${SERVICE_PORT}/health | json_pp
}

function ingest_data() {
    echo "Fetching module dependency data from graph_sync service..."
    # Get data from graph_sync
    GRAPH_DATA=$(curl -s http://localhost:8000/trigger)
    
    # Send to neo4j_sync
    echo "Ingesting data to Neo4j..."
    curl -s -X POST http://localhost:${SERVICE_PORT}/ingest \
        -H "Content-Type: application/json" \
        -d "{\"instances_data\": ${GRAPH_DATA}}" | json_pp
}

function analyse() {
    echo "Analysing dependency cycles..."
    curl -s http://localhost:${SERVICE_PORT}/analyse | json_pp
}

function logs() {
    echo "Showing logs for Neo4j Sync service..."
    docker logs -f ${CONTAINER_NAME}
}

# Main
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    healthcheck)
        healthcheck
        ;;
    ingest)
        ingest_data
        ;;
    analyse)
        analyse
        ;;
    logs)
        logs
        ;;
    *)
        echo "Usage: $0 [start|stop|healthcheck|ingest|analyse|logs]"
        exit 1
esac