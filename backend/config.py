import os
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')

    # Azure msal
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    AUTHORITY = os.getenv("AUTHORITY")
    SCOPE = [os.getenv("SCOPE")]
    REDIRECT_PATH = "/getAToken" 

    # Azure Cosmos DB
    COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
    COSMOS_KEY = os.getenv("COSMOS_KEY")
    COSMOS_DB_NAME = os.getenv("COSMOS_DB_NAME", "CivicKnitDB")
    COSMOS_CONTAINER_NAME = os.getenv("COSMOS_CONTAINER_NAME", "CivicContainer")

    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
    AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")

    # Azure Speech Services
    AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
    AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")