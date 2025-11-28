import os
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey

_container_client = None

async def get_container():
    global _container_client
    if _container_client: return _container_client
    
    try:
        client = CosmosClient(
            url=os.getenv("COSMOS_ENDPOINT"), 
            credential=os.getenv("COSMOS_KEY")
        )

        database = await client.create_database_if_not_exists(id=os.getenv("COSMOS_DB_NAME"))

        _container_client = await database.create_container_if_not_exists(
            id=os.getenv("COSMOS_CONTAINER_NAME"),
            partition_key=PartitionKey(path="/userId")
        )

        print("✅ [DB] Conectado")
        return _container_client
    
    except Exception as e:
        print(f"❌ [DB] Error: {e}")
        return None