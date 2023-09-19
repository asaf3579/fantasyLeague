import psycopg2
from datetime import datetime


class DBHandler:

    def __init__(self, database, user, password, host, port):
        self.connection = psycopg2.connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cursor = self.connection.cursor()

    def execute_query(self, query, values=None):
        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            print("Query executed successfully")
        except Exception as e:
            print(f"Error executing query: {e}")
            self.connection.rollback()

    def fetch_data(self, query, values=None):
        try:
            self.cursor.execute(query, values)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    def create_users_messages_table(self):
        self.cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL,
        color VARCHAR(7)
    );
''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                text VARCHAR(200),
                timestamp TIMESTAMP DEFAULT NOW(),
                user_id INTEGER REFERENCES users(id),
                user_name VARCHAR(50),
                color VARCHAR(7) 
            );
        ''')
        self.connection.commit()

    def close_connection(self):
        self.cursor.close()
        self.connection.close()
