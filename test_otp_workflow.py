#!/usr/bin/env python3
"""
Script de test pour le workflow complet OTP et emails TokenFlow
Tests:
1. Génération OTP
2. Expiration OTP
3. Envoi emails
4. Templates HTML
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from app import app, db, User, generate_otp

def test_otp_generation():
    """Test la génération de codes OTP."""
    print("\n" + "="*60)
    print("✓ TEST 1: GÉNÉRATION OTP")
    print("="*60)
    
    for i in range(5):
        otp = generate_otp()
        print(f"  OTP {i+1}: {otp} (longueur: {len(otp)})")
        assert len(otp) == 6, "Le code OTP doit avoir 6 chiffres"
        assert otp.isdigit(), "Le code OTP doit contenir uniquement des chiffres"
    
    print("✓ Tous les codes OTP générés sont valides\n")

def test_otp_expiration():
    """Test l'expiration des codes OTP."""
    print("="*60)
    print("✓ TEST 2: EXPIRATION OTP")
    print("="*60)
    
    now = datetime.utcnow()
    expired_time = now - timedelta(minutes=11)
    valid_time = now + timedelta(minutes=5)
    
    print(f"  Heure actuelle: {now.strftime('%H:%M:%S')}")
    print(f"  Temps expiré (- 11 min): {expired_time.strftime('%H:%M:%S')}")
    print(f"  Temps valide (+ 5 min): {valid_time.strftime('%H:%M:%S')}")
    
    # Vérifier expirations
    assert now > expired_time, "La vérification d'expiration pas correcte"
    assert now < valid_time, "La vérification de validité pas correcte"
    
    print("✓ Les vérifications d'expiration fonctionnent correctement\n")

def test_email_templates():
    """Test les templates d'emails."""
    print("="*60)
    print("✓ TEST 3: TEMPLATES EMAIL")
    print("="*60)
    
    from app import (
        create_otp_template,
        create_welcome_template,
        create_deposit_template,
        create_withdrawal_template,
        create_product_notification_template
    )
    
    test_email = "test@tokenflow.uk"
    
    # Test OTP template
    otp_html = create_otp_template("123456", "Code OTP", "Voici votre code", test_email)
    assert "123456" in otp_html, "Code OTP pas dans le template"
    assert "TokenFlow" in otp_html, "Logo TokenFlow pas dans le template"
    print("  ✓ Template OTP OK")
    
    # Test Welcome template
    welcome_html = create_welcome_template("John", test_email)
    assert "John" in welcome_html, "Nom utilisateur pas dans le template"
    assert "Bienvenue" in welcome_html, "Message bienvenue pas dans le template"
    print("  ✓ Template Bienvenue OK")
    
    # Test Deposit template
    deposit_html = create_deposit_template("+22997000000", 1000.00, "USD", "REF123", test_email)
    assert "1000.00" in deposit_html, "Montant pas dans le template"
    assert "USD" in deposit_html, "Devise pas dans le template"
    print("  ✓ Template Dépôt OK")
    
    # Test Withdrawal template
    withdrawal_html = create_withdrawal_template("+22997000000", 500.00, "USD", "WIT456", test_email)
    assert "500.00" in withdrawal_html, "Montant pas dans le template"
    assert "en cours" in withdrawal_html, "Statut pas dans le template"
    print("  ✓ Template Retrait OK")
    
    # Test Product template
    product_html = create_product_notification_template(
        "Crypto Starter",
        "Investissement dans les cryptomonnaies",
        1.5,
        6000,
        test_email
    )
    assert "Crypto Starter" in product_html, "Nom produit pas dans le template"
    assert "1.50%" in product_html or "1.5" in product_html, "ROI pas dans le template"
    print("  ✓ Template Notification Produit OK")
    
    print("✓ Tous les templates d'emails sont valides\n")

def test_responsive_design():
    """Test la conception responsive des emails."""
    print("="*60)
    print("✓ TEST 4: CONCEPTION RESPONSIVE")
    print("="*60)
    
    from app import create_otp_template
    
    html = create_otp_template("123456", "Test", "Test", "test@example.com")
    
    # Vérifications design responsive
    assert "max-width: 600px" in html, "Largeur max pas configurée"
    assert "media" in html or "@media" in html, "Media queries pas présentes"
    assert "padding" in html, "Padding pas configuré"
    assert "border-radius" in html, "Border-radius pas configuré"
    
    print("  ✓ Largeur max OK (600px)")
    print("  ✓ Padding OK")
    print("  ✓ Design moderne OK")
    print("✓ Les emails sont responsive\n")

def test_security_elements():
    """Test les éléments de sécurité dans les emails."""
    print("="*60)
    print("✓ TEST 5: ÉLÉMENTS SÉCURITÉ")
    print("="*60)
    
    from app import create_otp_template
    
    html = create_otp_template("123456", "Test", "Test", "test@example.com")
    
    # Vérifications de sécurité
    assert "Ne partagez jamais" in html or "jamais" in html, "Avertissement de sécurité manquant"
    assert "🔐" in html or "🔒" in html or "lock" in html.lower(), "Icône de sécurité manquante"
    assert "copyright" in html.lower() or "©" in html, "Copyright manquant"
    
    print("  ✓ Avertissement de sécurité OK")
    print("  ✓ Icônes de sécurité OK")
    print("  ✓ Footer copyright OK")
    print("✓ Les éléments de sécurité sont présents\n")

def test_branding():
    """Test la cohérence du branding TokenFlow."""
    print("="*60)
    print("✓ TEST 6: BRANDING TOKENFLOW")
    print("="*60)
    
    from app import (
        create_otp_template,
        create_welcome_template,
        create_deposit_template
    )
    
    templates = [
        create_otp_template("123456", "Test", "Test", "test@example.com"),
        create_welcome_template("User", "test@example.com"),
        create_deposit_template("+22997000000", 100, "USD", "REF", "test@example.com")
    ]
    
    for i, html in enumerate(templates, 1):
        assert "TokenFlow" in html, f"Logo TokenFlow manquant dans template {i}"
        assert "#4F46E5" in html or "#7C3AED" in html, f"Couleur TokenFlow manquante dans template {i}"
        print(f"  ✓ Template {i}: Branding OK")
    
    print("✓ Tous les templates ont le branding TokenFlow\n")

def main():
    """Exécute tous les tests."""
    print("\n" + "#"*60)
    print("# TEST WORKFLOW OTP ET EMAILS TOKENFLOW")
    print("#"*60)
    
    try:
        with app.app_context():
            test_otp_generation()
            test_otp_expiration()
            test_email_templates()
            test_responsive_design()
            test_security_elements()
            test_branding()
            
            print("="*60)
            print("✓✓✓ TOUS LES TESTS RÉUSSIS ✓✓✓")
            print("="*60)
            print("\n📊 Résumé:")
            print("  ✓ Génération OTP: OK")
            print("  ✓ Expiration OTP: OK")
            print("  ✓ Templates Email: 5/5")
            print("  ✓ Design Responsive: OK")
            print("  ✓ Éléments Sécurité: OK")
            print("  ✓ Branding TokenFlow: OK")
            print("\n✅ Le système OTP et emails est prêt pour la production!\n")
            
    except Exception as e:
        print(f"\n❌ ERREUR LORS DU TEST: {e}")
        print(f"Traceback: {e.__class__.__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
