"""
Script pour mettre à jour le pack_level des utilisateurs basé sur le nombre TOTAL d'investissements (actifs + terminés).

Règles:
- 0 investissement total: pack_level = 0 (pas d'accès PDF)
- 1 investissement total: pack_level = 1 (accès à 1 fichier)
- 2 investissements totaux: pack_level = 2 (accès à 2 fichiers)
- 3 investissements totaux: pack_level = 3 (accès à 3 fichiers)
- 4 investissements totaux: pack_level = 4 (accès à 4 fichiers)
- 5+ investissements totaux: pack_level = 5 (accès illimité)

IMPORTANT: Le pack_level ne diminue JAMAIS, il reste au niveau le plus élevé atteint.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, func

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require')

def update_pack_levels_cumulatif():
    """Met à jour le pack_level de tous les utilisateurs basé sur le total d'investissements."""
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
        
        # Compter TOUS les investissements (actifs + terminés) par utilisateur
        total_investments_query = text("""
            SELECT phone, COUNT(*) as total_count
            FROM investissement
            GROUP BY phone
        """)
        
        result = conn.execute(total_investments_query)
        investments_by_user = result.fetchall()
        
        print(f"📊 Analyse de {len(investments_by_user)} utilisateurs avec investissements...")
        
        updated_count = 0
        downgraded_count = 0
        
        for phone, total_count in investments_by_user:
            # Déterminer le nouveau pack_level basé sur le total d'investissements
            # Règle: 1 produit = 1 fichier téléchargeable
            if total_count >= 5:
                new_level = 5  # Accès illimité (5+ fichiers)
            elif total_count == 4:
                new_level = 4  # 4 fichiers
            elif total_count == 3:
                new_level = 3  # 3 fichiers
            elif total_count == 2:
                new_level = 2  # 2 fichiers
            elif total_count == 1:
                new_level = 1  # 1 fichier
            else:
                new_level = 0  # 0 investissement = pas d'accès
            
            # Récupérer le pack_level actuel
            current_result = conn.execute(text("""
                SELECT pack_level 
                FROM "user" 
                WHERE phone = :phone
            """), {"phone": phone})
            
            current_row = current_result.fetchone()
            current_level = current_row[0] if current_row else 1
            
            # Ne mettre à jour que si le nouveau niveau est supérieur ou égal
            # (le pack_level ne diminue jamais)
            if new_level >= current_level:
                if new_level > current_level:
                    conn.execute(text("""
                        UPDATE "user" 
                        SET pack_level = :level
                        WHERE phone = :phone
                    """), {"level": new_level, "phone": phone})
                    updated_count += 1
                    print(f"   ✅ {phone}: {current_level} → {new_level} ({total_count} investissements)")
            else:
                # Cas spécial: on garde l'ancien niveau même si inférieur
                # car le pack_level ne diminue jamais
                downgraded_count += 1
                print(f"   ⚠️  {phone}: garde niveau {current_level} (nouveau calcul: {new_level})")
        
        conn.commit()
        
        print(f"\n✅ {updated_count} utilisateurs mis à jour avec succès!")
        if downgraded_count > 0:
            print(f"⚠️  {downgraded_count} utilisateurs gardent leur ancien niveau (règle de non-régression)")
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
            if level == 0:
                access_text = "Pas d'accès PDF (0 investissement)"
            elif level == 1:
                access_text = "Accès à 1 fichier (1 investissement)"
            elif level == 2:
                access_text = "Accès à 2 fichiers (2 investissements)"
            elif level == 3:
                access_text = "Accès à 3 fichiers (3 investissements)"
            elif level == 4:
                access_text = "Accès à 4 fichiers (4 investissements)"
            elif level >= 5:
                access_text = "ACCÈS ILLIMITÉ (5+ investissements)"
            
            print(f"   Pack Level {level}: {count} utilisateurs - {access_text}")

if __name__ == "__main__":
    print("🚀 Mise à jour cumulative des pack_levels...")
    print("=" * 60)
    print("Règle: 1 produit acheté = 1 fichier téléchargeable")
    print("       Le pack_level ne diminue jamais")
    print("=" * 60)
    update_pack_levels_cumulatif()
    print("=" * 60)
    print("✅ Terminé!")