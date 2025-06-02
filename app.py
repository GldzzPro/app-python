from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import os
import sys
from datetime import datetime

# Add the parent directory to path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api.dao.neo4j_client import Neo4jClient

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("neo4j_sync")

# Neo4j connection settings from environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo")

# Create FastAPI app
app = FastAPI(
    title="Neo4j Sync Microservice",
    description="A stateless microservice for syncing Odoo module dependency data to Neo4j",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Models
class GraphNode(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any]

class GraphEdge(BaseModel):
    from_node: str
    to_node: str
    type: str
    properties: Dict[str, Any]

class GraphData(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)

class InstanceData(BaseModel):
    instance: str
    status: str
    data: Optional[GraphData] = None
    error: Optional[str] = None

class IngestRequest(BaseModel):
    instances_data: List[InstanceData]

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    service: str = "neo4j_sync"
    neo4j_connected: bool
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class CycleAnalysisResult(BaseModel):
    has_cycles: bool
    cycles: List[List[str]] = []
    affected_instances: List[str] = []
    message: str

# Global client variable
neo4j_client = None

def get_neo4j_client():
    """Get or create Neo4j client instance"""
    global neo4j_client
    if neo4j_client is None:
        try:
            neo4j_client = Neo4jClient(
                uri=NEO4J_URI,
                username=NEO4J_USERNAME,
                password=NEO4J_PASSWORD
            )
            logger.info("Successfully connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Neo4j connection failed: {str(e)}")
    return neo4j_client

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup Neo4j connection on shutdown"""
    global neo4j_client
    if neo4j_client:
        neo4j_client.close()
        logger.info("Neo4j connection closed")

# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the service is healthy and Neo4j is accessible"""
    neo4j_connected = False
    try:
        client = get_neo4j_client()
        # Verify connectivity
        client.run("RETURN 1")
        neo4j_connected = True
    except Exception as e:
        logger.warning(f"Neo4j health check failed: {str(e)}")
    
    return {
        "status": "ok",  # Service is ok even if Neo4j is not connected
        "version": "1.0.0",
        "service": "neo4j_sync",
        "neo4j_connected": neo4j_connected,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/ingest")
async def ingest_data(request: IngestRequest):
    """Ingest module dependency data into Neo4j"""
    try:
        client = get_neo4j_client()
        
        # First, ensure schema exists
        client.create_schema()
        
        # Process each instance's data
        for instance_data in request.instances_data:
            if instance_data.status != "success" or not instance_data.data:
                logger.warning(f"Skipping instance {instance_data.instance} due to status: {instance_data.status}")
                continue
                
            # Create Instance node
            client.run(
                "MERGE (i:Instance {name: $name})",
                {"name": instance_data.instance}
            )
            
            # Process module nodes
            for node in instance_data.data.nodes:
                client.run(
                    """
                    MERGE (m:Module {id: $id})
                    SET m += $properties
                    WITH m
                    MATCH (i:Instance {name: $instance})
                    MERGE (i)-[:DEPLOYS]->(m)
                    """,
                    {
                        "id": node["id"],
                        "properties": node,
                        "instance": instance_data.instance
                    }
                )
            
            # Process dependencies
            for edge in instance_data.data.edges:
                client.run(
                    """
                    MATCH (m1:Module {id: $from})
                    MATCH (m2:Module {id: $to})
                    MERGE (m1)-[r:DEPENDS_ON]->(m2)
                    SET r.instance = $instance
                    """,
                    {
                        "from": edge["from"],
                        "to": edge["to"],
                        "instance": instance_data.instance
                    }
                )
        
        return {"status": "success", "message": f"Data from {len(request.instances_data)} instances ingested successfully"}
    
    except Exception as e:
        logger.error(f"Error during ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during ingestion: {str(e)}")

@app.get("/analyse", response_model=CycleAnalysisResult)
async def analyse_dependencies():
    """Analyse the dependency graph for cycles"""
    try:
        client = get_neo4j_client()
        result = client.find_cycles()
        return result
    except Exception as e:
        logger.error(f"Error during cycle analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during cycle analysis: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
