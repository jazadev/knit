# Civic Knit - Asistente Cívico Inteligente

Plataforma de orientación ciudadana impulsada por Inteligencia Artificial, reconocimiento de voz y moderación de contenido en tiempo real.

Este proyecto opera bajo una arquitectura híbrida: el código fuente se ejecuta en el entorno local o en Azure App Service, mientras que los servicios cognitivos y de datos residen en la nube de Microsoft Azure.

---

## FASE 1: Aprovisionamiento de Infraestructura (Requisito Inicial)

Antes de iniciar la ejecución del código (tanto en desarrollo local como en producción), es mandatorio crear los servicios en Azure. Se utiliza Bicep para automatizar este proceso y garantizar la consistencia del entorno.

### 1. Inicio de sesión en Azure CLI
Se debe autenticar en la terminal:

```bash
az login
```

### 2. Obtención del ID de Usuario
Este identificador es necesario para asignar las políticas de acceso al Key Vault de manera correcta.

```bash
# En Bash / Mac:
MY_ID=$(az ad signed-in-user show --query id -o tsv)

# En PowerShell:
# $MY_ID = az ad signed-in-user show --query id -o tsv
```

### 3. Ejecución del script de despliegue (Bicep)
El siguiente comando creará los recursos: Azure OpenAI, Content Safety, Speech Services, Cosmos DB y Key Vault.

```bash
az group create -n rg-civicknit-prod -l eastus2

az deployment group create \
  --resource-group rg-civicknit-prod \
  --template-file civicknit-main.bicep \
  --parameters principalId=$MY_ID \
  --parameters appName=civicknit-prod
```

---

## FASE 2: Configuración del Entorno de Desarrollo Local

Una vez finalizado el despliegue de la infraestructura, se deben obtener las credenciales generadas en Azure para configurar el entorno local.

### 1. Clonación y preparación del entorno

```bash
git clone https://github.com/jazadev/knit
cd civicknit

# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configuración de Variables de Entorno (.env)
Se debe crear un archivo llamado `.env` en la raíz del proyecto. Este archivo contendrá las claves de acceso a los servicios creados en la FASE 1.

### 3. Obtención de Credenciales
Para completar el archivo `.env`, diríjase al Portal de Azure, ingrese al Grupo de Recursos `rg-civicknit-prod` y localice los valores en las secciones "Keys and Endpoint" (Claves y Punto de conexión) de cada recurso:

**A) Azure OpenAI (Recurso: civicknit-prod-openai):**
```ini
AZURE_OPENAI_ENDPOINT="<Copiar Endpoint>"
AZURE_OPENAI_KEY="<Copiar Key 1>"
AZURE_OPENAI_API_VERSION="2024-02-15-preview"
AZURE_DEPLOYMENT_NAME="gpt-4o"
```

**B) Azure Content Safety (Recurso: civicknit-prod-safety):**
```ini
AZURE_CONTENT_SAFETY_ENDPOINT="<Copiar Endpoint>"
AZURE_CONTENT_SAFETY_KEY="<Copiar Key 1>"
```

**C) Azure Speech (Recurso: civicknit-prod-speech):**
```ini
AZURE_SPEECH_REGION="eastus2"
AZURE_SPEECH_KEY="<Copiar Key 1>"
```

**D) Cosmos DB (Recurso: civicknit-prod-cosmos):**
```ini
AZURE_COSMOS_ENDPOINT="<Copiar URI>"
AZURE_COSMOS_KEY="<Copiar PRIMARY KEY>"
AZURE_COSMOS_DATABASE="CivicKnitDB"
AZURE_COSMOS_CONTAINER="CivicContainer"
```

**E) Autenticación (Microsoft Entra ID):**
En "App Registrations", crear un nuevo registro y obtener los siguientes valores:
```ini
CLIENT_ID="<Application (client) ID>"
CLIENT_SECRET="<Valor del secreto creado en Certificates & secrets>"
AUTHORITY="[https://login.microsoftonline.com/](https://login.microsoftonline.com/)<Directory (tenant) ID>"
SCOPE="User.Read"
```

### 4. Configuración de Redirección Local
En el recurso "App Registration" dentro del Portal de Azure, sección "Authentication", se debe agregar la siguiente URI para la plataforma Web:
`http://localhost:8000/getAToken`

### 5. Ejecución
Se utiliza Hypercorn como servidor web asíncrono:

```bash
python -m hypercorn run:app --bind 127.0.0.1:8000 --reload
```

La aplicación estará disponible en: `http://localhost:8000`

---

## FASE 3: Despliegue a Producción

La infraestructura base ya fue creada en la FASE 1. En esta etapa, se procede a desplegar el código fuente en el App Service y finalizar la configuración de seguridad.

### 1. Configuración de Autenticación en Producción
El script Bicep automatiza la conexión de servicios de IA y Base de Datos mediante Key Vault, pero las credenciales de Microsoft Entra ID deben configurarse manualmente por seguridad:

1. Navegar al recurso App Service `civicknit-prod-web` en el portal.
2. Ir a **Configuración -> Variables de entorno**.
3. Agregar manualmente las variables: `CLIENT_ID`, `CLIENT_SECRET`, `AUTHORITY` y `SCOPE`.
4. En "App Registration" (Azure AD), agregar la URI de redirección correspondiente a producción:
   `https://civicknit-prod-web.azurewebsites.net/getAToken`

### 2. Despliegue del Código
Para subir el código local al servicio en la nube, ejecute:

```bash
az webapp up --name civicknit-prod-web --resource-group rg-civicknit-prod
```