from flask import Blueprint, render_template, session, request, jsonify, url_for
from backend.database.connection import get_container
from backend.database.models import UserProfile, PersonalInfo, Preferences
from pydantic import ValidationError
from .services import get_profile_by_key

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

    try:
        user_profile = UserProfile(
            id=f"profile_{user_id}",
            userId=user_id,
            personalInfo=PersonalInfo(
                name=data.get('name'),
                email=data.get('email'),
                age=str(data.get('age', '')), # Aseguramos string para evitar conflictos
                gender=data.get('gender'),
                country=data.get('country'),
                state=data.get('state'),
                phone=data.get('phone'),
                platformLang=data.get('platformLang')
            ),
            preferences=Preferences(
                notifications=data.get('channels', {})
            ),
            topics=data.get('topics', {})
        )

        # JSON limpio para Cosmos
        doc_to_save = user_profile.model_dump()
        container.upsert_item(body=doc_to_save)
        
        return jsonify({"status": "success"})
    
    except ValidationError as e:
        print(f"Error de validación: {e}")
        return jsonify({"error": "Datos inválidos", "details": str(e)}), 400
        
    except Exception as e:
        print(f"Error guardando perfil: {e}")
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

@main_bp.route('/use-cases')
def use_cases():
    session_user = session.get("user", None)
    return render_template('use_cases.html', user=session_user)

@main_bp.route('/api/demo/set-persona', methods=['POST'])
def set_demo_persona():
    data = request.get_json()
    persona_type = data.get('type') 

    selected = get_profile_by_key(persona_type)
        
    if not selected:
        return jsonify({'error': 'Perfil demo no encontrado'}), 400

    # inyectar sesión
    session['user'] = selected
    session.modified = True
    
    return jsonify({'status': 'success', 'redirect': url_for('main.index')})