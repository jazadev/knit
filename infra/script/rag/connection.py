import psycopg2
import os

def get_connection_uri():

    # Read URI parameters from the environment
    dbhost = os.environ['AZURE_DB_HOST_PSQL']
    dbname = os.environ['AZURE_DB_NAME_PSQL']
    dbuser = os.environ['AZURE_DB_USER_PSQL']
    password= os.environ['AZURE_DB_PASSWORD']
    sslmode = os.environ['AZURE_DB_SSL_MODE']

    try:
        conn = psycopg2.get_connection_uri(f"postgresql://{dbuser}:{password}@{dbhost}/{dbname}?sslmode={sslmode}")
        cursor = conn.cursor(conn)

    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
