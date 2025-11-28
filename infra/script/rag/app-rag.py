import os
import glob
import numpy as np
import asyncpg
from openai import AsyncAzureOpenAI
from datetime import datetime
import asyncio
from typing import Optional, List 

# ----------------------------------------------------
# 1. CONFIGURACIÓN (REEMPLAZA ESTOS VALORES)
# ----------------------------------------------------

# Database Configuration (asyncpg requiere parámetros separados)
DB_HOST = os.environ['AZURE_DB_HOST_PSQL']
DB_USER = os.environ['AZURE_DB_USER_PSQL']
DB_PASS = os.environ['AZURE_DB_PASSWORD']
DB_NAME = os.environ['AZURE_DB_NAME_PSQL']
POSTGRES_TABLE = "gazette_chunks"

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY") 
OPENAI_DEPLOYMENT_ID = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT") 

# File Path
FILE_ROOT_PATH = "cdmx_gacetas/" 

# Concurrencia Máxima (Ajusta según las cuotas de tu API de OpenAI)
MAX_CONCURRENCY = 100 

# Inicializar Cliente Asíncrono de Azure OpenAI
client = AsyncAzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-02-01",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# ----------------------------------------------------
# 2. FUNCIONES CRÍTICAS ASÍNCRONAS
# ----------------------------------------------------

def classify_collection(date_gaceta: datetime) -> str:
    """Clasifica la fecha en collection1 o collection2."""
    # (Lógica de clasificación igual)
    start_c1 = datetime(2024, 10, 1).date()
    end_c1 = datetime(2025, 1, 31).date()
    date = date_gaceta.date()
    
    if start_c1 <= date <= end_c1:
        return "collection1"
    elif date.year >= 2025 or date.month >= 2:
        return "collection2"
    else:
        return "unknown" 

async def get_openai_embedding(text: str) -> Optional[List[float]]:
    """Llama a la API de forma asíncrona y aplica el casteo a float32."""
    try:
        response = await client.embeddings.create( 
            model=OPENAI_DEPLOYMENT_ID,
            input=text
        )
        vector_float64 = response.data[0].embedding
        
        # Casteo de float64 a float32
        vector_float32_list = np.array(vector_float64, dtype=np.float32).tolist()
        
        return vector_float32_list
    except Exception as e:
        # Esto captura errores de API (ej. Rate Limiting)
        print(f"❌ Error API/Embedding: {str(e)[:100]}...")
        # Devolver None permite que el flujo continúe sin bloquearse
        return None

async def insert_chunk(pool, data_tuple: tuple):
    """Inserta un chunk en la DB dentro de una transacción."""
    INSERT_SQL = f"""
        INSERT INTO {POSTGRES_TABLE} (chunk_id, source_filename, chunk_text, collection_name, gazette_date, embedding)
        VALUES ($1, $2, $3, $4, $5, $6);
    """
    try:
        async with pool.acquire() as conn: # Adquirir una conexión del pool
            # Usar await para ejecutar el comando
            await conn.execute(INSERT_SQL, *data_tuple)
        return True
    except Exception as e:
        print(f"❌ Error DB para {data_tuple[0]}: {e}")
        return False

# ----------------------------------------------------
# 3. COORDINACIÓN ASÍNCRONA
# ----------------------------------------------------

async def process_and_insert_files_async():
    """Coordina la lectura de archivos, vectorización concurrente y la inserción."""
    # Pool de Conexiones para manejar la concurrencia de la DB
    pool = await asyncpg.create_pool(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS,
        min_size=10, max_size=MAX_CONCURRENCY 
    )
    
    tasks = []
    
    # 1. Leer todos los archivos y crear las tareas de vectorización
    for file_path in glob.glob(os.path.join(FILE_ROOT_PATH, "**", "*.md"), recursive=True):
        
        file_name = os.path.basename(file_path)
        
        try:
            date_str = file_name[:10]
            gazette_date = datetime.strptime(date_str, '%Y-%m-%d')
            collection_name = classify_collection(gazette_date)
        except ValueError:
            print(f"❌ Error: No se pudo parsear la fecha del archivo: {file_name}. Saltando.")
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            chunk_text = f.read()

        if not chunk_text.strip():
            continue

        chunk_id = file_name.replace('.md', '')
        
        # Se crea una 'Tarea' asíncrona para cada chunk
        task = process_single_chunk(pool, chunk_id, file_name, chunk_text, collection_name, gazette_date)
        tasks.append(task)
    
    # 2. Ejecutar todas las tareas concurrentemente
    print(f"Iniciando procesamiento concurrente de {len(tasks)} archivos...")
    # asyncio.gather ejecuta todas las tareas a la vez
    results = await asyncio.gather(*tasks) 
    
    successful_inserts = sum(results)
    print("\n--- INGESTA COMPLETADA ---")
    print(f"Total de tareas intentadas: {len(tasks)}")
    print(f"Chunks insertados con éxito: {successful_inserts}")
    
    await pool.close()

async def process_single_chunk(pool, chunk_id, file_name, chunk_text, collection_name, gazette_date):
    """Procesa un solo chunk: vectoriza e inserta."""
    vector = await get_openai_embedding(chunk_text) # El bottleneck de red se espera
    
    if vector:
        data_tuple = (
            chunk_id, 
            file_name, 
            chunk_text, 
            collection_name, 
            gazette_date.date(), # Insertar solo la fecha
            vector
        )
        # 🔑 Inserción asíncrona en la DB
        return await insert_chunk(pool, data_tuple) 
    else:
        # El embedding falló (ej. Rate limit)
        return False


# ----------------------------------------------------
# 4. PUNTO DE ENTRADA
# ----------------------------------------------------

if __name__ == "__main__":
    # La función main debe ser el punto de entrada síncrono que llama al asíncrono
    try:
        asyncio.run(process_and_insert_files_async())
    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario.")
    except Exception as e:
        print(f"\n❌ ERROR FATAL EN EL MAIN: {e}")