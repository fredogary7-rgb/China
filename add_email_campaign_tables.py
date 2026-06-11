"""
Script de migration pour ajouter les tables EmailCampaign, EmailLog, Unsubscribe.
Exécution : python add_email_campaign_tables.py
"""

import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Importer l'application et la base de données
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, db
from sqlalchemy import text

def add_email_campaign_tables():
    """Crée les tables email_campaign, email_log, unsubscribe si elles n'existent pas."""
    
    with app.app_context():
        with db.engine.connect() as conn:
            print("=" * 60)
            print("🔄 Migration des tables d'emailing...")
            print("=" * 60)
            
            # 1. Table email_campaign
            print("📧 Création de la table email_campaign...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS email_campaign (
                    id SERIAL PRIMARY KEY,
                    campaign_type VARCHAR(50) NOT NULL,
                    product_id INTEGER,
                    subject VARCHAR(200) NOT NULL,
                    total_recipients INTEGER DEFAULT 0,
                    emails_sent INTEGER DEFAULT 0,
                    emails_failed INTEGER DEFAULT 0,
                    push_sent INTEGER DEFAULT 0,
                    notifications_created INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'completed',
                    scheduled_at TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_by VARCHAR(30),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_email_campaign_type 
                ON email_campaign (campaign_type, created_at)
            """))
            print("✅ Table email_campaign créée")
            
            # 2. Table email_log
            print("📝 Création de la table email_log...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS email_log (
                    id SERIAL PRIMARY KEY,
                    campaign_id INTEGER REFERENCES email_campaign(id),
                    user_phone VARCHAR(30) NOT NULL,
                    user_email VARCHAR(120) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    error_message TEXT,
                    sent_at TIMESTAMP,
                    opened_at TIMESTAMP,
                    clicked_at TIMESTAMP
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_email_log_campaign 
                ON email_log (campaign_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_email_log_user 
                ON email_log (user_phone)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_email_log_status 
                ON email_log (status)
            """))
            print("✅ Table email_log créée")
            
            # 3. Table unsubscribe
            print("🚫 Création de la table unsubscribe...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS unsubscribe (
                    id SERIAL PRIMARY KEY,
                    user_email VARCHAR(120) NOT NULL UNIQUE,
                    user_phone VARCHAR(30),
                    unsubscribe_token VARCHAR(100) NOT NULL UNIQUE,
                    reason VARCHAR(50),
                    unsubscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45)
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_unsubscribe_email 
                ON unsubscribe (user_email)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_unsubscribe_token 
                ON unsubscribe (unsubscribe_token)
            """))
            print("✅ Table unsubscribe créée")
            
            conn.commit()
            
            print("=" * 60)
            print("✅ Migration terminée avec succès !")
            print("=" * 60)
            print("\nTables créées :")
            print("  - email_campaign (historique des campagnes)")
            print("  - email_log (log détaillé des emails)")
            print("  - unsubscribe (liste de désinscription)")

if __name__ == "__main__":
    try:
        add_email_campaign_tables()
    except Exception as e:
        print(f"❌ Erreur lors de la migration : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)