# Propuesta Tecnológica

## 1. Plataforma / Proveedor

* Microsoft Azure

## 2. Recursos

### 2.1 Azure AI Foundry

* Workspace para gestionar modelos (GPT-4.1, GPT-4o).
* Experimentos de prompt engineering.
* Monitoreo de uso de tokens.

### 2.2 Azure AI Search

* Indexador de documentos en inglés (US).
* Configuración de cognitive skills para traducción automática a español (MX) y francés (CA).
* Embeddings multilingües para RAG.

### 2.3 Azure AI Content Safety (seguridad y cumplimiento)

* Filtrado de contenido: detecta y toma medidas en categorías específicas de contenido potencialmente perjudicial tanto en solicitudes de entrada como en finalizaciones de salida.
* Categorías personalizadas: permite crear y administrar categorías propias de contenido para mejorar la moderación y el filtrado para que coincidan con las directivas específicas o los casos de uso.
* Protección a instrucciones: detecta y bloquea ataques de entrada de usuario adversarios en LLMs.
* Detección de la base de datos: ayuda a garantizar que las respuestas de un LLM se basen en el material de origen proporcionado, lo que reduce el riesgo de resultados no fácticos o fabricados.
* Detección de material protegido: detección de material protegido examinan la salida de los LLMs para identificar y marcar material protegido conocido

### 2.3 Azure Cognitive Service Speech

* STT (Speech-to-Text): inglés, español, francés.
* TTS (Text-to-Speech): voces naturales (ej. en-US-JennyNeural, es-MX-DaliaNeural, fr-CA-SylvieNeural).

### 2.4 Azure Translator

* Para normalizar traducciones si se decide mantener corpus en inglés y traducir dinámicamente.

### 2.5 Azure App Service 

* Backend ligero con endpoints REST.
* Escalabilidad automática.
* Fácil integración con Semantic Kernel.

### 2.6 Azure Storage

* Almacén de documentos fuente (PDF, DOCX, Markdown).
* Disponer de carpetas organizadas por idioma.

### 2.7 Aplication Insights

* Telemetría: latencia, errores, métricas de accesibilidad (ej. uso de subtítulos vs TTS).
* Consultas a través de **consultas Kusto(KQL)**
* Panel y widgets:
  * Métricas → (Server response time, Request, Faiulures).
  * Logs (Analíticas) → consulta personalizadas con KQL.
  * Dependencias → para ver tiempos de OpenAI, Base de Datos.
  * Usuarios → para ver sesiones activas.

## 3. Lenguajes de programación, librerías, extensiones y marcos de trabajo
  * Flask/Quart
  * HTMX
  * Vanilla JavaScript y AlpineJS
  * Tailwind 
  * Semantic Kernel, Microsoft Agent Framework
  * Extensiones:
    * Ruff

## 4. Esqueleto del Repositorio

```
knit/
│
├── .github/                    # Configuración
│   └── workflows/              # Colección de flujos de trabajo
│       └── flow1.yml           # Flujo de trabajo
│
├── backend/                    # API y orquestación
│   ├── main/                   # Componente/Endpoint central
│   │   ├── _init_.py           # Configuración de blueprint
│   │   ├── route.py            # Definición de endpoints asociados
│   │   └── controller.py       # Funciones de endpoints
│   │
│   ├── auth/                   # Componente/Endpoint autenticación
│   │   ├── _init_.py           # Configuración de blueprint
│   │   ├── route.py            # Definición endpoints asociados
│   │   ├── controller.py       # Funciones de endpoints
│   │   ├── forms.py            # Definición de formulario
│   │   ├── model.py            # Definición del modelo de base de datos
│   │   └── services.py         # Clases/funciones de servicios/ayudadores asociados al endpoint
│   │
│   ├── app.py                  # Inicializador y configuración de aplicación
│   ├── .gitignore              # Lista de archivos o directorios que se deben ignorar y no rastrear en el repositorio
│   ├── helpers.py              # Funciones de ayuda de ámbito general
│   ├── set-env.sh              # Elimina variables de entorno (se ignora archivo en el repositorio)
│   ├── requirements.txt        # Dependencias (semantic-kernel, azure-ai, etc.)
│   ├── set-env.sh              # Establece variables de entorno (se ignora archivo en el repositorio)
│   └── tests/                  # Colección de pruebas unitarias
│
├── frontend/                   # Interfaz de la aplicación
│   ├── layout.html             # Plantilla de disposición general
│   ├── _forms.html             # Definición macros para formularios
│   ├── toast/                  # Componente notificaciones no intrusivas
│   │   ├── top-message.html    # Plantilla de mensaje de arriba
│   │   └── bottom-message.html # Plantilla de mensaje de abajo
│   │
│   ├── header/                 # Componente cabecera
│   │   ├── index.html          # Plantilla de cabecera
│   │   └── partials/           # Parciales de cabecera
│   │       └── head-1.html     # Plantilla de título 1
│   │
│   ├── components/             # Botón TTS, subtítulos, accesibilidad * Valorar que tan atómicas serán las plantillas
│   └── public/                 # Recursos globales
│       ├── js/                 # Código JavaScript
│       ├── img/                # Imágenes
│       └── css/                # Hojas de estilo
│
├── infra/                    # Infraestructura como código
│   ├── bicep o scripts/      # Plantillas Bicep/Az para Azure
│   ├── pipelines/            # GitHub Actions / Azure DevOps (opcional)
│   └── config/               # Variables de entorno 
│
├── docs/                     # Documentación
│   ├── english/              # Colección en inglés
│   ├── spanish/              # Colección en español
│   ├── architecture.md       # Diagrama y explicación
│   ├── accessibility.md      # Checklist de accesibilidad
│   └── usage.md              # Cómo correr el proyecto
│
└── README.md                 # Presentación / Guía rápida
```
