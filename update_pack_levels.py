"""
Script pour mettre à jour automatiquement le pack_level des utilisateurs
en fonction de leurs investissements actifs.

Règles:
- 0 investissement actif: pack_level = 1
- 1 investissement actif: pack_level = 2
- 2 investissements actifs: pack_level = 3
- 3 investissements actifs: pack_level = 4
- 4+ investissements actifs: pack_level = 5 (accès total)
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, func

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require')

def update_pack_levels():
    """Met à jour le pack_level de tous les utilisateurs."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Vérifier que la colonne pack_level existe
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user' AND column_name = 'pack_level'
        """))
        
        if not result.fetchone():
            print("❌ La colonne 'pack_level' n'existe pas. Exécutez d'abord add_pack_level_column.py")
            return
        
        # Compter les investissements actifs par utilisateur
        active_investments_query = text("""
            SELECT phone, COUNT(*) as active_count
            FROM investissement
            WHERE actif = TRUE
            GROUP BY phone
        """)
        
        result = conn.execute(active_investments_query)
        investments_by_user = result.fetchall()
        
        print(f"📊 Analyse de {len(investments_by_user)} utilisateurs avec investissements actifs...")
        
        updated_count = 0
        
        for phone, active_count in investments_by_user:
            # Déterminer le pack_level basé sur le nombre d'investissements
            if active_count >= 4:
                new_level = 5  # Accès total
            elif active_count == 3:
                new_level = 4
            elif active_count == 2:
                new_level = 3
            elif active_count == 1:
                new_level = 2
            else:
                new_level = 1
            
            # Mettre à jour le pack_level
            conn.execute(text("""
                UPDATE "user" 
                SET pack_level = :level
                WHERE phone = :phone
            """), {"level": new_level, "phone": phone})
            
            updated_count += 1
        
        conn.commit()
        
        print(f"✅ {updated_count} utilisateurs mis à jour avec succès!")
        print("")
        print("Récapitulatif:")
        
        # Afficher un récapitulatif
        summary_query = text("""
            SELECT pack_level, COUNT(*) as user_count
            FROM "user"
            WHERE pack_level IS NOT NULL
            GROUP BY pack_level
            ORDER BY pack_level
        """)
        
        result = conn.execute(summary_query)
        for row in result.fetchall():
            level, count = row
            access_text = ""
            if level == 1:
                access_text = "Pas d'accès PDF"
            elif level == 2:
                access_text = "Accès PDF Niveau 1-2"
            elif level == 3:
                access_text = "Accès PDF Niveau 1-3"
            elif level == 4:
                access_text = "Accès PDF Niveau 1-4"
            elif level >= 5:
                access_text = "ACCÈS TOTAL À TOUS LES PDFs"
            
            print(f"   Pack Level {level}: {count} utilisateurs - {access_text}")

if __name__ == "__main__":
    print("🚀 Mise à jour automatique des pack_levels...")
    print("=" * 60)
    update_pack_levels()
    print("=" * 60)
    print("✅ Terminé!")