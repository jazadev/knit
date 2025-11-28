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
    if 'user' not in session or not container: return jsonify([]), 200
    
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
    if 'user' not in session or not container: return jsonify({"error": "401"}), 401
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
    except Exception as e: return jsonify({"error": str(e)}), 500

@chat_bp.route('/api/chats/<chat_id>', methods=['DELETE'])
async def delete_chat(chat_id):
    container = await get_container()
    if 'user' not in session or not container: return jsonify({"error": "401"}), 401
    try:
        await container.delete_item(item=chat_id, partition_key=session['user']['oid'])
        return jsonify({"status": "success"})
    except Exception: return jsonify({"error": "failed"}), 500

@chat_bp.route('/chat', methods=['POST'])
async def chat():
    req = await request.get_json()
    user_message = req.get('message', '')

    if not user_message.strip(): return jsonify({"response": ""}), 400
    moderation_result = await asyncio.to_thread(check_text_safety, user_message)
    if moderation_result['flagged']:
        return jsonify({
            "moderation_flagged": True,
            "ai_response": "Hemos detectado contenido que viola nuestras normas de seguridad.",
            "severity": moderation_result['severity'],
            "original_message": user_message
        })

    # Le preguntamos a GPT si el mensaje es tóxico antes de responder.
    try:
        judge_response = await client.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": """
                 Eres un sistema de moderación de contenido para una App Cívica.
                 Tu tarea es clasificar el mensaje del usuario.
                 
                 Reglas de bloqueo (Responde 'UNSAFE'):
                 - Discriminación por género, raza o religión.
                 - Discursos que nieguen derechos humanos (ej. derecho al voto).
                 - Insultos o ataques personales.
                 
                 Reglas de paso (Responde 'SAFE'):
                 - Opiniones políticas respetuosas.
                 - Preguntas sobre trámites o leyes.
                 - Críticas constructivas al gobierno.
                 
                 Responde SOLO una palabra: 'SAFE' o 'UNSAFE'.
                 """},
                {"role": "user", "content": user_message}
            ],
            temperature=0
        )
        
        veredicto = judge_response.choices[0].message.content.strip()
        
        if "UNSAFE" in veredicto:
            return jsonify({
                "moderation_flagged": True,
                "ai_response": "Este comentario ha sido ocultado porque promueve la discriminación o va en contra de los principios cívicos de igualdad.",
                "severity": 5, # Severidad media/alta 
                "original_message": user_message
            })

    except Exception as e:
        print(f"Error en Juez Semántico: {e}")
    
    chat_id = req.get('chatId')
    app_lang = req.get('lang', 'es')
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
        Eres Civic Knit. FECHA: {now_utc}. {user_context}.
        Idioma: {app_lang}. Sé neutral, objetivo y cívico.
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
        ai_response = "Error de conexión."

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
        except Exception as e: print(f"Error guardando: {e}")

    return jsonify({"response": ai_response})