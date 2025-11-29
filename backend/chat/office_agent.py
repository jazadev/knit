"""
Office Agent - Agente conversacional con acceso a información vectorizada
Instalación: pip install semantic-kernel psycopg2-binary openai azure-identity
"""

import asyncio
from typing import List, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import psycopg2
from psycopg2.extras import RealDictCursor
import openai
import os
import json

# Configuración
COSMOS_CONNECTION_STRING = os.getenv("COSMOS_CONNECTION_STRING")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = "gpt-4"
AZURE_EMBEDDING_DEPLOYMENT = "text-embedding-ada-002"

@dataclass
class Message:
    """Representa un mensaje en la conversación"""

    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class DocumentAccess:
    """Registra el acceso a un documento"""

    document_id: str
    timestamp: datetime
    query: str
    similarity: float
    metadata: Dict = field(default_factory=dict)


class MetricsCollector:
    """Recolector de métricas de uso de documentos"""
    
    def __init__(self):
        self.accesos: List[DocumentAccess] = []
        self.queries_totales = 0
        self.queries_con_resultados = 0
        self.queries_sin_resultados = 0
    
    def registrar_busqueda(self, query: str, documentos: List[Dict]):
        """Registra una búsqueda y sus resultados"""

        self.queries_totales += 1
        
        if documentos:
            self.queries_con_resultados += 1
            for doc in documentos:
                self.accesos.append(DocumentAccess(
                    document_id=doc['id'],
                    timestamp=datetime.now(),
                    query=query,
                    similarity=doc['similarity'],
                    metadata=doc.get('metadata', {})
                ))
        else:
            self.queries_sin_resultados += 1
    
    def get_documentos_mas_accedidos(self, top_n: int = 10) -> List[tuple]:
        """Obtiene los documentos más accedidos"""
        contador = Counter([acceso.document_id for acceso in self.accesos])
        return contador.most_common(top_n)
    
    def get_queries_populares(self, top_n: int = 10) -> List[tuple]:
        """Obtiene las queries más frecuentes"""        
        contador = Counter([acceso.query for acceso in self.accesos])
        return contador.most_common(top_n)
    
    def get_estadisticas_por_periodo(self, dias: int = 7) -> Dict:
        """Estadísticas de los últimos N días"""
        fecha_limite = datetime.now() - timedelta(days=dias)
        accesos_periodo = [a for a in self.accesos if a.timestamp >= fecha_limite]
        
        return {
            'total_accesos': len(accesos_periodo),
            'documentos_unicos': len(set(a.document_id for a in accesos_periodo)),
            'similarity_promedio': sum(a.similarity for a in accesos_periodo) / len(accesos_periodo) if accesos_periodo else 0,
            'accesos_por_dia': len(accesos_periodo) / dias if dias > 0 else 0
        }
    
    def get_metricas_por_metadata(self, campo: str) -> Dict:
        """Agrupa métricas por un campo de metadata"""
        metricas = defaultdict(int)
        for acceso in self.accesos:
            valor = acceso.metadata.get(campo, 'Sin categoría')
            metricas[valor] += 1
        return dict(metricas)
    
    def exportar_metricas(self) -> Dict:
        """Exporta todas las métricas en formato JSON"""
        return {
            'resumen': {
                'queries_totales': self.queries_totales,
                'queries_exitosas': self.queries_con_resultados,
                'queries_sin_resultados': self.queries_sin_resultados,
                'tasa_exito': f"{(self.queries_con_resultados/self.queries_totales*100):.1f}%" if self.queries_totales > 0 else "0%",
                'total_accesos_documentos': len(self.accesos)
            },
            'top_documentos': self.get_documentos_mas_accedidos(10),
            'top_queries': self.get_queries_populares(10),
            'ultimos_7_dias': self.get_estadisticas_por_periodo(7),
            'ultimos_30_dias': self.get_estadisticas_por_periodo(30)
        }
    
    def mostrar_reporte(self):
        """Muestra un reporte visual de las métricas"""
        print("\n" + "="*70)
        print("📊 REPORTE DE MÉTRICAS - USO DE DOCUMENTOS")
        print("="*70)
        
        # Resumen general
        print("\n📈 RESUMEN GENERAL")
        print("-" * 70)
        print(f"Total de búsquedas realizadas: {self.queries_totales}")
        print(f"  ✓ Con resultados: {self.queries_con_resultados}")
        print(f"  ✗ Sin resultados: {self.queries_sin_resultados}")
        if self.queries_totales > 0:
            tasa = (self.queries_con_resultados / self.queries_totales) * 100
            print(f"  Tasa de éxito: {tasa:.1f}%")
        print(f"Total de accesos a documentos: {len(self.accesos)}")
        
        # Documentos más accedidos
        print("\n🔥 TOP 10 DOCUMENTOS MÁS ACCEDIDOS")
        print("-" * 70)
        top_docs = self.get_documentos_mas_accedidos(10)
        for i, (doc_id, count) in enumerate(top_docs, 1):
            barra = "█" * (count // max(1, max(c for _, c in top_docs) // 20))
            print(f"{i:2d}. {doc_id[:50]:<50} {count:4d} {barra}")
        
        # Queries más populares
        print("\n🔍 TOP 10 PREGUNTAS MÁS FRECUENTES")
        print("-" * 70)
        top_queries = self.get_queries_populares(10)
        for i, (query, count) in enumerate(top_queries, 1):
            print(f"{i:2d}. [{count:2d}x] {query[:60]}")
        
        # Estadísticas por período
        print("\n📅 ESTADÍSTICAS POR PERÍODO")
        print("-" * 70)
        stats_7d = self.get_estadisticas_por_periodo(7)
        stats_30d = self.get_estadisticas_por_periodo(30)
        
        print("Últimos 7 días:")
        print(f"  • Accesos totales: {stats_7d['total_accesos']}")
        print(f"  • Documentos únicos: {stats_7d['documentos_unicos']}")
        print(f"  • Promedio diario: {stats_7d['accesos_por_dia']:.1f}")
        print(f"  • Similarity promedio: {stats_7d['similarity_promedio']:.2%}")
        
        print("\nÚltimos 30 días:")
        print(f"  • Accesos totales: {stats_30d['total_accesos']}")
        print(f"  • Documentos únicos: {stats_30d['documentos_unicos']}")
        print(f"  • Promedio diario: {stats_30d['accesos_por_dia']:.1f}")
        print(f"  • Similarity promedio: {stats_30d['similarity_promedio']:.2%}")
        
        # Métricas por categoría (si existe metadata)
        if self.accesos and 'categoria' in self.accesos[0].metadata:
            print("\n📑 ACCESOS POR CATEGORÍA")
            print("-" * 70)
            metricas_cat = self.get_metricas_por_metadata('categoria')
            for categoria, count in sorted(metricas_cat.items(), key=lambda x: x[1], reverse=True):
                print(f"  {categoria}: {count}")
        
        print("\n" + "="*70 + "\n")


class OfficeAgent:
    """
    Agente conversacional con acceso a información vectorizada en Cosmos DB.
    Puede responder preguntas generales Y consultar documentos vectorizados cuando sea relevante.
    """
    
    def __init__(self):
        self.conversation_history: List[Message] = []
        self.conn = None
        self.openai_client = None
        self.agent_name = "Office Agent"
        self.metrics = MetricsCollector()  # Sistema de métricas
        
        # Sistema de prompt del agente
        self.system_prompt = f"""Eres {self.agent_name}, un asistente inteligente de oficina especializado en temas del gobierno de la ciudad de méxico.

CAPACIDADES:
- Responder preguntas generales de forma conversacional, neutra y amigable
- Acceder a documentos internos vectorizados cuando sea relevante
- Combinar tu conocimiento general con información específica de la gaceta de la ciudad de mexico
- Responder sin recomendaciones de indole politico, racial, de genero, religioso o clacista

INSTRUCCIONES:
1. Si la pregunta es general (saludos, conversación, conocimiento común), responde directamente
2. Si la pregunta requiere información específica de documentos/políticas/procedimientos internos, 
   convocatorias, tramites, proyectos inciativas PRIMERO busca en la base vectorizada
3. Siempre indica cuando estás usando información de documentos internos
4. Sé conversacional, claro y útil
5. Si no encuentras información relevante en los documentos, responde con tu conocimiento general 
   pero menciona que no encontraste documentación específica

Fecha actual: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    async def initialize(self):
        """Inicializa conexiones a Cosmos DB y Azure OpenAI"""
        ### Necesito adecuarme a la estrucura del proyecto de Ana!!
        
        #print(f"🚀 Inicializando {self.agent_name}...")
        
        # Conexión a Cosmos DB
        try:
            self.conn = psycopg2.connect(
                COSMOS_CONNECTION_STRING,
                cursor_factory=RealDictCursor
            )
            print("✓ Conectado a Cosmos DB")
        except Exception as e:
            print(f"✗ Error conectando a Cosmos DB: {e}")
            raise
        
        # Cliente de OpenAI
        self.openai_client = openai.AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-02-01",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        print("✓ Cliente Azure OpenAI configurado")
        
        print(f"✓ {self.agent_name} listo para conversar\n")
    
    def _generar_embedding(self, texto: str) -> List[float]:
        """Genera embedding para un texto usando Azure OpenAI"""
        
        try:
            response = self.openai_client.embeddings.create(
                input=texto,
                model=AZURE_EMBEDDING_DEPLOYMENT
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generando embedding: {e}")
            return None
    
    def _buscar_documentos_relevantes(self, query: str, limit: int = 3, threshold: float = 0.75) -> List[Dict]:
        """
        Busca documentos vectorizados relevantes para la consulta
        
        Args:
            query: Pregunta o texto a buscar
            limit: Número máximo de resultados
            threshold: Umbral de similitud (0-1, mayor = más estricto)
        
        Returns:
            Lista de documentos relevantes con su contenido y metadata
        """
        
        # Generar embedding de la query
        query_embedding = self._generar_embedding(query)
        if not query_embedding:
            return []
        
        # Convertir a formato compatible con pgvector
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        try:
            cur = self.conn.cursor()
            
            # Buscar documentos similares usando cosine similarity
            # Nota: Ajusta los nombres de columnas según tu esquema
            cur.execute("""
                SELECT 
                    id,
                    content,
                    metadata,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM documents
                WHERE 1 - (embedding <=> %s::vector) > %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (embedding_str, embedding_str, threshold, embedding_str, limit))
            
            results = cur.fetchall()
            cur.close()
            
            documents = []
            for row in results:
                documents.append({
                    'id': row['id'],
                    'content': row['content'],
                    'metadata': row.get('metadata', {}),
                    'similarity': float(row['similarity'])
                })
            
            return documents
            
        except Exception as e:
            print(f"Error buscando documentos: {e}")
            return []
    
    def _necesita_busqueda_vectorial(self, mensaje: str) -> bool:
        """
        Determina si el mensaje requiere búsqueda en documentos vectorizados
        Usa keywords y contexto para decidir
        """
        
        # Keywords que sugieren búsqueda de documentos internos
        keywords_internos = [
            'política', 'procedimiento', 'documento', 'manual', 'guía',
            'cómo hacer', 'proceso de', 'requisitos', 'normativa',
            'protocolo', 'reglamento', 'lineamiento', 'formato',
            'qué dice', 'según', 'dónde encuentro', 'información sobre',
            'licitación', 'concurso', 'organigrama', 'alcaldia'
        ]
        
        mensaje_lower = mensaje.lower()
        
        # Si contiene keywords específicos, definitivamente buscar
        if any(keyword in mensaje_lower for keyword in keywords_internos):
            return True
        
        # Si es una pregunta de procedimiento o información específica
        palabras_pregunta = ['cómo', 'cuál', 'dónde', 'qué', 'quién', 'cuándo', 'cuánto']
        if any(palabra in mensaje_lower for palabra in palabras_pregunta):
            # Evitar preguntas muy generales
            preguntas_generales = ['cómo estás', 'qué tal', 'cómo te llamas']
            if not any(pg in mensaje_lower for pg in preguntas_generales):
                return True
        
        return False
    
    async def procesar_mensaje(self, mensaje_usuario: str) -> str:
        """
        Procesa un mensaje del usuario y genera respuesta
        
        Flujo:
        1. Determina si necesita buscar en documentos vectorizados
        2. Si es necesario, busca documentos relevantes
        3. Construye contexto con documentos encontrados
        4. Genera respuesta usando GPT con todo el contexto
        """
        
        ### ******** AADAPTARLO CON EL DE ANA
        ##print(f"\n💬 Usuario: {mensaje_usuario}")
        
        # Agregar mensaje del usuario al historial
        self.conversation_history.append(Message(role="user", content=mensaje_usuario))
        
        # Determinar si necesita búsqueda vectorial
        necesita_busqueda = self._necesita_busqueda_vectorial(mensaje_usuario)
        
        contexto_documentos = ""
        documentos_encontrados = []
        
        if necesita_busqueda:
            #print("🔍 Buscando en documentos vectorizados...")
            documentos_encontrados = self._buscar_documentos_relevantes(mensaje_usuario, limit=3)
            
            # Registrar métricas de búsqueda
            self.metrics.registrar_busqueda(mensaje_usuario, documentos_encontrados)
            
            if documentos_encontrados:
                #print(f"✓ Encontrados {len(documentos_encontrados)} documentos relevantes")
                
                # Construir contexto con documentos
                contexto_partes = ["\n--- INFORMACIÓN DE DOCUMENTOS INTERNOS ---"]
                for i, doc in enumerate(documentos_encontrados, 1):
                    metadata_info = ""
                    if doc['metadata']:
                        metadata_info = f" (Fuente: {doc['metadata'].get('source', 'N/A')})"
                    
                    contexto_partes.append(
                        f"\nDocumento {i}{metadata_info} [Relevancia: {doc['similarity']:.2%}]:\n{doc['content']}"
                    )
                
                contexto_partes.append("\n--- FIN DE DOCUMENTOS ---\n")
                contexto_documentos = "\n".join(contexto_partes)
            else:
                pass
                #print("ℹ️  No se encontraron documentos relevantes")
        
        # Construir mensajes para la API
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Agregar contexto de documentos si existe
        if contexto_documentos:
            messages.append({
                "role": "system",
                "content": contexto_documentos
            })
        
        # Agregar historial de conversación (últimos 10 mensajes)
        for msg in self.conversation_history[-10:]:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Generar respuesta
        #print("💭 Generando respuesta...")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            respuesta = response.choices[0].message.content
            
            # Agregar respuesta al historial
            self.conversation_history.append(Message(role="assistant", content=respuesta))
            
            return respuesta
            
        except Exception as e:
            ## Esta va a costar trabajo capturalo , mmm....
            error_msg = f"Lo siento, ocurrió un error al procesar tu mensaje: {e}"
            #print(f"✗ Error: {e}")
            return error_msg
    
    def limpiar_historial(self):
        """Limpia el historial de conversación"""
        self.conversation_history = []
        #print("🗑️  Historial de conversación limpiado")
    
    def mostrar_historial(self):
        """Muestra el historial de conversación"""
        print("\n" + "="*60)
        print("HISTORIAL DE CONVERSACIÓN")
        print("="*60)
        for msg in self.conversation_history:
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            print(f"[{timestamp}] {msg.role.upper()}: {msg.content[:100]}...")
        print("="*60 + "\n")
    
    def guardar_metricas(self, archivo: str = "metricas_office_agent.json"):
        """Guarda las métricas en un archivo JSON"""
        try:
            metricas = self.metrics.exportar_metricas()
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(metricas, f, indent=2, ensure_ascii=False, default=str)
            print(f"✓ Métricas guardadas en {archivo}")
        except Exception as e:
            print(f"✗ Error guardando métricas: {e}")
    
    def cargar_metricas(self, archivo: str = "metricas_office_agent.json"):
        """Carga métricas desde un archivo JSON"""
        try:
            if os.path.exists(archivo):
                with open(archivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✓ Métricas cargadas desde {archivo}")
                return data
            else:
                print(f"ℹ️  No se encontró archivo de métricas: {archivo}")
                return None
        except Exception as e:
            print(f"✗ Error cargando métricas: {e}")
            return None
    
    def close(self):
        """Cierra conexiones"""
        if self.conn:
            self.conn.close()
            #print("✓ Conexiones cerradas")


async def main():
    """Ejemplo de uso del Office Agent"""
    
    # Inicializar agente
    agent = OfficeAgent()
    await agent.initialize()
    
    print("="*60)
    print(f"  {agent.agent_name} - Chat Interactivo")
    print("="*60)
    print("Comandos especiales:")
    print("  /historial - Ver historial de conversación")
    print("  /metricas  - Ver métricas de uso de documentos")
    print("  /guardar   - Guardar métricas en archivo JSON")
    print("  /limpiar   - Limpiar historial")
    print("  /salir     - Salir del chat")
    print("="*60 + "\n")
    
    # Ejemplos de conversación
    ejemplos = [
        "Hola, ¿cómo estás?",
        "¿Cuál es el procedimiento para solicitar vacaciones?",
        "¿Qué documentos necesito para un reembolso de gastos?",
    ]
    
    print("📝 Ejecutando ejemplos de conversación...\n")
    for ejemplo in ejemplos:
        respuesta = await agent.procesar_mensaje(ejemplo)
        print(f"\n🤖 {agent.agent_name}: {respuesta}\n")
        print("-"*60)
        await asyncio.sleep(1)
    
    # Modo interactivo
    print("\n💬 Ahora puedes chatear libremente (escribe /salir para terminar)\n")
    
    while True:
        try:
            mensaje = input("Tú: ").strip()
            
            if not mensaje:
                continue
            
            # Comandos especiales
            if mensaje.lower() == '/salir':
                print(f"\n👋 ¡Hasta luego! Gracias por usar {agent.agent_name}")
                # Mostrar métricas finales
                agent.metrics.mostrar_reporte()
                agent.guardar_metricas()
                break
            elif mensaje.lower() == '/historial':
                agent.mostrar_historial()
                continue
            elif mensaje.lower() == '/metricas':
                agent.metrics.mostrar_reporte()
                continue
            elif mensaje.lower() == '/guardar':
                agent.guardar_metricas()
                continue
            elif mensaje.lower() == '/limpiar':
                agent.limpiar_historial()
                continue
            
            # Procesar mensaje
            respuesta = await agent.procesar_mensaje(mensaje)
            print(f"\n🤖 {agent.agent_name}: {respuesta}\n")
            
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
    
    # Cerrar conexiones
    agent.close()


# Ejemplo simple de uso programático (sin modo interactivo)
async def ejemplo_simple():
    """Uso simple del agente sin modo interactivo"""
    
    agent = OfficeAgent()
    await agent.initialize()
    
    # Hacer una pregunta
    respuesta = await agent.procesar_mensaje(
        "¿Cuál es el proceso para reportar un incidente de seguridad?"
    )
    print(f"\nRespuesta: {respuesta}")
    
    # Otra pregunta (mantiene contexto)
    respuesta = await agent.procesar_mensaje(
        "¿Y cuánto tiempo tengo para reportarlo?"
    )
    print(f"\nRespuesta: {respuesta}")
    
    agent.close()
