"""Script pour vérifier les tables custom_product et notification."""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DB_URL = os.getenv('DATABASE_URL')

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

tables_to_check = ['custom_product', 'notification']

for table in tables_to_check:
    cursor.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = '{table}'
        );
    """)
    exists = cursor.fetchone()[0]
    if exists:
        print(f"✅ La table '{table}' existe.")
    else:
        print(f"❌ La table '{table}' n'existe pas.")

cursor.close()
conn.close()