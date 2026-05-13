"""
Migration script to add OTP verification columns to the User table.
Run with: python add_otp_columns.py
"""
from sqlalchemy import create_engine, text, inspect

# Database URL - same as in app.py
DATABASE_URL = "postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require"

def add_otp_columns():
    """Add OTP verification columns to the user table."""
    print("🔗 Connecting to database...")
    print(f"Database URL: {DATABASE_URL[:50]}...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ Connected to database successfully!")
        
        # Check if columns already exist
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        print(f"📋 Existing columns: {columns}")
        
        with engine.connect() as conn:
            # Add otp_code column
            if 'otp_code' not in columns:
                conn.execute(text('''
                    ALTER TABLE "user" 
                    ADD COLUMN otp_code VARCHAR(6) NULL
                '''))
                print("✅ Colonne 'otp_code' ajoutée")
            else:
                print("ℹ️ Colonne 'otp_code' déjà existante")
            
            # Add otp_expires column
            if 'otp_expires' not in columns:
                conn.execute(text('''
                    ALTER TABLE "user" 
                    ADD COLUMN otp_expires TIMESTAMP NULL
                '''))
                print("✅ Colonne 'otp_expires' ajoutée")
            else:
                print("ℹ️ Colonne 'otp_expires' déjà existante")
            
            # Add otp_verified column
            if 'otp_verified' not in columns:
                conn.execute(text('''
                    ALTER TABLE "user" 
                    ADD COLUMN otp_verified BOOLEAN DEFAULT FALSE
                '''))
                print("✅ Colonne 'otp_verified' ajoutée")
            else:
                print("ℹ️ Colonne 'otp_verified' déjà existante")
            
            conn.commit()
        
        print("🎉 Migration des colonnes OTP terminée !")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_otp_columns()