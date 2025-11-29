import os
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential

def check_text_safety(text: str) -> dict:
    """ Llama al servicio Azure AI Content Safety para revisar un texto. """
    
    palabras_prohibidas = ["odio", "estupid", "idiota", "maldit"]
    text_lower = text.lower()
    
    for palabra in palabras_prohibidas:
        if palabra in text_lower:
            return {
                "flagged": True,
                "severity": 1,
                "reason": f"Palabra prohibida detectada: {palabra}"
            }

    # 2. FILTRO DE AZURE
    endpoint = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")
    key = os.getenv("AZURE_CONTENT_SAFETY_KEY")
    
    if not endpoint or not key:
        return {"flagged": False, "reason": "MODERATION_DISABLED"}

    client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
    
    request = {
        "text": text,
        "categories": ["Hate", "SelfHarm", "Sexual", "Violence"],
        "blocklistNames": [] 
    }
    
    try:
        response = client.analyze_text(request)
        
        # Bajamos la tolerancia a > 0 para ser más estrictos
        flagged = any(result.severity > 0 for result in response.categories_analysis)

        analysis_simple = [
            {"category": str(res.category), "severity": res.severity} 
            for res in response.categories_analysis
        ]

        return {
            "flagged": flagged,
            # Obtenemos la severidad más alta encontrada
            "severity": max(r.severity for r in response.categories_analysis) if response.categories_analysis else 0,
            "reason": analysis_simple
        }
        
    except Exception as e:
        print(f"Content Safety Error: {e}")
        return {"flagged": False, "reason": "API_ERROR"}