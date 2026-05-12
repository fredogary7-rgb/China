import os
from sqlalchemy import create_engine, text
import random
import string
import hashlib
import time
from dotenv import load_dotenv

load_dotenv()

# URL de la base de données NeonDB
DATABASE_URI = os.getenv("DEFAULT_DB", "postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require")

def generate_referral_code(user_id, phone):
    """Génère un code de parrainage unique basé sur l'ID et le téléphone"""
    base = f"{user_id}{phone}{time.time()}"
    hash_obj = hashlib.md5(base.encode())
    hash_str = hash_obj.hexdigest()[:6].upper()
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    return f"TF{hash_str}{letters}"

def add_referral_code_column():
    """Ajoute la colonne referral_code à la table users et génère des codes"""
    engine = create_engine(DATABASE_URI)
    
    try:
        with engine.connect() as conn:
            # Vérifier si la colonne existe déjà
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'referral_code'
            """))
            columns = [row[0] for row in result.fetchall()]
            
            if 'referral_code' in columns:
                print("✅ La colonne 'referral_code' existe déjà")
            else:
                # Ajouter la colonne referral_code
                conn.execute(text("""
                    ALTER TABLE users ADD COLUMN referral_code TEXT
                """))
                conn.commit()
                print("✅ Colonne 'referral_code' ajoutée avec succès")
            
            # Générer des codes de parrainage pour tous les utilisateurs existants
            result = conn.execute(text("""
                SELECT id, phone, referral_code FROM users
            """))
            users = result.fetchall()
            
            updated_count = 0
            for user in users:
                user_id, phone, existing_code = user
                
                if existing_code is None or str(existing_code).strip() == '':
                    # Générer un code unique
                    referral_code = generate_referral_code(user_id, phone if phone else user_id)
                    
                    # Vérifier que le code n'existe pas déjà
                    while True:
                        check = conn.execute(text("""
                            SELECT COUNT(*) FROM users WHERE referral_code = :code
                        """), {"code": referral_code})
                        if check.fetchone()[0] == 0:
                            break
                        referral_code = generate_referral_code(user_id, phone if phone else user_id)
                    
                    # Mettre à jour l'utilisateur
                    conn.execute(text("""
                        UPDATE users SET referral_code = :code WHERE id = :uid
                    """), {"code": referral_code, "uid": user_id})
                    updated_count += 1
                    print(f"   → Utilisateur {user_id}: {referral_code}")
            
            conn.commit()
            print(f"\n✅ {updated_count} utilisateurs mis à jour avec un code de parrainage")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("🚀 Ajout de la colonne referral_code...")
    add_referral_code_column()
    print("\n✅ Terminé !")