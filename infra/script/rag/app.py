import asyncio
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes.models import (
    DataSourceConnection,
    SearchIndexerSkillset,
    SearchIndexer,
    SearchIndexerSkill,
    SplitSkill,
    AzureOpenAIEmbeddingSkill,
    FieldMapping,
    OutputFieldMapping,
    IndexingParametersConfiguration,
    HighWaterMarkChangeDetectionPolicy,
)

# *** Finalmente no funciona tiene problemas con el SDK ***

# =========================
# ENVIROMENT CONFIG
# =========================
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_BLOB_CONTAINER = os.getenv("AZURE_STORAGE_BLOB_CONTAINER")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# Nombres de los recursos a crear
SKILLSET_NAME = "rag-vectorization-skillset"
INDEX_NAMES = ["rag-index-1", "rag-index-2"]
DATASOURCE_HISTORIC = "data-source-historic"
DATASOURCE_CURRENT = "data-source-current"
INDEXER_HISTORIC = "rag-indexer-1"
INDEXER_CURRENT = "rag-indexer-2"

# Cliente de Azure AI Search (para crear/gestionar recursos)
search_admin_client = SearchIndexerClient(
    endpoint=AZURE_SEARCH_ENDPOINT, 
    credential=AzureKeyCredential(AZURE_SEARCH_KEY)
)

# ====================================================================
#              SEARCH COMPONENTS DEFINITION
# ====================================================================

# --- A. Skillset ---
def get_skillset_definition():
    """Retorna el objeto SearchIndexerSkillset."""
    
    # 1. Definir los Skills usando las clases nativas
    skills_list = [
        # Document Extraction Skill
        SearchIndexerSkill(
            odatatype="#Microsoft.Skills.Util.DocumentExtractionSkill",
            name="documentExtraction",
            parsing_mode="default",
            data_to_extract="contentAndMetadata",
            context="/document",
            inputs=[{"name": "file_data", "source": "/document/file_data"}],
            outputs=[
                {"name": "content", "target_name": "extracted_text"},
                {"name": "metadata_storage_last_modified", "target_name": "last_updated_date"}
            ]
        ),
        # Split Skill (Chunking)
        SplitSkill(
            name="documentSplit",
            context="/document/extracted_text",
            text_split_mode="pages",
            maximum_page_length=500,
            page_overlap=50,
            inputs=[{"name": "text", "source": "/document/extracted_text"}],
            outputs=[{"name": "textItems", "target_name": "pages_of_chunks"}]
        ),
        # Azure OpenAI Embedding Skill
        AzureOpenAIEmbeddingSkill(
            name="vectorization",
            resource_uri=AZURE_OPENAI_ENDPOINT,
            deployment_id=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            context="/document/pages_of_chunks/*",
            inputs=[{"name": "text", "source": "/document/pages_of_chunks/*"}],
            outputs=[{"name": "embedding", "target_name": "vector_embedding"}]
        )
    ]
    
    # 2. Crear y retornar el objeto SkillSet
    return SearchIndexerSkillset(
        name=SKILLSET_NAME,
        description="Skills para extraer, dividir y vectorizar documentos para RAG.",
        skills=skills_list
    )

# --- B. Data Sources ---

def get_datasource_definition(name: str, folder_query: str):
    """Retorna el objeto DataSourceConnection."""
    
    return DataSourceConnection(
        name=name,
        type="azureblob",
        connection_string=AZURE_STORAGE_CONNECTION_STRING,
        container={"name": AZURE_STORAGE_BLOB_CONTAINER, "query": folder_query},
        data_change_detection_policy=HighWaterMarkChangeDetectionPolicy(
            high_water_mark_column_name="metadata_storage_last_modified"
        )
    )

# --- C. Indexers ---
def get_indexer_definition(name: str, datasource_name: str, target_index: str):
    """Retorna el objeto SearchIndexer."""

    # Mapeos de Campos
    field_mappings = [
        FieldMapping(source_field_name="metadata_storage_path", target_field_name="filepath"),
        FieldMapping(source_field_name="metadata_storage_name", target_field_name="source"),
        FieldMapping(source_field_name="metadata_storage_last_modified", target_field_name="lastUpdated"),
        FieldMapping(source_field_name="metadata_storage_path", target_field_name="id", mapping_function={"name": "base64Encode"})
    ]

    # Mapeos de Salida (Output Field Mappings)
    output_field_mappings = [
        OutputFieldMapping(
            source_field_name="/document/pages_of_chunks/*",
            target_field_name="chunks",
            mapping_mode="custom",
            content=[
                OutputFieldMapping(source_field_name="/document/pages_of_chunks/*/text", target_field_name="content"),
                OutputFieldMapping(source_field_name="/document/pages_of_chunks/*/vector_embedding", target_field_name="embedding"),
                OutputFieldMapping(source_field_name="metadata_storage_name", target_field_name="source_collection", mapping_function={"name": "base64Encode"})
            ]
        )
    ]
    
    # Parámetros
    params = IndexingParametersConfiguration(
        data_to_extract="contentAndMetadata",
        indexing_parameters=[{"name": "maxPageSize", "value": 4000}]
    )

    return SearchIndexer(
        name=name,
        data_source_name=datasource_name,
        skill_set_name=SKILLSET_NAME,
        target_index_name=target_index,
        parameters=params,
        field_mappings=field_mappings,
        output_field_mappings=output_field_mappings,
        schedule={"interval": "PT24H"}
    )

# ====================================================================
#              RESOURCES CREATORS
# ====================================================================

