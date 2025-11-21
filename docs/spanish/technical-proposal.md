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
│   │   ├── __init__.py         # Configuración de blueprint
│   │   ├── route.py            # Definición de endpoints
│   │   └── controller.py       # Lógica de inicio aplicación
│   │
│   ├── auth/                   # Autenticación Microsoft
│   │   ├── __init__.py         # Configuración de blueprint
│   │   ├── route.py            # Definición endpoints
│   │   ├── controller.py       # Lógica de autenticación
│   │   ├── forms.py            # Definición de formulario
│   │   ├── model.py            # Definición del modelo de base de datos
│   │   └── services.py         # Clases/funciones de servicios/auxiliares
│   │
│   ├── chat/                   # Chat conversacional
│   │   ├── __init__.py         # Configuración de blueprint
│   │   ├── route.py            # Definición de endpoints
│   │   └── controller.py       # Lógica de chat
│   │
│   ├── database/               # Capa de Datos
│   │   ├── __init__.py
│   │   ├── connection.py       # Cosmo DB connection
│   │   ├── models.py           # Todos los modelos
│   │   ├── migrations/         # Migrations
│   │   └── seed_data.py        # Datos iniciales
│   │
│   ├── app.py                  # Inicializador Flask
│   ├── config.py               # Configuración de entorno
│   ├── .gitignore              # Lista de archivos o directorios que se deben ignorar y no rastrear en el repositorio
│   ├── helpers.py              # Funciones auxiliares globales
│   ├── set-env.sh              # Elimina variables de entorno (en .gitignore)
│   ├── requirements.txt        # Dependencias de Python
│   ├── set-env.sh              # Establece variables de entorno (en .gitignore)
│   └── tests/                  # Colección de pruebas
│       ├── test_agents.py
│       ├── test_auth.py
│       └── test_chat.py
│
├── frontend/                            # Interfaz de aplicación
│   ├── templates/
│   │   ├── layout.html                  # Plantilla base
│   │   ├── _forms.html                  # Definición macros para formularios
│   │   │
│   │   ├── auth/
│   │   │   ├── login.html               # Plantilla de inicio de sesión
│   │   │   └── callback.html            # Plantilla devolución de llamada
│   │   │
│   │   ├── header/                      # Componente cabecera
│   │   │   ├── index.html               # Plantilla de cabecera
│   │   │   └── partials/                # Parciales de cabecera
│   │   │       └── head-1.html          # Plantilla de título 1
│   │   │
│   │   ├── sidebar/                     # Componente barra lateral
│   │   │   ├── index.html               # Plantilla de barra lateral
│   │   │   └── partials/                # Parciales de barra lateral
│   │   │       ├── header.html          # Plantilla cabecera
│   │   │       ├── body.html            # Plantilla cuerpo
│   │   │       └── footer.html          # Plantilla pie
│   │   │
│   │   ├── notification/                # Componente notificación
│   │   │   ├── index.html               # Plantilla notificación
│   │   │   └── partials/                # Parciales de notificación
│   │   │       ├── header.html          # Plantilla cabecera
│   │   │       ├── body.html            # Plantilla cuerpo
│   │   │       ├── footer.html          # Plantilla pie
│   │   │       └── card.html            # Plantilla tarjeta
│   │   │
│   │   ├── settings/                    # Componente ajustes
│   │   │   ├── index.html               # Plantilla ajustes
│   │   │   └── partials/                # Parciales de ajustes
│   │   │       ├── header.html          # Plantilla cabecera
│   │   │       ├── body.html            # Plantilla cuerpo
│   │   │       ├── footer.html          # Plantilla pie
│   │   │       ├── personal-data.html   # Plantilla datos personales
│   │   │       ├── channels.html        # Plantilla canales
│   │   │       └── interest.html        # Plantilla intereses
│   │   │
│   │   ├── components/                  # Colección de componentes
│   │   │   ├── toast/                   # Componente notificación
│   │   │   │   └── index.html           # Plantilla notificación
│   │   │   └── buttons/                 # Componentes botón
│   │   │       ├── hamburger-menu.html  # Plantilla menú hamburgesa
│   │   │       ├── zoom-in-out.html     # Plantilla acercar / alejar
│   │   │       ├── language.html        # Plantilla lenguaje
│   │   │       └── hamburger-menu.html  # Plantilla notificación
│   │   │
│   │   └── errors/
│   │       ├── 404.html
│   │       └── 500.html
│   │   
│   └── public/                          # Recursos globales
│       ├── js/                          # Código JavaScript
│       │   ├── i18n.js                  # Cliente de traducción
│       │   └── knit.js                  # Script adicionales
│       ├── img/                         # Imágenes
│       │   ├── hamburger.svg            # Hamburgesa
│       │   └── logo.svg                 # Logotipo
│       └── css/                         # Hojas de estilo
│           └── knit.css                 # Estilos personalzados
│
├── infra/                               # Infraestructura como código
│   ├── bicep o scripts/                 # Plantillas Bicep/Az para Azure
│   ├── pipelines/                       # GitHub Actions / Azure DevOps (opcional)
│   └── config/                          # Variables de entorno 
│
├── docs/                                # Documentación
│   ├── english/                         # Colección en inglés
│   ├── spanish/                         # Colección en español
│   ├── architecture.md                  # Diagrama y explicación
│   ├── accessibility.md                 # Checklist de accesibilidad
│   └── usage.md                         # Cómo correr el proyecto
│
└── README.md                            # Presentación / Guía rápida
```
