import mimetypes
from backend import create_app

mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

app = create_app()

if __name__ == '__main__':
    # puerto 5001 para evitar conflictos con mac 
    app.run(debug=False, port=5001)