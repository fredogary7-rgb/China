"""Script pour vérifier/créer la table notification."""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DB_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require')

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

# Check if notification table exists
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'notification'
    );
""")
exists = cursor.fetchone()[0]

if exists:
    print("✅ La table 'notification' existe déjà.")
else:
    print("⚠️ La table 'notification' n'existe pas. Création...")
    cursor.execute("""
        CREATE TABLE notification (
            id SERIAL PRIMARY KEY,
            user_phone VARCHAR(30) NOT NULL,
            type VARCHAR(20) NOT NULL,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            action_url VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("✅ Table 'notification' créée avec succès !")

cursor.close()
conn.close()