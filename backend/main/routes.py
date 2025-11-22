from flask import Blueprint, render_template, session, request, jsonify
from backend.database.connection import get_container
from datetime import datetime, timezone

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    session_user = session.get("user", None)
    if not session_user:
        return render_template('index.html', user=None)
    
    frontend_user = session_user.copy()
    container = get_container()

    if container:
        try:
            user_id = session_user.get("oid")
            # Leemos el perfil completo
            doc = container.read_item(item=f"profile_{user_id}", partition_key=user_id)
            
            # Inyectamos los datos
            frontend_user['dbProfile'] = doc.get('personalInfo', {})
            frontend_user['dbTopics'] = doc.get('topics', {})
            frontend_user['dbPreferences'] = doc.get('preferences', {})
        except Exception:
            # Si no existe el perfil
            pass

    return render_template('index.html', user=frontend_user)

@main_bp.route('/api/save-profile', methods=['POST'])
def save_profile():
    container = get_container()
    if 'user' not in session or not container:
        return jsonify({"error": "401"}), 401
    
    data = request.get_json()
    user_id = session['user']['oid']
    
    # documento a guardar
    doc = {
        "id": f"profile_{user_id}",
        "userId": user_id,
        "type": "profile",
        
        "personalInfo": {
            "name": data.get('name'),
            "email": data.get('email'),
            "age": data.get('age'),
            "gender": data.get('gender'),
            "country": data.get('country'),
            "state": data.get('state'),
            "phone": data.get('phone'),
            "platformLang": data.get('platformLang')
        },
        "preferences": {
            "notifications": data.get('channels')
        },
        "topics": data.get('topics'),
        
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    try:
        container.upsert_item(body=doc)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/api/delete-account', methods=['POST'])
def delete_account():
    container = get_container()
    if 'user' not in session or not container:
        return jsonify({"error": "401"}), 401
    
    user_id = session['user']['oid']
    
    try:
        # Borrado en cascada de todo lo del usuario
        items = list(container.query_items(
            query="SELECT * FROM c WHERE c.userId = @userId",
            parameters=[{"name": "@userId", "value": user_id}],
            enable_cross_partition_query=False
        ))
        
        for item in items:
            container.delete_item(item=item['id'], partition_key=user_id)
            
        session.clear()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500