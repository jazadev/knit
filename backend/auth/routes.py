import os
import msal
import asyncio
from quart import Blueprint, session, redirect, url_for, request
from datetime import datetime, timezone
from backend.database.connection import get_container

auth_bp = Blueprint('auth', __name__)

def _build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        os.getenv("CLIENT_ID"),
        authority=os.getenv("AUTHORITY"),
        client_credential=os.getenv("CLIENT_SECRET"),
        token_cache=cache
    )

@auth_bp.route('/api/login')
async def login():
    redirect_uri = url_for("auth.authorized", _external=True, _scheme='https')
    
    # Envolvemos la llamada síncrona en un hilo aparte
    flow = await asyncio.to_thread(
        _build_msal_app().initiate_auth_code_flow,
        [os.getenv("SCOPE")],
        redirect_uri=redirect_uri
    )
    
    session["flow"] = flow
    return redirect(flow["auth_uri"])

@auth_bp.route('/getAToken')
async def authorized():
    try:
        cache = msal.SerializableTokenCache()
        msal_app = _build_msal_app(cache=cache)
        flow = session.get("flow")
        
        if not flow: 
            return redirect(url_for("auth.login", _external=True))

        # Envolvemos el intercambio de token
        result = await asyncio.to_thread(
            msal_app.acquire_token_by_auth_code_flow,
            flow,
            request.args
        )
        
        if "error" in result: 
            return f"Error: {result.get('error_description')}"

        user_claims = result.get("id_token_claims")
        session["user"] = user_claims
        session["token_cache"] = cache.serialize()
        
        container = await get_container()

        if container:
            user_id = user_claims.get("oid")
            try:
                await container.read_item(item=f"profile_{user_id}", partition_key=user_id)
            except Exception:
                # Crear perfil limpio si no existe
                new_profile = {
                    "id": f"profile_{user_id}",
                    "userId": user_id,
                    "type": "profile",
                    "personalInfo": {
                        "name": user_claims.get("name"),
                        "email": user_claims.get("preferred_username"),
                        "age": "", "gender": "", "country": "", "state": "", "phone": "",
                        "platformLang": "es"
                    },
                    "preferences": { "notifications": { "email": True, "sms": False } },
                    "topics": {
                        "events": { "enabled": True, "subs": {"cultural": True, "sports": False, "arts": False} },
                        "services": { "enabled": True, "subs": {"water": True, "light": True, "potholes": False} },
                        "institutions": { "enabled": False, "subs": {} },
                        "procedures": { "enabled": True, "subs": {} },
                        "community": { "enabled": False, "subs": {} },
                        "civic": { "enabled": False, "subs": {} }
                    },
                    "createdAt": datetime.now(timezone.utc).isoformat()
                }
                await container.create_item(body=new_profile)

        return redirect(url_for("main.index", _external=True, _scheme='https'))
        
    except Exception as e:
        return f"Error Auth: {str(e)}"

@auth_bp.route('/api/logout')
async def logout():
    session.clear()
    return redirect(f"{os.getenv('AUTHORITY')}/oauth2/v2.0/logout?post_logout_redirect_uri={url_for('main.index', _external=True, _scheme='https')}")