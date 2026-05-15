#!/usr/bin/env python
"""
Script pour créer un utilisateur administrateur.
Exécution : python create_admin.py
"""

import os
import sys
from datetime import datetime

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
import uuid

def create_admin_user():
    """Crée un utilisateur administrateur."""
    
    with app.app_context():
        # Vérifier s'il existe déjà un admin
        existing_admin = User.query.filter_by(is_admin=True).first()
        
        if existing_admin:
            print(f"⚠️ Un administrateur existe déjà :")
            print(f"   Téléphone: {existing_admin.phone}")
            print(f"   Email: {existing_admin.email}")
            print(f"   Nom: {existing_admin.username}")
            print(f"\n💡 Pour créer un autre admin, supprimez d'abord l'admin existant.")
            return existing_admin
        
        # Générer des identifiants admin
        admin_phone = "admin_" + str(uuid.uuid4())[:8]
        admin_email = "jk840945@icloud.com"
        admin_username = "Super Admin"
        admin_password = "Admin@2024Secure!"
        
        # Vérifier si l'email existe déjà
        if User.query.filter_by(email=admin_email).first():
            admin_email = f"admin_{uuid.uuid4().hex[:6]}@tokenflow.uk"
        
        # Créer l'utilisateur admin
        new_admin = User(
            username=admin_username,
            email=admin_email,
            phone=admin_phone,
            password=admin_password,
            is_admin=True,
            is_banned=False,
            email_verified=True,
            otp_verified=True,
            solde_total=0,
            solde_depot=0,
            solde_revenu=0,
            solde_parrainage=0,
            referral_code="ADMIN001",
            date_creation=datetime.utcnow()
        )
        
        db.session.add(new_admin)
        db.session.commit()
        
        print("\n" + "="*60)
        print("🎉 UTILISATEUR ADMINISTRATEUR CRÉÉ AVEC SUCCÈS !")
        print("="*60)
        print("\n📋 COORDONNÉES DE L'ADMINISTRATEUR :")
        print(f"   🔹 Téléphone: {admin_phone}")
        print(f"   🔹 Email: {admin_email}")
        print(f"   🔹 Mot de passe: {admin_password}")
        print(f"   🔹 Nom: {admin_username}")
        print("\n🔗 LIEN DE CONNEXION :")
        print(f"   https://votre-domaine.com/connexion")
        print("\n⚠️  IMPORTANT :")
        print("   - Conservez ces informations en lieu sûr")
        print("   - Changez le mot de passe après la première connexion")
        print("   - L'admin a accès à /admin pour gérer la plateforme")
        print("="*60)
        
        return new_admin

if __name__ == "__main__":
    try:
        create_admin_user()
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'admin : {e}")
        import traceback
        traceback.print_exc()