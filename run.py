from backend import create_app

app = create_app()

if __name__ == '__main__':
    # puerto 5001 para evitar conflictos con mac 
    app.run(debug=True, port=5001)