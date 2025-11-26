// rag-main.bicep

// ====================================================================
// PARÁMETROS CONFIGURABLES
// ====================================================================
param location string = resourceGroup().location
param projectName string = 'rag-pipeline-cdmx'
param principalId string // CLAVE: ID de objeto (Object ID) del usuario o servicio que desplegará/accederá a secretos.
param searchSku string = 'standard'
param openAISku string = 'S0'
param cognitiveServicesSku string = 'S0'
param storageSku string = 'Standard_LRS'
param containerName string = 'gaceta-pdfs' // Contenedor para los PDFs

// ====================================================================
// RECURSOS PRINCIPALES
// ====================================================================

// 1. Azure Storage Account (Blob Storage - Fuente de datos)
resource storageAccount 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: toLower('ragplcdmxstorage')
  location: location
  sku: { name: storageSku }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
  }
}

resource blobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-09-01' = {
  name: 'ragplcdmxstorage/default/${containerName}'
  properties: {
    publicAccess: 'None'
  }
}

// 2. Azure AI Search Service
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: '${projectName}-search'
  location: location
  sku: { name: searchSku }
  properties: {}
}

// 3. Azure AI Services (Document Intelligence)
resource cognitiveService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${projectName}-aiservices'
  location: location
  sku: { name: cognitiveServicesSku }
  kind: 'CognitiveServices'
  properties: {
    customSubDomainName: '${projectName}-aiservices'
  }
}

// 4. Azure OpenAI Service
resource openAIService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${projectName}-openai'
  location: location
  sku: { name: openAISku }
  kind: 'OpenAI'
  properties: {
    customSubDomainName: '${projectName}-openai'
  }
}

// 5. Implementación del Modelo de Embeddings
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = {
  parent: openAIService
  name: 'embedding-ada'
  sku: { 
    name: 'Standard'
    capacity: 1
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-ada-002'
      version: '2'
    }
  }
}

// --------------------------------------------------------------------
// KEY VAULT Y ALMACENAMIENTO DE SECRETOS
// --------------------------------------------------------------------
resource keyVault 'Microsoft.KeyVault/vaults@2021-10-01' = {
  name: '${projectName}-kv'
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
resource searchKeySecret 'Microsoft.KeyVault/vaults/secrets@2021-10-01' = {
  parent: keyVault
  name: 'SearchAdminKey'
  properties: { value: searchService.listAdminKeys().primaryKey }
}

resource cogKeySecret 'Microsoft.KeyVault/vaults/secrets@2021-10-01' = {
  parent: keyVault
  name: 'CogServicesKey'
  properties: { value: cognitiveService.listKeys().key1 }
}

resource storageKeySecret 'Microsoft.KeyVault/vaults/secrets@2021-10-01' = {
  parent: keyVault
  name: 'StorageAccessKey'
  properties: { value: storageAccount.listKeys().keys[0].value }
}

// ====================================================================
// SALIDAS CLAVE (Solo exponen URIs y nombres, NO secretos)
// ====================================================================
output keyVaultUri string = keyVault.properties.vaultUri
output searchServiceName string = searchService.name
output cognitiveServicesEndpoint string = cognitiveService.properties.endpoint
output openAIServiceEndpoint string = openAIService.properties.endpoint
output storageAccountName string = storageAccount.name
output containerName string = containerName

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
//      --template-file rag-main.bicep \
//      --parameters principalId='<OBJECT_ID_AQUI>'
