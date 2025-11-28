import os
from quart import Quart, render_template
from .config import Config

def create_app(config_class=Config):
    # la ruta exacta de este archivo
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # ruta del frontend
    template_dir = os.path.join(base_dir, '..', 'frontend', 'templates')
    static_dir = os.path.join(base_dir, '..', 'frontend', 'static')

    # inicializamos la app
    app = Quart(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    app.config.from_object(config_class)

    # Detectamos si estamos en Azure o en Local
    if os.getenv("WEBSITE_HOSTNAME"): 
        # Estamos en Azure Forzamos HTTPS
        app.config["PREFERRED_URL_SCHEME"] = "https"
    else:
        # Usamos HTTP normal para no romper SSL
        app.config["PREFERRED_URL_SCHEME"] = "http"
        app.config["SESSION_COOKIE_SECURE"] = False

    # bBlueprints
    from backend.main.routes import main_bp
    from backend.auth.routes import auth_bp
    from backend.chat.routes import chat_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)

    @app.errorhandler(404)
    async def page_not_found(e):
        return await render_template('/components/errors/404.html', user=None), 404

    @app.errorhandler(500)
    async def internal_error(e):
        return await render_template('/components/errors/500.html', user=None), 500

    return app