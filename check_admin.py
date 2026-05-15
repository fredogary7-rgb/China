#!/usr/bin/env python
"""Script pour vérifier/créer l'admin"""
import sys
sys.path.insert(0, '.')
from app import app, db, User

with app.app_context():
    admin = User.query.filter_by(is_admin=True).first()
    if admin:
        print("=" * 50)
        print("✅ ADMIN TROUVE :")
        print(f"   Telephone: {admin.phone}")
        print(f"   Email: {admin.email}")
        print(f"   Nom: {admin.username}")
        print(f"   Mot de passe: {admin.password}")
        print("=" * 50)
    else:
        print("❌ Aucun admin trouve. Executez create_admin.py")