import os
from flask import Flask
from flask_session import Session
from .config import Config

# Inicializamos extensiones globalmente
sess = Session()

def create_app(config_class=Config):
    # la ruta exacta de este archivo
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # ruta del frontend
    template_dir = os.path.join(base_dir, '..', 'frontend', 'templates')
    static_dir = os.path.join(base_dir, '..', 'frontend', 'static')

    # inicializamos la app
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    app.config.from_object(config_class)

    sess.init_app(app)

    # bBlueprints
    from backend.main.routes import main_bp
    from backend.auth.routes import auth_bp
    from backend.chat.routes import chat_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)

    return app