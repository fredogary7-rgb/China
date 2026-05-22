"""
Script pour créer la table push_subscription si elle n'existe pas.
Usage: python create_push_subscription_table.py
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Charger les variables d'environnement
load_dotenv()

# Récupérer l'URL de la base de données depuis app.py
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require")

def create_push_subscription_table():
    """Crée la table push_subscription si elle n'existe pas."""
    
    engine = create_engine(DATABASE_URL)
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS push_subscription (
        id SERIAL PRIMARY KEY,
        user_phone VARCHAR(30) NOT NULL,
        endpoint TEXT NOT NULL,
        p256dh TEXT NOT NULL,
        auth TEXT NOT NULL,
        browser VARCHAR(50),
        device_type VARCHAR(20) DEFAULT 'desktop',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_push_subscription_user ON push_subscription(user_phone, is_active);
    CREATE UNIQUE INDEX IF NOT EXISTS idx_push_subscription_endpoint ON push_subscription(endpoint);
    """
    
    try:
        with engine.connect() as conn:
            # Créer la table
            conn.execute(text(create_table_sql))
            conn.commit()
            print("✅ Table 'push_subscription' créée avec succès !")
            
            # Créer les index
            conn.execute(text(create_index_sql))
            conn.commit()
            print("✅ Index créés avec succès !")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        raise

if __name__ == "__main__":
    print("🔧 Création de la table push_subscription...")
    create_push_subscription_table()
    print("🎉 Table push_subscription prête !")