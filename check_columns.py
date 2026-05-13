#!/usr/bin/env python3
from app import db, app
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('user')]
    
    with open('check_output.txt', 'w') as f:
        f.write(f"Columns in user table: {columns}\n")
        
        if 'balance_usd' in columns and 'balance_eur' in columns:
            f.write("✅ balance_usd and balance_eur columns exist!\n")
        else:
            f.write("❌ Columns not found\n")