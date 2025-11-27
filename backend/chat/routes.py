import os
import requests
from flask import Blueprint, request, jsonify, session
from openai import AzureOpenAI
from datetime import datetime, timezone, date
from backend.database.connection import get_container
from backend.database.models import ChatSession, ChatMessage
from pydantic import ValidationError

chat_bp = Blueprint('chat', __name__)

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

SYSTEM_PROMPT = f"Eres Civic Knit... FECHA: {datetime.now().strftime('%d/%m/%Y')}"

# Ruta para obtener token de voz
@chat_bp.route('/api/speech-token', methods=['GET'])
def get_speech_token():
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")

    if not speech_key or not speech_region:
        return jsonify({"error": "Faltan credenciales de voz"}), 500

    # Azure pide el token a esta URL específica
    fetch_token_url = f"https://{speech_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    
    headers = {
        'Ocp-Apim-Subscription-Key': speech_key
    }
    
    try:
        response = requests.post(fetch_token_url, headers=headers)
        access_token = str(response.text)
        return jsonify({
            "token": access_token, 
            "region": speech_region
        })
    except Exception as e:
        print(e)
        return jsonify({"error": "Error obteniendo token de voz"}), 500

@chat_bp.route('/api/chats', methods=['GET'])
def get_chats():
    container = get_container()
    if 'user' not in session or not container: return jsonify([]), 200
    
    user_id = session['user']['oid']
    query = "SELECT * FROM c WHERE c.userId = @userId AND c.type = 'chat' ORDER BY c.updatedAt DESC"
    try:
        items = list(container.query_items(
            query=query, parameters=[{"name": "@userId", "value": user_id}], enable_cross_partition_query=False
        ))
        return jsonify(items)
    except Exception: return jsonify([])

@chat_bp.route('/api/chats', methods=['DELETE'])
def delete_all_chats():
    container = get_container()
    if 'user' not in session or not container: return jsonify({"error": "401"}), 401
    user_id = session['user']['oid']
    try:
        query = "SELECT * FROM c WHERE c.userId = @userId AND c.type = 'chat'"
        items = list(container.query_items(query=query, parameters=[{"name": "@userId", "value": user_id}]))
        for item in items:
            container.delete_item(item=item['id'], partition_key=user_id)
        return jsonify({"status": "success"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@chat_bp.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    container = get_container()
    if 'user' not in session or not container: return jsonify({"error": "401"}), 401
    try:
        container.delete_item(item=chat_id, partition_key=session['user']['oid'])
        return jsonify({"status": "success"})
    except Exception: return jsonify({"error": "failed"}), 500

@chat_bp.route('/chat', methods=['POST'])
def chat():
    req = request.get_json()
    user_message = req.get('message', '')
    chat_id = req.get('chatId')
    container = get_container()
    user = session.get("user")

    if not user_message.strip(): return jsonify({"response": ""}), 400

    # Lógica IA
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT_NAME"),
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}],
            temperature=0.7
        )
        ai_response = response.choices[0].message.content
    except Exception as e:
        print(e)
        ai_response = "Error de conexión."

    # Persistencia
    if user and container and chat_id:
        user_id = user.get("oid")
        try:
            try:
                chat_doc = container.read_item(item=chat_id, partition_key=user_id)
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
            container.upsert_item(body=chat_session.model_dump())
        except ValidationError as e:
            print(f"Error de validación de datos: {e}")
        except Exception as e: 
            print(f"Error guardando chat: {e}")

    return jsonify({"response": ai_response})