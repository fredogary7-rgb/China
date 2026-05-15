#!/usr/bin/env python
"""
Script pour mettre à jour l'email de l'administrateur existant.
Exécution : python update_admin_email.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User

def update_admin_email():
    """Met à jour l'email de l'admin existant."""
    
    with app.app_context():
        admin = User.query.filter_by(is_admin=True).first()
        
        if not admin:
            print("❌ Aucun administrateur trouvé. Exécutez d'abord create_admin.py")
            return
        
        new_email = "jk840945@icloud.com"
        
        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        existing_user = User.query.filter_by(email=new_email).first()
        if existing_user and existing_user.id != admin.id:
            print(f"⚠️ Cet email est déjà utilisé par un autre utilisateur (ID: {existing_user.id})")
            return
        
        old_email = admin.email
        admin.email = new_email
        admin.email_verified = True
        db.session.commit()
        
        print("\n" + "="*60)
        print("✅ EMAIL DE L'ADMINISTRATEUR MIS À JOUR !")
        print("="*60)
        print(f"\n📋 NOUVELLES INFORMATIONS :")
        print(f"   🔹 Téléphone: {admin.phone}")
        print(f"   🔹 Email (ancien): {old_email}")
        print(f"   🔹 Email (nouveau): {new_email}")
        print(f"   🔹 Nom: {admin.username}")
        print("="*60)

if __name__ == "__main__":
    try:
        update_admin_email()
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour : {e}")
        import traceback
        traceback.print_exc()