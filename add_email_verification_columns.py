"""
Migration script to add email verification columns to the User table.
Run with: python add_email_verification_columns.py
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

load_dotenv()

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require')

def add_email_verification_columns():
    """Add email verification columns to the user table."""
    engine = create_engine(DATABASE_URL)
    
    # Check if columns already exist
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('user')]
    
    with engine.connect() as conn:
        # Add email_verified column
        if 'email_verified' not in columns:
            conn.execute(text('''
                ALTER TABLE "user" 
                ADD COLUMN email_verified BOOLEAN DEFAULT FALSE
            '''))
            print("✅ Colonne 'email_verified' ajoutée")
        else:
            print("ℹ️ Colonne 'email_verified' déjà existante")
        
        # Add email_verification_token column
        if 'email_verification_token' not in columns:
            conn.execute(text('''
                ALTER TABLE "user" 
                ADD COLUMN email_verification_token VARCHAR(200) NULL
            '''))
            print("✅ Colonne 'email_verification_token' ajoutée")
        else:
            print("ℹ️ Colonne 'email_verification_token' déjà existante")
        
        # Add verification_token_expires column
        if 'verification_token_expires' not in columns:
            conn.execute(text('''
                ALTER TABLE "user" 
                ADD COLUMN verification_token_expires TIMESTAMP NULL
            '''))
            print("✅ Colonne 'verification_token_expires' ajoutée")
        else:
            print("ℹ️ Colonne 'verification_token_expires' déjà existante")
        
        conn.commit()
    
    print("🎉 Migration des colonnes de vérification email terminée !")

if __name__ == "__main__":
    add_email_verification_columns()