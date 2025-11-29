import os
import requests
import asyncio
from quart import Blueprint, request, jsonify, session
from openai import AsyncAzureOpenAI, BadRequestError
from datetime import datetime, timezone
from backend.database.connection import get_container
from backend.database.models import ChatSession, ChatMessage
from pydantic import ValidationError
from .moderation import check_text_safety

chat_bp = Blueprint('chat', __name__)

client = AsyncAzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

MODERATION_WARNINGS = {
    'es': "Hemos detectado contenido que podría violar nuestras normas. Por favor, reformula tu pregunta.",
    'en': "We detected content that may violate our guidelines. Please rephrase your query.",
    'fr': "Nous avons détecté du contenu pouvant enfreindre nos règles. Veuillez reformuler votre requête."
}

# Ruta para obtener token de voz
@chat_bp.route('/api/speech-token', methods=['GET'])
async def get_speech_token():
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")

    if not speech_key or not speech_region:
        return jsonify({"error": "Faltan credenciales de voz"}), 500

    fetch_token_url = f"https://{speech_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {'Ocp-Apim-Subscription-Key': speech_key}
    
    try:
        # Requests es síncrono se manda a un hilo para no bloquear
        response = await asyncio.to_thread(requests.post, fetch_token_url, headers=headers)
        access_token = str(response.text)
        return jsonify({"token": access_token, "region": speech_region})
    except Exception as e:
        print(e)
        return jsonify({"error": "Error obteniendo token de voz"}), 500

@chat_bp.route('/api/chats', methods=['GET'])
async def get_chats():
    container = await get_container()
    if 'user' not in session or not container:
        return jsonify([]), 200
    
    user_id = session['user']['oid']
    query = "SELECT * FROM c WHERE c.userId = @userId AND c.type = 'chat' ORDER BY c.updatedAt DESC"
    
    try:
        query_iterable = container.query_items(
            query=query, 
            parameters=[{"name": "@userId", "value": user_id}] 
        )
        
        items_crudos = [item async for item in query_iterable]
        
        chats_finales = []
        for item in items_crudos:
            try:
                chat_obj = ChatSession(**item)
                chats_finales.append(chat_obj.model_dump(by_alias=True, mode='json'))
            except ValidationError as e:
                print(f"Chat corrupto ignorado (ID: {item.get('id')}): {e}")
                
        return jsonify(chats_finales)

    except Exception as e:
        print(f"Error leyendo chats: {e}")
        return jsonify([])

@chat_bp.route('/api/chats', methods=['DELETE'])
async def delete_all_chats():
    container = await get_container()
    if 'user' not in session or not container:
        return jsonify({"error": "401"}), 401
    user_id = session['user']['oid']
    try:
        query = "SELECT * FROM c WHERE c.userId = @userId AND c.type = 'chat'"
        query_iterable = container.query_items(
            query=query, 
            parameters=[{"name": "@userId", "value": user_id}] 
        )
        
        items = []
        async for item in query_iterable:
            items.append(item)
            
        for item in items:
            await container.delete_item(item=item['id'], partition_key=user_id)
            
        return jsonify({"status": "success"})
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

@chat_bp.route('/api/chats/<chat_id>', methods=['DELETE'])
async def delete_chat(chat_id):
    container = await get_container()
    if 'user' not in session or not container:
        return jsonify({"error": "401"}), 401
    try:
        await container.delete_item(item=chat_id, partition_key=session['user']['oid'])
        return jsonify({"status": "success"})
    except Exception: 
        return jsonify({"error": "failed"}), 500

