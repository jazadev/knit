import os
import requests
import asyncio
from quart import Blueprint, request, jsonify, session
from openai import AsyncAzureOpenAI
from datetime import datetime, timezone
from backend.database.connection import get_container
from backend.database.models import ChatSession, ChatMessage
from pydantic import ValidationError

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
    chat_id = req.get('chatId')
    app_lang = req.get('lang', 'es')
    
    browser_lang = request.accept_languages.best 
    
    container = await get_container()
    user = session.get("user")

    if not user_message.strip(): return jsonify({"response": ""}), 400

    now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    # Lógica de contexto
    if user and 'dbProfile' in user:
        profile = user['dbProfile']
        nombre = profile.get('name', 'Ciudadano')
        pais = profile.get('country', 'MX')
        estado = profile.get('state', 'CDMX')
        idioma = app_lang if app_lang else profile.get('platformLang', 'es')
        
        user_context = f"""
        CONTEXTO DEL USUARIO:
        - Nombre: {nombre}
        - Ubicación: {estado}, {pais}
        - Idioma preferido: {idioma}
        """
    else:
        user_context = f"""
        CONTEXTO DEL USUARIO (INVITADO):
        - Estatus: Anónimo
        - Idioma seleccionado: {app_lang}
        - Idioma navegador: {browser_lang}
        """
    
    SYSTEM_PROMPT = f"""
        Eres Civic Knit, un asistente experto en civismo.
        FECHA UTC: {now_utc}.        
        {user_context}
        REGLAS:
        1. Sé neutral y objetivo.
        2. Respeta el idioma del usuario ({app_lang}).
        3. Basa tus respuestas en leyes y datos oficiales.
        """

    # Lógica IA
    try:
        response = await client.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT_NAME"),
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}],
            temperature=0.7
        )
        ai_response = response.choices[0].message.content
    except Exception as e:
        print(f"Error OpenAI: {e}")
        ai_response = "Error de conexión."

    # Persistencia
    if user and container and chat_id:
        user_id = user.get("oid")
        try:
            try:
                chat_doc = await container.read_item(item=chat_id, partition_key=user_id)
                chat_session = ChatSession(**chat_doc)
            except Exception:
                chat_session = ChatSession(
                    id=chat_id, 
                    userId=user_id, 
                    title=user_message[:30] + "...",
                    messages=[]
                )
            
            chat_session.messages.append(ChatMessage(role="user", text=user_message))
            chat_session.messages.append(ChatMessage(role="ai", text=ai_response))
            chat_session.updatedAt = datetime.now(timezone.utc).isoformat()
            
            await container.upsert_item(body=chat_session.model_dump())
            
        except ValidationError as e:
            print(f"Error validación: {e}")
        except Exception as e: 
            print(f"Error guardando chat: {e}")

    return jsonify({"response": ai_response})