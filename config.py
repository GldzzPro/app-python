import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Neo4j connection settings
NEO4J_URI = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'neo')

# No authentication required - using admin access via Neo4j credentials only
SALT_ROUNDS = int(os.getenv('SALT_ROUNDS', 10))