"""
Script pour ajouter la colonne pack_level à la table user.
Usage: python add_pack_level_column.py
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require')

def add_pack_level_column():
    """Ajoute la colonne pack_level à la table user si elle n'existe pas."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user' AND column_name = 'pack_level'
        """))
        
        if result.fetchone():
            print("✅ La colonne 'pack_level' existe déjà.")
        else:
            # Add the column
            conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN pack_level INTEGER DEFAULT 1
            """))
            conn.commit()
            print("✅ Colonne 'pack_level' ajoutée avec succès!")
            print("   - Type: INTEGER")
            print("   - Valeur par défaut: 1 (niveau de base)")
            print("")
            print("Niveaux d'accès:")
            print("   - Niveau 1: Pas d'accès aux PDFs")
            print("   - Niveau 2: Accès aux PDFs niveau 1-2")
            print("   - Niveau 3: Accès aux PDFs niveau 1-3")
            print("   - Niveau 4: Accès aux PDFs niveau 1-4")
            print("   - Niveau 5+: Accès à TOUS les PDFs")

if __name__ == "__main__":
    add_pack_level_column()