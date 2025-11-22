import os
from azure.cosmos import CosmosClient, PartitionKey

container = None

def get_container():
    global container
    if container: return container
    
    try:
        client = CosmosClient(os.getenv("COSMOS_ENDPOINT"), credential=os.getenv("COSMOS_KEY"))
        db = client.create_database_if_not_exists(id=os.getenv("COSMOS_DB_NAME"))
        container = db.create_container_if_not_exists(
            id=os.getenv("COSMOS_CONTAINER_NAME"),
            partition_key=PartitionKey(path="/userId")
        )
        print("✅ [DB] Conectado")
        return container
    except Exception as e:
        print(f"❌ [DB] Error: {e}")
        return None