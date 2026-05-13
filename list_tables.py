#!/usr/bin/env python3
"""List all tables in the database."""
from app import db, app
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    with open('tables_list.txt', 'w', encoding='utf-8') as f:
        f.write("Tables in database:\n")
        for table in sorted(tables):
            f.write(f"  - {table}\n")
    print("Results written to tables_list.txt")
