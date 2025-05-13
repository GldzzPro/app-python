#!/usr/bin/env python

import sys
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from api.dao.neo4j_client import Neo4jClient

def main():
    """
    Ingest mock data into Neo4j database.
    Creates sample Instance and Module nodes with relationships between them.
    """
    print("Ingesting mock data into Neo4j database...")
    
    try:
        # Create Neo4j client
        client = Neo4jClient(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        
        # MERGE a sample Instance node
        client.run("""
            MERGE (i:Instance {name: 'prod-instance-1'})
            ON CREATE SET i.created = timestamp()
            RETURN i
        """)
        print("Created Instance node")
        
        # MERGE two Module nodes with properties
        client.run("""
            MERGE (m:Module {id: 'module-1'})
            ON CREATE SET m.name = 'Core Module', 
                          m.version = '1.0.0',
                          m.created = timestamp()
            RETURN m
        """)
        
        client.run("""
            MERGE (m:Module {id: 'module-2'})
            ON CREATE SET m.name = 'Auth Module', 
                          m.version = '0.9.5',
                          m.created = timestamp()
            RETURN m
        """)
        print("Created Module nodes")
        
        # Create relationships between Instance and Modules
        client.run("""
            MATCH (i:Instance {name: 'prod-instance-1'})
            MATCH (m:Module {id: 'module-1'})
            MERGE (i)-[:DEPLOYS]->(m)
            MERGE (m)-[:DEPLOYED_BY]->(i)
        """)
        
        client.run("""
            MATCH (i:Instance {name: 'prod-instance-1'})
            MATCH (m:Module {id: 'module-2'})
            MERGE (i)-[:DEPLOYS]->(m)
            MERGE (m)-[:DEPLOYED_BY]->(i)
        """)
        print("Created Instance-Module relationships")
        
        # Create DEPENDS_ON relationship with properties
        client.run("""
            MATCH (m1:Module {id: 'module-2'})
            MATCH (m2:Module {id: 'module-1'})
            MERGE (m1)-[r:DEPENDS_ON {instance: 'prod-instance-1', since: '2023-01-15'}]->(m2)
            RETURN r
        """)
        print("Created Module dependency relationship")
        
        # Close the client
        client.close()
        
        print("Mock data ingestion completed successfully!")
        return 0
    except Exception as e:
        print(f"Error ingesting mock data: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())