#!/usr/bin/env python3
"""Run the balance columns migration directly."""
import sys
sys.path.insert(0, '.')

from app import app, db
from sqlalchemy import text, inspect

output_lines = []

def log(msg):
    output_lines.append(msg)
    print(msg)

with app.app_context():
    log("🔍 Checking current columns in user table...")
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('user')]
    log(f"Current columns: {columns}")
    
    if 'balance_usd' not in columns:
        log("\n➕ Adding balance_usd column...")
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE "user" ADD COLUMN balance_usd REAL DEFAULT 0.0'))
            conn.commit()
        log("✅ Colonne 'balance_usd' ajoutée")
    else:
        log("\nℹ️ Colonne 'balance_usd' déjà existante")
    
    if 'balance_eur' not in columns:
        log("\n➕ Adding balance_eur column...")
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE "user" ADD COLUMN balance_eur REAL DEFAULT 0.0'))
            conn.commit()
        log("✅ Colonne 'balance_eur' ajoutée")
    else:
        log("\nℹ️ Colonne 'balance_eur' déjà existante")
    
    log("\n💰 Migrating solde_total to balance_usd...")
    with db.engine.connect() as conn:
        result = conn.execute(text('''
            UPDATE "user" 
            SET balance_usd = solde_total 
            WHERE balance_usd IS NULL OR balance_usd = 0
        '''))
        conn.commit()
        log(f"✅ {result.rowcount} utilisateurs migrés vers balance_usd")
    
    log("\n💶 Calculating balance_eur from balance_usd...")
    with db.engine.connect() as conn:
        result = conn.execute(text('''
            UPDATE "user" 
            SET balance_eur = balance_usd * 0.92 
            WHERE balance_eur IS NULL OR balance_eur = 0
        '''))
        conn.commit()
        log(f"✅ balance_eur calculé pour {result.rowcount} utilisateurs")
    
    log("\n🎉 Migration balance_usd/balance_eur terminée !")
    
    # Show sample data
    log("\n📊 Sample data:")
    with db.engine.connect() as conn:
        result = conn.execute(text('''
            SELECT email, solde_total, balance_usd, balance_eur 
            FROM "user" 
            LIMIT 5
        '''))
        log("Email | Solde Total | Balance USD | Balance EUR")
        log("-" * 60)
        for row in result.fetchall():
            log(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")

# Write output to file
with open('migration_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))