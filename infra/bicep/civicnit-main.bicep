// civicknit-main.bicep

// ====================================================================
// PARÁMETROS CONFIGURABLES
// ====================================================================
param location string = resourceGroup().location
param projectName string = 'civicknit-prod'
param principalId string // CLAVE: ID de objeto (Object ID) del usuario para acceso a Key Vault.
param openAISku string = 'S0'
param contentSafetySku string = 'S0'
param speechSku string = 'S0'
param appServiceSku string = 'B1' // Plan Básico para Dev/Test
param cosmosDbName string = 'CivicKnitDB'

// ====================================================================
// RECURSOS PRINCIPALES
// ====================================================================

// 1. Azure Content Safety (Moderación)
resource contentSafety 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${projectName}-safety'
  location: location
  sku: { name: contentSafetySku }
  kind: 'ContentSafety'
  properties: {
    customSubDomainName: '${projectName}-safety'
  }
}

// 2. Azure Speech Services (Voz)
resource speechService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${projectName}-speech'
  location: location
  sku: { name: speechSku }
  kind: 'SpeechServices'
  properties: {
    customSubDomainName: '${projectName}-speech'
  }
}

// 3. Azure OpenAI Service (Cerebro del Chat)
resource openAIService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${projectName}-openai'
  location: location
  sku: { name: openAISku }
  kind: 'OpenAI'
  properties: {
    customSubDomainName: '${projectName}-openai'
  }
}

// Implementación del Modelo GPT-4o
resource gptDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAIService
  name: 'gpt-4o'
  sku: { 
    name: 'Standard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-08-06'
    }
  }
}

// 4. Azure Cosmos DB (Base de Datos NoSQL)
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: '${projectName}-cosmos'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    capabilities: [ { name: 'EnableServerless' } ]
  }
}

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosAccount
  name: cosmosDbName
  properties: { resource: { id: cosmosDbName } }
}

resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: cosmosDb
  name: 'CivicContainer'
  properties: {
    resource: {
      id: 'CivicContainer'
      partitionKey: { paths: ['/userId'], kind: 'Hash' }
    }
  }
}

// --------------------------------------------------------------------
// KEY VAULT Y ALMACENAMIENTO DE SECRETOS
// --------------------------------------------------------------------
resource keyVault 'Microsoft.KeyVault/vaults@2021-10-01' = {
  name: '${projectName}-kv-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: principalId
        permissions: { secrets: [ 'get', 'list', 'set', 'delete' ] }
      }
    ]
  }
}

// 5. Guardar Secretos en Key Vault
resource secretOpenAI 'Microsoft.KeyVault/vaults/secrets@2021-10-01' = {
  parent: keyVault
  name: 'AZURE-OPENAI-KEY'
  properties: { value: openAIService.listKeys().key1 }
}

resource secretSafety 'Microsoft.KeyVault/vaults/secrets@2021-10-01' = {
  parent: keyVault
  name: 'AZURE-CONTENT-SAFETY-KEY'
  properties: { value: contentSafety.listKeys().key1 }
}

resource secretSpeech 'Microsoft.KeyVault/vaults/secrets@2021-10-01' = {
  parent: keyVault
  name: 'AZURE-SPEECH-KEY'
  properties: { value: speechService.listKeys().key1 }
}

resource secretCosmos 'Microsoft.KeyVault/vaults/secrets@2021-10-01' = {
  parent: keyVault
  name: 'AZURE-COSMOS-KEY'
  properties: { value: cosmosAccount.listKeys().primaryMasterKey }
}

// ====================================================================
// WEB APP (APP SERVICE) - Integración Automática
// ====================================================================

resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: '${projectName}-plan'
  location: location
  sku: { name: appServiceSku }
  kind: 'linux'
  properties: { reserved: true }
}

resource webApp 'Microsoft.Web/sites@2022-09-01' = {
  name: '${projectName}-web'
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'python -m hypercorn run:app --bind 0.0.0.0:8000'
      appSettings: [
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: openAIService.properties.endpoint
        }
        {
          name: 'AZURE_OPENAI_KEY'
          value: '@Microsoft.KeyVault(SecretUri=${secretOpenAI.properties.secretUri})'
        }
        {
          name: 'AZURE_CONTENT_SAFETY_ENDPOINT'
          value: contentSafety.properties.endpoint
        }
        {
          name: 'AZURE_CONTENT_SAFETY_KEY'
          value: '@Microsoft.KeyVault(SecretUri=${secretSafety.properties.secretUri})'
        }
        {
          name: 'AZURE_SPEECH_REGION'
          value: location
        }
        {
          name: 'AZURE_SPEECH_KEY'
          value: '@Microsoft.KeyVault(SecretUri=${secretSpeech.properties.secretUri})'
        }
        {
          name: 'AZURE_COSMOS_ENDPOINT'
          value: cosmosAccount.properties.documentEndpoint
        }
        {
          name: 'AZURE_COSMOS_KEY'
          value: '@Microsoft.KeyVault(SecretUri=${secretCosmos.properties.secretUri})'
        }
        {
          name: 'AZURE_COSMOS_DATABASE'
          value: cosmosDbName
        }
        {
          name: 'AZURE_COSMOS_CONTAINER'
          value: 'CivicContainer'
        }
        {
          name: 'AZURE_DEPLOYMENT_NAME'
          value: 'gpt-4o'
        }
        {
          name: 'AZURE_OPENAI_API_VERSION'
          value: '2024-02-15-preview'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
      ]
    }
  }
}

// ====================================================================
// SALIDAS CLAVE (Solo exponen URIs y nombres, NO secretos)
// ====================================================================
output keyVaultUri string = keyVault.properties.vaultUri
output webAppName string = webApp.name
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output openAIEndpoint string = openAIService.properties.endpoint
output contentSafetyEndpoint string = contentSafety.properties.endpoint
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint

// ============================================================
// Para desplegar
// 1. Login a Azure
// 2. Obtener ID de Objeto (para el parámetro principalId)
// 3. Desplegar la infraestructura (ejecución)
// Nota: Los tenat nuevos requieren registrar el servicio az provider register --namespace Microsoft.KeyVault
// ============================================================
// $ az login --tenant <TENANT-ID>
// $ az ad signed-in-user show --query id --output tsv
// $ az deployment group create \
//      --resource-group rg-Civicknit \
//      --template-file civicknit-main.bicep \
//      --parameters principalId='<OBJECT_ID_AQUI>'
