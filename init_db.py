#!/usr/bin/env python

import sys
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from api.dao.neo4j_client import Neo4jClient

def main():
    """
    Initialize the Neo4j database by creating necessary constraints and indexes.
    """
    print("Initializing Neo4j database schema...")
    
    try:
        # Create Neo4j client
        client = Neo4jClient(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
        
        # Create schema (constraints and indexes)
        client.create_schema()
        
        print("Schema created successfully!")
        
        # Close the client
        client.close()
        
        return 0
    except Exception as e:
        print(f"Error initializing database: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())