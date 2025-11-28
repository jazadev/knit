import mimetypes
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from backend import create_app

mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

app = create_app()

if __name__ == '__main__':
    config = Config()
    config.bind = ["127.0.0.1:5001"]
    config.use_reloader = True # Habilitar recarga automática en desarrollo
        
    asyncio.run(serve(app, config))