import os
import pytest
from neo4j.exceptions import Neo4jError

from api.dao.neo4j_client import Neo4jClient
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

@pytest.fixture(scope="module")
def neo4j_client():
    """Create a Neo4j client for testing and set up schema and test data"""
    client = Neo4jClient(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    # Create schema with named constraints and indexes
    client.create_schema()
    # Create test data for the tests
    client.create_test_data()
    yield client
    client.close()

def test_schema_constraints_exist(neo4j_client):
    """Test that the required constraints exist in the database"""
    # Check Module.id constraint
    result = neo4j_client.run("""
        SHOW CONSTRAINTS
        WHERE name = 'module_id_unique'
    """)
    assert result.single() is not None, "Module.id constraint not found"
    
    # Check Instance.name constraint
    result = neo4j_client.run("""
        SHOW CONSTRAINTS
        WHERE name = 'instance_name_unique'
    """)
    assert result.single() is not None, "Instance.name constraint not found"

def test_indexes_exist(neo4j_client):
    """Test that the required indexes exist in the database"""
    # Check Module.id index
    result = neo4j_client.run("""
        SHOW INDEXES
        WHERE labelsOrTypes = ['Module'] AND properties = ['id']
    """)
    assert result.single() is not None, "Module.id index not found"
    
    # Check Instance.name index
    result = neo4j_client.run("""
        SHOW INDEXES
        WHERE labelsOrTypes = ['Instance'] AND properties = ['name']
    """)
    assert result.single() is not None, "Instance.name index not found"

def test_instance_node_exists(neo4j_client):
    """Test that the Instance node exists"""
    result = neo4j_client.run("""
        MATCH (i:Instance {name: 'prod-instance-1'})
        RETURN i
    """)
    assert result.single() is not None, "Instance node not found"

def test_module_nodes_exist(neo4j_client):
    """Test that the Module nodes exist"""
    # Check module-1
    result = neo4j_client.run("""
        MATCH (m:Module {id: 'module-1'})
        RETURN m
    """)
    assert result.single() is not None, "Module 1 not found"
    
    # Check module-2
    result = neo4j_client.run("""
        MATCH (m:Module {id: 'module-2'})
        RETURN m
    """)
    assert result.single() is not None, "Module 2 not found"

def test_relationships_exist(neo4j_client):
    """Test that the relationships between nodes exist"""
    # Check DEPLOYS relationships
    result = neo4j_client.run("""
        MATCH (:Instance {name: 'prod-instance-1'})-[r:DEPLOYS]->(:Module)
        RETURN count(r) as count
    """)
    assert result.single()["count"] == 2, "Expected 2 DEPLOYS relationships"
    
    # Check DEPLOYED_BY relationships
    result = neo4j_client.run("""
        MATCH (:Module)-[r:DEPLOYED_BY]->(:Instance {name: 'prod-instance-1'})
        RETURN count(r) as count
    """)
    assert result.single()["count"] == 2, "Expected 2 DEPLOYED_BY relationships"
    
    # Check DEPENDS_ON relationship with properties
    result = neo4j_client.run("""
        MATCH (:Module {id: 'module-2'})-[r:DEPENDS_ON]->(:Module {id: 'module-1'})
        WHERE r.instance = 'prod-instance-1'
        RETURN r
    """)
    relationship = result.single()["r"]
    assert relationship is not None, "DEPENDS_ON relationship not found"
    assert relationship["instance"] == "prod-instance-1", "Incorrect instance property"
    assert relationship["since"] == "2023-01-15", "Incorrect since property"