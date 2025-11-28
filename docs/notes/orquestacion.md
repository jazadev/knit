# Orquestación para Chat Knit (CK)

## Componentes

* Python Quart → Framework ligero para servicios web asíncronos, ideal para prototipos de agentes.
* Microsoft Agent Framework → Capacidad de definir agentes especializados y orquestadores dentro de Azure AI Foundry.
* Webscraper → Script para obetener información oficial generada día a día.
* Convertidor y destilador - Script que convierte documentos PDF a markdown y destila aquellos que requieren mayor esfuerzo y generan mayor impacto financiero. 
* AI Search (RAG) → Nuestra base de conocimiento indexada, que permite búsquedas semánticas y recuperación aumentada con generación.
* Grounding con Bing Search → Canal para traer información pública y fresca del día a día.


## Flujo de decisión  
La idea es tener un agente orquestador que decida a quién poner a trabajer y de que manera:

* Agente RAG (cuando la información está en tu base privada/indexada), o
* Agente Bing (cuando necesitas datos nuevos o externos)
* Una herramienta de que facilita el procesamiento de respuestas para el Agente RAG y Bing.

📌 Se ajusta a la filosofía del Agent Framework, en donde:

* El orquestador actúa como “router” de la intención.
* Los agentes especialistas se encargan de ejecutar la tarea en su dominio (RAG o Bing).
* El resultado se devuelve al orquestador, que lo integra y responde al usuario.

##  Matices importantes
* No se necesita que el orquestador sea un agente “pesado”: puede ser una policy o router agent que clasifica la intención.
* El agente de RAG y el de Bing pueden ser sub-agentes dentro del mismo framework, no necesariamente servicios separados.
* En escenarios más complejos, se puede incluso fusionar resultados: primero consultar RAG y, si no hay suficiente confianza, complementar con Bing. (Ver casos de uso)
* Microsoft recomienda este patrón como multi-agent orchestration, donde cada agente tiene un rol claro y el orquestador decide la ruta.

## Arquitectura de alto nivel

```code
                ┌────────────────────────────┐
                │       Usuario final        │
                │ (consulta vía Python Quart)│
                └─────────────┬──────────────┘
                              │
                              ▼
                ┌────────────────────────────┐
                │   Agente Orquestador       │
                │ (Microsoft Agent Framework)│
                └─────────────┬──────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          │                                       │
          ▼                                       ▼
┌───────────────────────────┐         ┌─────────────────────────────┐
│   Agente Especialista RAG │         │   Agente Especialista Bing  │
│ (Azure AI Search + Foundry│         │ (Grounding with Bing Search)│
│   + tu base de datos)     │         │   Datos públicos frescos    │
└─────────────┬─────────────┘         └──────────────┬──────────────┘
              │                                      │
              ▼                                      ▼
   ┌───────────────────────┐             ┌────────────────────────┐
   │   Respuesta generada  │             │   Respuesta generada   │
   │   con contexto RAG    │             │   con datos actuales   │
   └─────────────┬─────────┘             └─────────────┬──────────┘
                 │                                     │
                 └──────────────────┬──────────────────┘
                                    ▼
                      ┌───────────────────────────┐
                      │   Agente Orquestador      │
                      │   (fusiona resultados)    │
                      └─────────────┬─────────────┘
                                    │
                                    ▼
                       ┌───────────────────────────┐
                       │  Usuario recibe respuesta │
                       └───────────────────────────┘
```

## Puntos clave del diseño

* Orquestador: decide si la consulta se resuelve con RAG (información interna) o con Bing (información pública y fresca).
* Agente RAG: usa Azure AI Search para recuperar documentos indexados y enriquecer la respuesta con tu conocimiento privado.
* Agente Bing: usa Grounding with Bing Search para traer información actualizada del día a día.
* Fusión de resultados: el orquestador puede combinar ambos si la confianza del RAG es baja o si la consulta requiere contexto mixto.
