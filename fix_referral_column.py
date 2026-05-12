"""
Script pour ajouter les colonnes referral_code et parrain_code à la table user
Exécution : python fix_referral_column.py
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

load_dotenv()

DATABASE_URI = os.getenv("DEFAULT_DB", "postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require")

def fix_referral_column():
    engine = create_engine(DATABASE_URI)
    inspector = inspect(engine)
    
    # Vérifier les colonnes existantes
    try:
        columns = [col['name'] for col in inspector.get_columns('user')]
        print(f"Colonnes actuelles dans 'user': {columns}")
    except Exception as e:
        print(f"Erreur lors de l'inspection de la table user: {e}")
        return
    
    with engine.connect() as conn:
        # Ajouter referral_code si elle n'existe pas
        if 'referral_code' not in columns:
            conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN referral_code VARCHAR(8)
            """))
            conn.commit()
            print("✅ Colonne 'referral_code' ajoutée avec succès")
        else:
            print("ℹ️ Colonne 'referral_code' existe déjà")
        
        # Ajouter parrain_code si elle n'existe pas
        if 'parrain_code' not in columns:
            conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN parrain_code VARCHAR(8)
            """))
            conn.commit()
            print("✅ Colonne 'parrain_code' ajoutée avec succès")
        else:
            print("ℹ️ Colonne 'parrain_code' existe déjà")
    
    print("\n🎉 Migration terminée ! Redémarrez votre application Flask.")

if __name__ == "__main__":
    fix_referral_column()