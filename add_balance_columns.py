#!/usr/bin/env python3
"""Add balance_usd and balance_eur columns to user table using Flask-SQLAlchemy."""
from app import db, app
from sqlalchemy import inspect, text

with app.app_context():
    # Check current columns
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('user')]
    
    print(f"Current columns in user table: {columns}")
    
    # Add balance_usd column if not exists
    if 'balance_usd' not in columns:
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE "user" ADD COLUMN balance_usd REAL DEFAULT 0.0'))
            conn.commit()
        print("✅ Added balance_usd column")
    else:
        print("ℹ️ balance_usd column already exists")
    
    # Add balance_eur column if not exists
    if 'balance_eur' not in columns:
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE "user" ADD COLUMN balance_eur REAL DEFAULT 0.0'))
            conn.commit()
        print("✅ Added balance_eur column")
    else:
        print("ℹ️ balance_eur column already exists")
    
    # Migrate existing solde_total to balance_usd
    with db.engine.connect() as conn:
        result = conn.execute(text('''
            UPDATE "user" 
            SET balance_usd = solde_total 
            WHERE balance_usd IS NULL OR balance_usd = 0
        '''))
        conn.commit()
        print(f"✅ Migrated {result.rowcount} users' balance to balance_usd")
    
    # Calculate EUR balance (1 USD = 0.92 EUR)
    with db.engine.connect() as conn:
        result = conn.execute(text('''
            UPDATE "user" 
            SET balance_eur = balance_usd * 0.92 
            WHERE balance_eur IS NULL OR balance_eur = 0
        '''))
        conn.commit()
        print(f"✅ Calculated EUR balance for {result.rowcount} users")
    
    # Show sample data
    with db.engine.connect() as conn:
        result = conn.execute(text('''
            SELECT email, solde_total, balance_usd, balance_eur 
            FROM "user" 
            LIMIT 5
        '''))
        print("\n📊 Sample data:")
        print("Email | Solde Total (USD) | Balance USD | Balance EUR")
        print("-" * 60)
        for row in result.fetchall():
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")
    
    print("\n✅ Balance columns migration completed successfully!")