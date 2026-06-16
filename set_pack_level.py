#!/usr/bin/env python
"""Script pour définir le pack_level d'un utilisateur"""

import os
import sys

# Ajouter le dossier China au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User

def set_pack_level(email, level):
    """Définir le pack_level d'un utilisateur par email"""
    with app.app_context():
        user = User.query.filter_by(email=email.lower()).first()
        if user:
            print(f"Utilisateur trouvé: {user.username} ({user.email})")
            print(f"Pack level actuel: {user.pack_level}")
            user.pack_level = level
            db.session.commit()
            print(f"✅ Pack level mis à jour à: {level}")
        else:
            print(f"❌ Aucun utilisateur trouvé avec l'email: {email}")

if __name__ == "__main__":
    # Email de l'utilisateur à mettre à jour
    email = "1xthom14@gmail.com"
    level = 5  # Niveau maximum pour accès illimité
    
    if len(sys.argv) > 2:
        email = sys.argv[1]
        level = int(sys.argv[2])
    
    set_pack_level(email, level)