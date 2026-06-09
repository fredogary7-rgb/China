#!/usr/bin/env python3
"""
🧪 Script de vérification et test - TokenFlow Configuration Checker

Ce script vérifie que toutes les configurations sont correctes et prêtes pour la production.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

class ConfigChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success = []
    
    def check_smtp(self):
        """Vérifie la configuration SMTP."""
        print("\n📧 VÉRIFICATION SMTP")
        print("=" * 60)
        
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = os.getenv('SMTP_PORT')
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        email_from = os.getenv('EMAIL_FROM')
        
        if not smtp_server:
            self.errors.append("❌ SMTP_SERVER non défini")
        else:
            print(f"✅ SMTP_SERVER: {smtp_server}")
            self.success.append("SMTP_SERVER")
        
        if not smtp_port:
            self.errors.append("❌ SMTP_PORT non défini")
        else:
            print(f"✅ SMTP_PORT: {smtp_port}")
            self.success.append("SMTP_PORT")
        
        if not smtp_user:
            self.errors.append("❌ SMTP_USER non défini")
        else:
            print(f"✅ SMTP_USER: {smtp_user}")
            self.success.append("SMTP_USER")
        
        if not smtp_password:
            self.errors.append("❌ SMTP_PASSWORD non défini")
        else:
            print(f"✅ SMTP_PASSWORD: {'*' * len(smtp_password)} ({len(smtp_password)} caractères)")
            self.success.append("SMTP_PASSWORD")
            
            if len(smtp_password) < 10:
                self.warnings.append("⚠️  SMTP_PASSWORD semble trop court (< 10 caractères)")
        
        if not email_from:
            self.warnings.append("⚠️  EMAIL_FROM non défini (utilisant valeur par défaut)")
        else:
            print(f"✅ EMAIL_FROM: {email_from}")
            self.success.append("EMAIL_FROM")
    
    def check_vapid(self):
        """Vérifie la configuration VAPID."""
        print("\n🔑 VÉRIFICATION VAPID (Web Push)")
        print("=" * 60)
        
        vapid_private = os.getenv('VAPID_PRIVATE_KEY')
        vapid_public = os.getenv('VAPID_PUBLIC_KEY')
        
        if not vapid_private:
            self.warnings.append("⚠️  VAPID_PRIVATE_KEY non défini (sera généré automatiquement)")
        else:
            print(f"✅ VAPID_PRIVATE_KEY: {vapid_private[:20]}... ({len(vapid_private)} caractères)")
            self.success.append("VAPID_PRIVATE_KEY")
        
        if not vapid_public:
            self.warnings.append("⚠️  VAPID_PUBLIC_KEY non défini (sera généré automatiquement)")
        else:
            print(f"✅ VAPID_PUBLIC_KEY: {vapid_public[:20]}... ({len(vapid_public)} caractères)")
            self.success.append("VAPID_PUBLIC_KEY")
    
    def check_oauth_google(self):
        """Vérifie la configuration OAuth Google."""
        print("\n🔐 VÉRIFICATION OAUTH GOOGLE")
        print("=" * 60)
        
        google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not google_client_id:
            self.warnings.append("⚠️  GOOGLE_CLIENT_ID non défini")
        else:
            print(f"✅ GOOGLE_CLIENT_ID: {google_client_id}")
            self.success.append("GOOGLE_CLIENT_ID")
        
        if not google_client_secret:
            self.warnings.append("⚠️  GOOGLE_CLIENT_SECRET non défini")
        else:
            print(f"✅ GOOGLE_CLIENT_SECRET: {'*' * len(google_client_secret)} ({len(google_client_secret)} caractères)")
            self.success.append("GOOGLE_CLIENT_SECRET")
    
    def check_oauth_apple(self):
        """Vérifie la configuration OAuth Apple."""
        print("\n🍎 VÉRIFICATION OAUTH APPLE")
        print("=" * 60)
        
        apple_team_id = os.getenv('APPLE_TEAM_ID')
        apple_client_id = os.getenv('APPLE_CLIENT_ID')
        apple_key_id = os.getenv('APPLE_KEY_ID')
        apple_private_key = os.getenv('APPLE_PRIVATE_KEY')
        
        if not apple_team_id:
            self.warnings.append("⚠️  APPLE_TEAM_ID non défini")
        else:
            print(f"✅ APPLE_TEAM_ID: {apple_team_id}")
            self.success.append("APPLE_TEAM_ID")
        
        if not apple_client_id:
            self.warnings.append("⚠️  APPLE_CLIENT_ID non défini")
        else:
            print(f"✅ APPLE_CLIENT_ID: {apple_client_id}")
            self.success.append("APPLE_CLIENT_ID")
        
        if not apple_key_id:
            self.warnings.append("⚠️  APPLE_KEY_ID non défini")
        else:
            print(f"✅ APPLE_KEY_ID: {apple_key_id}")
            self.success.append("APPLE_KEY_ID")
        
        if not apple_private_key:
            self.warnings.append("⚠️  APPLE_PRIVATE_KEY non défini")
        else:
            key_preview = apple_private_key[:20] + "..." + apple_private_key[-20:]
            print(f"✅ APPLE_PRIVATE_KEY: {key_preview}")
            self.success.append("APPLE_PRIVATE_KEY")
    
    def check_database(self):
        """Vérifie la configuration de la base de données."""
        print("\n🗄️  VÉRIFICATION BASE DE DONNÉES")
        print("=" * 60)
        
        database_url = os.getenv('DATABASE_URL', os.getenv('SQLALCHEMY_DATABASE_URI'))
        
        if not database_url:
            self.warnings.append("⚠️  DATABASE_URL non défini")
        else:
            # Masquer les credentials sensibles
            if '@' in database_url:
                parts = database_url.split('@')
                creds = parts[0].split('://')
                masked = creds[0] + "://***:***@" + parts[1]
            else:
                masked = database_url
            
            print(f"✅ DATABASE_URL: {masked}")
            self.success.append("DATABASE_URL")
    
    def test_smtp_connection(self):
        """Teste la connexion SMTP."""
        print("\n🧪 TEST DE CONNEXION SMTP")
        print("=" * 60)
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
                print("⚠️  Configuration SMTP incomplète, test ignoré")
                return
            
            print(f"Connexion à {smtp_server}:{smtp_port}...")
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=5)
            server.starttls()
            print("✅ TLS activé")
            
            server.login(smtp_user, smtp_password)
            print("✅ Authentification réussie")
            
            server.quit()
            print("✅ Connexion SMTP OK")
            self.success.append("TEST_SMTP")
            
        except smtplib.SMTPAuthenticationError as e:
            self.errors.append(f"❌ Erreur authentification SMTP: {e}")
        except smtplib.SMTPConnectError as e:
            self.errors.append(f"❌ Erreur connexion SMTP: {e}")
        except Exception as e:
            self.errors.append(f"❌ Erreur test SMTP: {type(e).__name__}: {e}")
    
    def print_summary(self):
        """Affiche un résumé des résultats."""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ")
        print("=" * 60)
        
        print(f"\n✅ Succès: {len(self.success)}")
        for item in self.success:
            print(f"   • {item}")
        
        if self.warnings:
            print(f"\n⚠️  Avertissements: {len(self.warnings)}")
            for item in self.warnings:
                print(f"   • {item}")
        
        if self.errors:
            print(f"\n❌ Erreurs: {len(self.errors)}")
            for item in self.errors:
                print(f"   • {item}")
        
        print("\n" + "=" * 60)
        
        if self.errors:
            print("🔴 CONFIGURATION INCOMPLÈTE - ERREURS À CORRIGER")
            return False
        elif self.warnings:
            print("🟡 CONFIGURATION PARTIELLE - CERTAINS SERVICES DÉSACTIVÉS")
            return True
        else:
            print("🟢 CONFIGURATION COMPLÈTE ET VALIDE")
            return True
    
    def run(self):
        """Exécute toutes les vérifications."""
        print("\n" + "=" * 60)
        print("🔧 VÉRIFICATION DE CONFIGURATION - TOKENFLOW")
        print("=" * 60)
        
        self.check_smtp()
        self.check_vapid()
        self.check_oauth_google()
        self.check_oauth_apple()
        self.check_database()
        
        print("\n🧪 Tentative de connexion SMTP...")
        self.test_smtp_connection()
        
        success = self.print_summary()
        
        print("\n📚 Pour plus d'informations, consultez: CONFIG_GUIDE.md")
        
        return success

if __name__ == "__main__":
    checker = ConfigChecker()
    success = checker.run()
    sys.exit(0 if success else 1)