def create_search_resources():
    """Crea los Data Sources, el Skillset y los Indexers en orden correcto."""
    
    print(f"--- 1. Creando Skillset: {SKILLSET_NAME} ---")
    skillset_def = get_skillset_definition()
    #search_admin_client.create_or_update_skillset(skillset_name=SKILLSET_NAME, skillset=skillset_def)
    search_admin_client.create_or_update_skillset(skillset=skillset_def)
    print("Skillset creado/actualizado exitosamente.")

    print("\n--- 2. Creando Data Sources ---")
    # Data Source Histórico
    '''ds_historic_def = get_datasource_definition(DATASOURCE_HISTORIC, "historic/")
    search_admin_client.create_or_update_data_source(ds_historic_def)
    print(f"Data Source: {DATASOURCE_HISTORIC} (Historic) creado.")'''

    # Data Source Histórico
    ds_historic_def = get_datasource_definition(DATASOURCE_HISTORIC, "historic/")
    
    # CAMBIO CRÍTICO: Pasamos el diccionario directamente como argumento.
    # El SDK lo aceptará como diccionario JSON aunque espere la clase.
    search_admin_client.create_or_update_data_source_connection(
        data_source_connection=ds_historic_def # <--- ds_historic_def es un diccionario (dict)
    )
    print(f"Data Source: {DATASOURCE_HISTORIC} (Historic) creado.")

    # Data Source Actual
    ds_current_def = get_datasource_definition(DATASOURCE_CURRENT, "current/")
    
    # CAMBIO CRÍTICO (Igual que arriba)
    search_admin_client.create_or_update_data_source_connection(
        data_source_connection=ds_current_def
    )
    print(f"Data Source: {DATASOURCE_CURRENT} (Current) creado.")    

    # Data Source Actual
    ds_current_def = get_datasource_definition(DATASOURCE_CURRENT, "current/")
    search_admin_client.create_or_update_data_source(ds_current_def)
    print(f"Data Source: {DATASOURCE_CURRENT} (Current) creado.")

    print("\n--- 3. Creando Indexers ---")
    # Indexer 1 (Histórico) -> rag-index-1
    indexer_historic_def = get_indexer_definition(INDEXER_HISTORIC, DATASOURCE_HISTORIC, INDEX_NAMES[0])
    search_admin_client.create_or_update_indexer(indexer_historic_def)
    print(f"Indexer: {INDEXER_HISTORIC} creado. (Comienza la ingesta en {INDEX_NAMES[0]})")
    
    # Indexer 2 (Actual) -> rag-index-2
    indexer_current_def = get_indexer_definition(INDEXER_CURRENT, DATASOURCE_CURRENT, INDEX_NAMES[1])
    search_admin_client.create_or_update_indexer(indexer_current_def)
    print(f"Indexer: {INDEXER_CURRENT} creado. (Comienza la ingesta en {INDEX_NAMES[1]})")

    print("\n✅ Implementación de Ingesta Finalizada.")

# ====================================================================
#              PARALLEL SEARCH AND FUSION FUNCTION
# ====================================================================

async def search_index_async(index_name: str, query_text: str, top: int = 4):
    """Ejecuta una búsqueda híbrida asíncrona en un solo índice."""
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=index_name,
        credential=AzureKeyCredential(AZURE_SEARCH_KEY)
    )
    
    # Parámetros para búsqueda híbrida
    results = await search_client.search(
        search_text=query_text, 
        query_type="semantic", # Asume que el índice tiene Semantic Search configurado
        select=["content", "source"],
        top=top, # Pide los top 'n' de cada índice
        include_total_count=True,
        vector_queries=[], # Si estuvieras generando el vector aquí, lo pasarías
        # Aquí puedes agregar el filtro OData si fuera necesario, pero no lo es con la segmentación por carpeta
        # filter=None 
    )
    return [{"@search.score": r["@search.score"], "content": r["content"], "source": r["source"]} async for r in results]


async def execute_fused_search(query_text: str, top_k_total: int = 8):
    """Ejecuta la búsqueda paralela, fusiona los resultados y re-rankea."""
    
    print(f"\n--- Ejecutando búsqueda paralela para: '{query_text}' ---")
    
    # 1. Ejecución Asíncrona de Tareas
    tasks = [
        search_index_async(INDEX_NAMES[0], query_text, top=top_k_total), # Histórico
        search_index_async(INDEX_NAMES[1], query_text, top=top_k_total)  # Actual
    ]
    
    # results_historic y results_current se obtienen en paralelo
    results_historic, results_current = await asyncio.gather(*tasks)

    # 2. Fusión y Re-ranking
    all_results = results_historic + results_current
    
    # 3. Clasificación por Score (@search.score)
    final_ranked_chunks = sorted(
        all_results, 
        key=lambda r: r['@search.score'], 
        reverse=True
    )
    
    # 4. Selección del Top K total
    top_k_context = final_ranked_chunks[:top_k_total]
    
    print(f"Resultados recuperados (Total: {len(all_results)}, Top {top_k_total} fusionados):")
    for i, chunk in enumerate(top_k_context):
        print(f"  {i+1}. Score: {chunk['@search.score']:.4f} | Source: {chunk['source']}")

    return top_k_context


if __name__ == "__main__":
    # --- Parte 1: Implementación de la Infraestructura ---
    create_search_resources()

    # --- Parte 2: Ejemplo de Búsqueda ---
    # Es necesario que la parte 1 haya terminado y que los documentos se hayan vectorizado.
    
    # Nota: El cliente de búsqueda asíncrono necesita un loop de eventos.
    # asyncio.run(execute_fused_search("¿Cuál es la política de vacaciones para 2024?"))
    pass