@chat_bp.route('/chat', methods=['POST'])
async def chat():
    req = await request.get_json()
    chat_id = req.get('chatId')
    app_lang = req.get('lang', 'es')
    user_message = req.get('message', '')

    if not user_message.strip():
        return jsonify({"response": ""}), 400
    moderation_result = await asyncio.to_thread(check_text_safety, user_message)
    if moderation_result['flagged']:
        warning_message = MODERATION_WARNINGS.get(app_lang, MODERATION_WARNINGS['es'])
        
        return jsonify({
            "moderation_flagged": True,
            "ai_response": warning_message,
            "severity": moderation_result['severity'],
            "original_message": user_message
        })

    # Le preguntamos a GPT si el mensaje es tóxico antes de responder.
    try:
        judge_response = await client.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": """
                 Role: Content Moderation AI for a Civic App.
                 Task: Classify the user message.
                 
                 BLOCKING RULES (Respond 'UNSAFE'):
                 1. Discrimination/Hate: Against gender, race, religion, nationality (e.g., "Women can't lead", "X people are bad").
                 2. Insults/Attacks: Personal attacks (e.g., "You are stupid", "Idiot").
                 3. Anti-Democratic: Denying human rights (e.g., "Don't vote").
                 
                 PASSING RULES (Respond 'SAFE'):
                 1. Opinions on politics (even negative ones, if respectful).
                 2. Questions about laws, procedures, or history.
                 3. Civic criticism.
                 
                 Output: Respond ONLY with one word: 'SAFE' or 'UNSAFE'.
                 """},
                {"role": "user", "content": user_message}
            ],
            temperature=0
        )
        
        veredicto = judge_response.choices[0].message.content.strip()
        
        if "UNSAFE" in veredicto:        
            warning_message = MODERATION_WARNINGS.get(app_lang, MODERATION_WARNINGS['es'])

            return jsonify({
                "moderation_flagged": True,
                "ai_response": warning_message, # <-- Enviamos el texto traducido
                "severity": 5,
                "original_message": user_message
            })

    except Exception as e:
        print(f"Error en Juez Semántico: {e}")
    
    container = await get_container()
    user = session.get("user")

    now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    # Lógica de contexto de usuario
    if user and 'dbProfile' in user:
        profile = user['dbProfile']
        user_context = f"Usuario: {profile.get('name')}, {profile.get('state')}, {profile.get('country')}"
    else:
        user_context = "Usuario Invitado."
    
    SYSTEM_PROMPT = f"""
    ROLE: You are **Civic Knit**, a Digital Civic Assistant specialized in government information, laws, procedures, and public policies. Your main goal is to facilitate civic life by providing clear, accessible, and accurate information.

    # CORE RULES & CONTEXT
    1. **IDENTITY:** Be neutral, objective, civic-minded, and strictly professional.
    2. **LOCATION SCOPE:** Your knowledge base is focused on **Mexico City (CDMX)**. All answers regarding procedures, laws, or programs must be framed within this jurisdiction unless the user explicitly asks about federal topics or another location.
    3. **KNOWLEDGE PRIORITY (RAG):** You have access to recent legal and normative documents. **YOU MUST PRIORITIZE this information** over your general knowledge to ensure currency and precision. If the context is not relevant, rely on your internal training.
    4. **MODERATION:** The user's message has already passed a safety filter. Always maintain a **respectful** and **helpful** tone. Never be punitive or repeat safety rules to the user.

    # OUTPUT INSTRUCTION
    - **LANGUAGE:** You MUST respond strictly in the language: **{app_lang}**.
    - **FORMAT:** Use **Markdown** (bolding, lists, headers) to make reading easier.
    - **CITATIONS:** If you used information from the provided documents, add a reference at the end (e.g., "Source: Official Gazette, Art. 5").

    # SESSION DATA
    - CURRENT DATE UTC: {now_utc}
    - USER PROFILE: {user_context}
    """

    try:
        response = await client.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT_NAME"),
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}],
            temperature=0.7
        )
        ai_response = response.choices[0].message.content

    except BadRequestError as e:
        if e.code == 'content_filter':
            return jsonify({
                "moderation_flagged": True,
                "ai_response": "Contenido bloqueado por las políticas de seguridad de Azure AI.",
                "severity": 2, 
                "original_message": user_message
            })
        ai_response = "Error en la solicitud."
    except Exception as e:
        ai_response = f"Error {e} de conexión."

    # Persistencia (Guardar chat)
    if user and container and chat_id and ai_response:
        # (Tu lógica de guardado sigue igual aquí...)
        user_id = user.get("oid")
        try:
            try:
                chat_doc = await container.read_item(item=chat_id, partition_key=user_id)
                chat_session = ChatSession(**chat_doc)
            except Exception:
                chat_session = ChatSession(id=chat_id, userId=user_id, title=user_message[:30]+"...", messages=[])
            
            chat_session.messages.append(ChatMessage(role="user", text=user_message))
            chat_session.messages.append(ChatMessage(role="ai", text=ai_response))
            chat_session.updatedAt = datetime.now(timezone.utc).isoformat()
            await container.upsert_item(body=chat_session.model_dump())
        except Exception as e:
            print(f"Error guardando: {e}")

    return jsonify({"response": ai_response})