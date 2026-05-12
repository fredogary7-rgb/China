"""
Script de migration pour ajouter les nouvelles colonnes à la table user
Exécuter avec: python add_user_columns.py
"""
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = "postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require"

def add_columns():
    engine = create_engine(DATABASE_URL)
    
    columns_to_add = [
        ("username", "VARCHAR(100)"),
        ("email", "VARCHAR(120)"),
        ("google_id", "VARCHAR(100)"),
        ("apple_id", "VARCHAR(100)"),
    ]
    
    with engine.connect() as conn:
        for column_name, column_type in columns_to_add:
            try:
                # Check if column exists
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'user' AND column_name = '{column_name}'
                """))
                
                if result.fetchone() is None:
                    # Column doesn't exist, add it
                    conn.execute(text(f"""
                        ALTER TABLE "user" 
                        ADD COLUMN {column_name} {column_type}
                    """))
                    conn.commit()
                    print(f"✅ Colonne '{column_name}' ajoutée avec succès")
                else:
                    print(f"ℹ️ Colonne '{column_name}' existe déjà")
                    
            except Exception as e:
                print(f"❌ Erreur pour la colonne '{column_name}': {e}")
        
        print("\n🎉 Migration terminée !")

if __name__ == "__main__":
    add_columns()