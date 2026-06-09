#!/usr/bin/env python3
"""
📧 Script de test d'envoi d'emails - TokenFlow

Ce script teste l'envoi d'emails via SMTP et génère les clés VAPID si nécessaire.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def test_email_sending():
    """Teste l'envoi d'un email de test."""
    print("\n📧 TEST D'ENVOI D'EMAIL")
    print("=" * 60)
    
    try:
        # Import après que les variables d'environnement soient chargées
        from app import send_email_smtp
        
        # Email de test
        test_email = "fredogary7@gmail.com"  # À remplacer par votre email
        
        print(f"\nAjout du chemin d'import d'app.py...")
        
        # Créer un email de test
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #F1F5F9; margin: 0; padding: 20px;">
            <table style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden;">
                <tr>
                    <td style="padding: 40px; text-align: center; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);">
                        <h1 style="margin: 0; color: white; font-size: 24px;">🧪 Test TokenFlow</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 40px;">
                        <h2 style="color: #0F172A;">Email de Test</h2>
                        <p style="color: #475569; line-height: 1.6;">
                            Cet email confirme que votre configuration SMTP fonctionne correctement.
                        </p>
                        <p style="color: #475569;">
                            ✅ L'authentification SMTP est valide<br>
                            ✅ La connexion TLS fonctionne<br>
                            ✅ Les emails peuvent être envoyés
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px 40px 40px;">
                        <a href="https://flowtoken.uk" style="display: inline-block; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); color: white; text-decoration: none; padding: 12px 30px; border-radius: 8px; font-weight: bold;">
                            Accéder à TokenFlow
                        </a>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px; background-color: #F8FAFC; border-top: 1px solid #E2E8F0; text-align: center; font-size: 12px; color: #64748B;">
                        © 2024 TokenFlow. Plateforme fintech sécurisée.
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_content = \"\"\"Email de test TokenFlow\n\nCet email confirme que votre configuration SMTP fonctionne correctement.\"\"\"\n        \n        print(f\"Envoi d'un email de test à: {test_email}\")\n        success, error = send_email_smtp(\n            test_email,\n            \"🧪 Test Email - TokenFlow\",\n            html_content,\n            text_content\n        )\n        \n        if success:\n            print(\"✅ Email envoyé avec succès!\")\n            return True\n        else:\n            print(f\"❌ Erreur lors de l'envoi: {error}\")\n            return False\n            \n    except ImportError as e:\n        print(f\"❌ Erreur d'import: {e}\")\n        print(\"Assurez-vous d'être dans le bon répertoire et que app.py existe.\")\n        return False\n    except Exception as e:\n        print(f\"❌ Erreur: {type(e).__name__}: {e}\")\n        import traceback\n        traceback.print_exc()\n        return False\n\ndef test_vapid_generation():\n    \"\"\"Teste la génération des clés VAPID.\"\"\"\n    print(\"\\n🔑 TEST GÉNÉRATION CLÉS VAPID\")\n    print(\"=\" * 60)\n    \n    try:\n        from app import get_vapid_keys\n        \n        private_key, public_key = get_vapid_keys()\n        \n        if private_key and public_key:\n            print(f\"✅ Clés VAPID générées avec succès\")\n            print(f\"   Private key: {private_key[:20]}... ({len(private_key)} caractères)\")\n            print(f\"   Public key: {public_key[:20]}... ({len(public_key)} caractères)\")\n            return True\n        else:\n            print(f\"❌ Impossible de générer les clés VAPID\")\n            return False\n            \n    except Exception as e:\n        print(f\"❌ Erreur: {type(e).__name__}: {e}\")\n        return False\n\ndef test_otp_generation():\n    \"\"\"Teste la génération de codes OTP.\"\"\"\n    print(\"\\n🔐 TEST GÉNÉRATION CODES OTP\")\n    print(\"=\" * 60)\n    \n    try:\n        from app import generate_otp\n        \n        otps = [generate_otp() for _ in range(5)]\n        \n        all_valid = all(len(otp) == 6 and otp.isdigit() for otp in otps)\n        \n        if all_valid:\n            print(\"✅ Codes OTP générés correctement\")\n            for i, otp in enumerate(otps, 1):\n                print(f\"   {i}. {otp}\")\n            return True\n        else:\n            print(f\"❌ Codes OTP invalides: {otps}\")\n            return False\n            \n    except Exception as e:\n        print(f\"❌ Erreur: {type(e).__name__}: {e}\")\n        return False\n\nif __name__ == \"__main__\":\n    print(\"\\n\" + \"=\" * 60)\n    print(\"🧪 TESTS D'ENVOI - TOKENFLOW\")\n    print(\"=\" * 60)\n    \n    results = []\n    \n    # Test 1: Configuration\n    print(\"\\n1️⃣  Vérification de la configuration...\")\n    from check_config import ConfigChecker\n    checker = ConfigChecker()\n    checker.check_smtp()\n    if checker.errors:\n        print(\"\\n❌ La configuration SMTP est incorrecte.\")\n        print(\"Veuillez d'abord corriger la configuration.\")\n        sys.exit(1)\n    \n    # Test 2: OTP\n    print(\"\\n2️⃣  Test de génération OTP...\")\n    results.append((\"OTP Generation\", test_otp_generation()))\n    \n    # Test 3: VAPID\n    print(\"\\n3️⃣  Test de génération VAPID...\")\n    results.append((\"VAPID Generation\", test_vapid_generation()))\n    \n    # Test 4: Email\n    print(\"\\n4️⃣  Test d'envoi d'email...\")\n    results.append((\"Email Sending\", test_email_sending()))\n    \n    # Summary\n    print(\"\\n\" + \"=\" * 60)\n    print(\"📊 RÉSUMÉ DES TESTS\")\n    print(\"=\" * 60)\n    \n    for test_name, result in results:\n        status = \"✅\" if result else \"❌\"\n        print(f\"{status} {test_name}\")\n    \n    all_passed = all(result for _, result in results)\n    \n    print(\"\\n\" + \"=\" * 60)\n    if all_passed:\n        print(\"🟢 TOUS LES TESTS RÉUSSIS\")\n    else:\n        print(\"🔴 CERTAINS TESTS ONT ÉCHOUÉ\")\n        print(\"\\nConsultez les messages d'erreur ci-dessus.\")\n    \n    sys.exit(0 if all_passed else 1)
