import os
import random
import string
import threading
import time
import uuid
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlencode
import re
import requests

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text, distinct
from werkzeug.middleware.proxy_fix import ProxyFix

TRANSLATIONS = {
    "fr": {
        "welcome": "Bienvenue",
        "login": "Connexion",
        "logout": "Déconnexion",
        "dashboard": "Tableau de bord",
        "profile": "Profil",
        "deposit": "Dépôt",
        "withdraw": "Retrait",
        "invest": "Investir",
        "referral": "Parrainage",
        "support": "Support",
        "balance": "Solde",
        "transactions": "Transactions",
        "settings": "Paramètres"
    },
    "en": {
        "welcome": "Welcome",
        "login": "Login",
        "logout": "Logout",
        "dashboard": "Dashboard",
        "profile": "Profile",
        "deposit": "Deposit",
        "withdraw": "Withdraw",
        "invest": "Invest",
        "referral": "Referral",
        "support": "Support",
        "balance": "Balance",
        "transactions": "Transactions",
        "settings": "Settings"
    }
}

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "ma_cle_ultra_secrete"

# Charger le .env local en forçant la surcharge des variables d'environnement système
load_dotenv(override=True)
print("=" * 60)
print("🔧 Configuration chargée depuis .env (override=True):")
print(f"   SMTP_SERVER = {os.getenv('SMTP_SERVER')}")
print(f"   SMTP_PORT = {os.getenv('SMTP_PORT')}")
print(f"   SMTP_USER = {os.getenv('SMTP_USER')}")
print(f"   SMTP_PASSWORD = {'*' * len(os.getenv('SMTP_PASSWORD', '')) if os.getenv('SMTP_PASSWORD') else 'None'}")
print("=" * 60)

# Configuration pour les URL externes en production
SERVER_NAME = os.getenv('SERVER_NAME', 'flowtoken.uk')
PREFERRED_URL_SCHEME = os.getenv('PREFERRED_URL_SCHEME', 'https')

# Appliquer ProxyFix pour gérer les en-têtes X-Forwarded-* du proxy inverse (nginx, etc.)
# Cela permet à Flask de détecter correctement HTTPS en production
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Forcer le schéma HTTPS pour la génération d'URL
app.config['PREFERRED_URL_SCHEME'] = 'https'
MONEYFUSION_API_KEY = os.getenv("MONEYFUSION_API_KEY")
MONEYFUSION_API_URL = os.getenv("MONEYFUSION_API_URL")

# SoleasPay API Configuration
SOLEAS_API_KEY = os.getenv("SOLEAS_API_KEY", "SP_y7QKkaamPsVTlw8GDDGyzlJ7bmPUvdLorOQqWUXfRLI_AP")
SOLEAS_API_URL = os.getenv("SOLEAS_API_URL", "https://api.soleaspay.com/v1")
SOLEAS_WEBHOOK_SECRET = os.getenv("SOLEAS_WEBHOOK_SECRET", "b42ed39b9e0db71db4556a2dfe1b1ad00dcce656fd4dba033f1947f913f1908bc817588c2edb32d92533a1d162e57ad4b1f7299f39695c5671c3ef07baa6f22a")

# SoleasPay Services by Country
SOLEAS_SERVICES = {
    # 🇨🇲 CAMEROUN
    "CM": [
        {"id": 1, "name": "MOMO CM", "description": "MTN MOBILE MONEY CAMEROUN"},
        {"id": 2, "name": "OM CM", "description": "ORANGE MONEY CAMEROUN"},
    ],

    # 🇨🇮 CÔTE D'IVOIRE
    "CI": [
        {"id": 29, "name": "OM CI", "description": "ORANGE MONEY COTE D'IVOIRE"},
        {"id": 30, "name": "MOMO CI", "description": "MTN MONEY COTE D'IVOIRE"},
        {"id": 31, "name": "MOOV CI", "description": "MOOV COTE D'IVOIRE"},
        {"id": 32, "name": "WAVE CI", "description": "WAVE COTE D'IVOIRE"},
    ],

    # 🇧🇫 BURKINA FASO
    "BF": [
        {"id": 33, "name": "MOOV BF", "description": "MOOV BURKINA FASO"},
        {"id": 34, "name": "OM BF", "description": "ORANGE MONEY BURKINA FASO"},
    ],

    # 🇧🇯 BENIN
    "BJ": [
        {"id": 35, "name": "MOMO BJ", "description": "MTN MONEY BENIN"},
        {"id": 36, "name": "MOOV BJ", "description": "MOOV BENIN"},
    ],

    # 🇹🇬 TOGO
    "TG": [
        {"id": 37, "name": "T-MONEY TG", "description": "T-MONEY TOGO"},
        {"id": 38, "name": "MOOV TG", "description": "MOOV TOGO"},
    ],

    # 🇨🇩 CONGO DRC
    "COD": [
        {"id": 52, "name": "VODACOM COD", "description": "VODACOM CONGO DRC"},
        {"id": 53, "name": "AIRTEL COD", "description": "AIRTEL CONGO DRC"},
        {"id": 54, "name": "ORANGE COD", "description": "ORANGE CONGO DRC"},
    ],

    # 🇨🇬 CONGO BRAZZAVILLE
    "COG": [
        {"id": 55, "name": "AIRTEL COG", "description": "AIRTEL CONGO"},
        {"id": 56, "name": "MOMO COG", "description": "MTN MOMO CONGO"},
    ],

    # 🇬🇦 GABON
    "GAB": [
        {"id": 57, "name": "AIRTEL GAB", "description": "AIRTEL GABON"},
    ],

    # 🇺🇬 UGANDA
    "UGA": [
        {"id": 58, "name": "AIRTEL UGA", "description": "AIRTEL UGANDA"},
        {"id": 59, "name": "MOMO UGA", "description": "MTN MOMO UGANDA"},
    ],

    # 🌍 INTERNATIONAL (Crypto & Digital Payments)
    "INTL": [
        {"id": 3, "name": "BITCOIN", "description": "Bitcoin (BTC)", "type": "CRYPTOCURRENCY"},
        {"id": 4, "name": "PAYPAL_BTN", "description": "PayPal Button", "type": "TRUSTEECURRENCY"},
        {"id": 5, "name": "EUM", "description": "EUM Token", "type": "TRUSTEECURRENCY"},
        {"id": 6, "name": "XPI", "description": "XPI Token", "type": "OTHER"},
        {"id": 7, "name": "PAYPAL", "description": "PayPal", "type": "TRUSTEECURRENCY"},
        {"id": 8, "name": "PM", "description": "Perfect Money", "type": "TRUSTEECURRENCY"},
        {"id": 10, "name": "LITECOIN", "description": "Litecoin (LTC)", "type": "CRYPTOCURRENCY"},
        {"id": 11, "name": "DOGECOIN", "description": "Dogecoin (DOGE)", "type": "CRYPTOCURRENCY"},
    ],
}

# Country Code Mapping
COUNTRY_CODE_MAP = {
    # Cameroun
    "Cameroun": "CM",
    "Cameroon": "CM",

    # Côte d'Ivoire
    "Côte d'Ivoire": "CI",
    "Cote d Ivoire": "CI",
    "Cote dIvoire": "CI",
    "Ivory Coast": "CI",

    # Burkina Faso
    "Burkina Faso": "BF",

    # Bénin
    "Bénin": "BJ",
    "Benin": "BJ",

    # Togo
    "Togo": "TG",

    # Congo DRC
    "Congo DRC": "COD",
    "RDC": "COD",
    "République Démocratique du Congo": "COD",

    # Congo Brazzaville
    "Congo": "COG",
    "Congo Brazzaville": "COG",

    # Gabon
    "Gabon": "GAB",

    # Uganda
    "Uganda": "UGA",
}

def get_soleas_services():
    """Retourne la configuration des services SoleasPay."""
    return SOLEAS_SERVICES

def get_country_code(country_name):
    """Convertit le nom du pays en code pays."""
    return COUNTRY_CODE_MAP.get(country_name, country_name.upper() if len(country_name) == 2 else None)

def get_service_by_id(country_code, service_id):
    """Récupère un service par son ID pour un pays donné."""
    services = SOLEAS_SERVICES.get(country_code, [])
    for service in services:
        if service["id"] == int(service_id):
            return service
    return None

def get_available_countries():
    """Retourne la liste des pays disponibles."""
    countries = []
    for code, services in SOLEAS_SERVICES.items():
        # Trouver le nom du pays depuis COUNTRY_CODE_MAP
        for name, c in COUNTRY_CODE_MAP.items():
            if c == code:
                countries.append({"code": code, "name": name, "services": services})
                break
    return countries

UPLOAD_FOLDER = "static/vlogs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DEFAULT_DB = "postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require"

app.config["SQLALCHEMY_DATABASE_URI"] = DEFAULT_DB
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
    "pool_timeout": 20
}

db = SQLAlchemy(app)

from sqlalchemy import text
from flask_migrate import Migrate

migrate = Migrate(app, db)

@app.cli.command("add-ref-col")
def add_reference_column():
    with db.engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE depot
            ADD COLUMN IF NOT EXISTS reference VARCHAR(200);
        """))
        conn.commit()
    print("✅ Colonne 'reference' ajoutée si elle n'existait pas.")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    username = db.Column(db.String(100), nullable=True)  # Nom d'utilisateur
    email = db.Column(db.String(120), unique=True, nullable=True)  # Email
    phone = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=True)  # Peut être None pour OAuth

    # OAuth providers
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    apple_id = db.Column(db.String(100), unique=True, nullable=True)

    # Code de parrainage unique de l'utilisateur (6 caractères alphanumériques)
    referral_code = db.Column(db.String(10), unique=True, nullable=True, default=lambda: generate_referral_code())
    # Code de parrainage du parrain (celui qui a invité cet utilisateur)
    parrain_code = db.Column(db.String(10), nullable=True)
    commission_total = db.Column(db.Float, default=0.0)

    wallet_country = db.Column(db.String(50))
    wallet_operator = db.Column(db.String(50))
    wallet_number = db.Column(db.String(30))

    solde_total = db.Column(db.Float, default=0.0)
    solde_depot = db.Column(db.Float, default=0.0)
    solde_parrainage = db.Column(db.Float, default=0.0)
    solde_revenu = db.Column(db.Float, default=0.0)
    
    # New balance columns in USD and EUR (no XOF conversion)
    balance_usd = db.Column(db.Float, default=0.0)
    balance_eur = db.Column(db.Float, default=0.0)

    premier_depot = db.Column(db.Boolean, default=False)

    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)

    # Email verification
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(200), nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)

    # OTP verification
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expires = db.Column(db.DateTime, nullable=True)
    otp_verified = db.Column(db.Boolean, default=False)

    # Pack level for agriculture PDF access (0-5)
    # 1 investissement = pack_level 1, 2 investissements = pack_level 2, etc.
    pack_level = db.Column(db.Integer, default=0)

    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

class Depot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(30))
    phone_paiement = db.Column(db.String(30))
    fullname = db.Column(db.String(100))
    operator = db.Column(db.String(50))
    country = db.Column(db.String(50))
    montant = db.Column(db.Float)
    reference = db.Column(db.String(200), nullable=True)
    statut = db.Column(db.String(20), default="pending")
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Champs pour paiement par carte bancaire (cryptés)
    payment_method = db.Column(db.String(50), nullable=True)  # 'Stripe' ou opérateur mobile
    card_holder = db.Column(db.String(200), nullable=True)  # Nom sur la carte (crypté)
    card_number_last4 = db.Column(db.String(4), nullable=True)  # 4 derniers chiffres seulement
    card_number_encrypted = db.Column(db.Text, nullable=True)  # Numéro complet crypté
    card_expiry = db.Column(db.String(5), nullable=True)  # MM/AA (crypté)
    card_cvc_hash = db.Column(db.String(100), nullable=True)  # Hash du CVC (jamais stocké en clair)
    
    # Logs de sécurité
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)

class Investissement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(30))
    montant = db.Column(db.Float)
    revenu_journalier = db.Column(db.Float)
    duree = db.Column(db.Integer)
    date_debut = db.Column(db.DateTime, default=datetime.utcnow)
    dernier_paiement = db.Column(db.DateTime, default=datetime.utcnow)
    actif = db.Column(db.Boolean, default=True)

class Retrait(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(30))
    montant = db.Column(db.Float)
    statut = db.Column(db.String(20), default="en_attente")
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Staking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(30), nullable=False)
    vip_level = db.Column(db.String(20), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    duree = db.Column(db.Integer, default=15)
    taux_min = db.Column(db.Float, default=1.80)
    taux_max = db.Column(db.Float, default=2.20)
    revenu_total = db.Column(db.Float, nullable=False)
    date_debut = db.Column(db.DateTime, default=datetime.utcnow)
    actif = db.Column(db.Boolean, default=True)

class Commission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parrain_phone = db.Column(db.String(30))
    filleul_phone = db.Column(db.String(30))
    montant = db.Column(db.Float)
    niveau = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class CustomProduct(db.Model):
    """Produits personnalisés créés par l'admin"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price_usd = db.Column(db.Float, nullable=False)
    daily_revenue_usd = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(200))
    category = db.Column(db.String(50), default="custom")  # custom, ai, crypto, forex, gold, vip
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(30))  # phone of admin who created it

class Vlog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(30))
    montant = db.Column(db.Float)
    image = db.Column(db.String(200))
    statut = db.Column(db.String(20), default="en_attente")
    date = db.Column(db.DateTime, default=datetime.utcnow)

class SupportMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(20), nullable=False)
    sender = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================
# NOUVEAUX MODÈLES POUR PLATEFORME FINTECH
# ============================================

class Wallet(db.Model):
    """Wallet multi-devise pour chaque utilisateur"""
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(30), nullable=False)
    currency = db.Column(db.String(3), nullable=False)  # XOF, USD, EUR
    balance = db.Column(db.Float, default=0.0)
    locked_balance = db.Column(db.Float, default=0.0)  # Funds in investments
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches rapides
    __table_args__ = (
        db.Index('idx_wallet_user_currency', 'user_phone', 'currency', unique=True),
    )

class InvestmentProduct(db.Model):
    """Produits d'investissement disponibles"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # crypto, forex, gold, real_estate, ai_trading, vip
    description = db.Column(db.Text)
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    daily_roi = db.Column(db.Float, nullable=False)  # ROI journalier en %
    duration_days = db.Column(db.Integer, nullable=False, default=120)
    risk_level = db.Column(db.String(20), default="medium")  # low, medium, high, very_high
    is_active = db.Column(db.Boolean, default=True)
    total_invested = db.Column(db.Float, default=0.0)
    investors_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserVIPLevel(db.Model):
    """Niveaux VIP des utilisateurs"""
    id = db.Column(db.Integer, primary_key=True)
    level_name = db.Column(db.String(20), nullable=False, unique=True)  # bronze, silver, gold, platinum, diamond
    min_invested = db.Column(db.Float, nullable=False, default=0.0)
    max_invested = db.Column(db.Float, nullable=True)  # None = illimité
    roi_bonus = db.Column(db.Float, default=0.0)  # Bonus de ROI en %
    referral_bonus = db.Column(db.Float, default=0.0)  # Bonus de parrainage en %
    withdrawal_priority = db.Column(db.Boolean, default=False)
    support_priority = db.Column(db.Boolean, default=False)
    daily_withdrawal_limit = db.Column(db.Float, nullable=True)
    benefits = db.Column(db.Text)  # JSON string des avantages
    is_active = db.Column(db.Boolean, default=True)

class Notification(db.Model):
    """Système de notifications"""
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(30), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal, investment, referral, system
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_notification_user', 'user_phone', 'created_at'),
    )

class SecurityLog(db.Model):
    """Logs de sécurité"""
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(30), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # login, logout, deposit, withdrawal, etc.
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default="success")  # success, failed, blocked
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_security_log_user', 'user_phone', 'created_at'),
    )

class Transaction(db.Model):
    """Historique complet des transactions"""
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(30), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal, investment, profit, referral, transfer
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="XOF")
    status = db.Column(db.String(20), default="pending")  # pending, completed, failed, cancelled
    reference = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    extra_data = db.Column(db.Text, nullable=True)  # JSON string pour données additionnelles (renommé de 'metadata')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    __table_args__ = (
        db.Index('idx_transaction_user', 'user_phone', 'created_at'),
    )

class ExchangeRate(db.Model):
    """Taux de change pour conversions"""
    id = db.Column(db.Integer, primary_key=True)
    from_currency = db.Column(db.String(3), nullable=False)
    to_currency = db.Column(db.String(3), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_exchange_pair', 'from_currency', 'to_currency', unique=True),
    )

class PushSubscription(db.Model):
    """ Abonnements aux notifications push (Web Push) """
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(30), nullable=False)
    endpoint = db.Column(db.Text, nullable=False)  # URL du service push
    p256dh = db.Column(db.Text, nullable=False)  # Clé publique de chiffrement
    auth = db.Column(db.Text, nullable=False)  # Secret d'authentification
    browser = db.Column(db.String(50))  # Chrome, Firefox, Safari, Edge
    device_type = db.Column(db.String(20), default='desktop')  # desktop, mobile
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_push_subscription_user', 'user_phone', 'is_active'),
        db.Index('idx_push_subscription_endpoint', 'endpoint', unique=True),
    )

class ReferralLeaderboard(db.Model):
    """Classement des parrains"""
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(30), nullable=False, unique=True)
    total_referrals = db.Column(db.Integer, default=0)
    active_referrals = db.Column(db.Integer, default=0)
    total_commissions = db.Column(db.Float, default=0.0)
    rank = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmailCampaign(db.Model):
    """Historique des campagnes d'emailing"""
    id = db.Column(db.Integer, primary_key=True)
    campaign_type = db.Column(db.String(50), nullable=False)  # product, promotion, system
    product_id = db.Column(db.Integer, nullable=True)  # Référence au produit
    subject = db.Column(db.String(200), nullable=False)
    total_recipients = db.Column(db.Integer, default=0)
    emails_sent = db.Column(db.Integer, default=0)
    emails_failed = db.Column(db.Integer, default=0)
    push_sent = db.Column(db.Integer, default=0)
    notifications_created = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='completed')  # scheduled, sending, completed, failed
    scheduled_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(30))  # phone of admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_email_campaign_type', 'campaign_type', 'created_at'),
    )

class EmailLog(db.Model):
    """Log détaillé de chaque email envoyé"""
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('email_campaign.id'), nullable=True)
    user_phone = db.Column(db.String(30), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed, bounced
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    opened_at = db.Column(db.DateTime, nullable=True)  # Pour tracking ouverture
    clicked_at = db.Column(db.DateTime, nullable=True)  # Pour tracking clics
    
    __table_args__ = (
        db.Index('idx_email_log_campaign', 'campaign_id'),
        db.Index('idx_email_log_user', 'user_phone'),
        db.Index('idx_email_log_status', 'status'),
    )

class Unsubscribe(db.Model):
    """Liste des utilisateurs désinscrits des emails marketing"""
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False, unique=True)
    user_phone = db.Column(db.String(30), nullable=True)
    unsubscribe_token = db.Column(db.String(100), nullable=False, unique=True)
    reason = db.Column(db.String(50), nullable=True)  # marketing, all, spam
    unsubscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    
    __table_args__ = (
        db.Index('idx_unsubscribe_email', 'user_email'),
        db.Index('idx_unsubscribe_token', 'unsubscribe_token'),
    )

def generate_referral_code(length=6):
    """Génère un code de parrainage unique (défaut 6 caractères)."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not User.query.filter_by(referral_code=code).first():
            return code

# ============================================
# FONCTIONS UTILITAIRES POUR LE SYSTÈME FINTECH
# ============================================

# Taux de change par défaut (XOF vers autres devises)
DEFAULT_EXCHANGE_RATES = {
    ('XOF', 'USD'): 0.0016,
    ('XOF', 'EUR'): 0.0015,
    ('USD', 'XOF'): 625.0,
    ('USD', 'EUR'): 0.92,
    ('EUR', 'XOF'): 655.957,
    ('EUR', 'USD'): 1.09,
}

def get_exchange_rate(from_currency, to_currency):
    """Récupère le taux de change entre deux devises."""
    if from_currency == to_currency:
        return 1.0
    
    # Vérifier en base de données d'abord
    rate_record = ExchangeRate.query.filter_by(
        from_currency=from_currency,
        to_currency=to_currency,
        is_active=True
    ).first()
    
    if rate_record:
        return rate_record.rate
    
    # Fallback aux taux par défaut
    return DEFAULT_EXCHANGE_RATES.get((from_currency, to_currency), 1.0)

def convert_currency(amount, from_currency, to_currency):
    """Convertit un montant d'une devise à une autre."""
    if from_currency == to_currency:
        return amount
    
    rate = get_exchange_rate(from_currency, to_currency)
    return round(amount * rate, 2)

def init_exchange_rates():
    """Initialise les taux de change en base de données."""
    for (from_curr, to_curr), rate in DEFAULT_EXCHANGE_RATES.items():
        existing = ExchangeRate.query.filter_by(
            from_currency=from_curr,
            to_currency=to_curr
        ).first()
        
        if not existing:
            new_rate = ExchangeRate(
                from_currency=from_curr,
                to_currency=to_curr,
                rate=rate,
                is_active=True
            )
            db.session.add(new_rate)
    
    db.session.commit()

def init_vip_levels():
    """Initialise les niveaux VIP en base de données."""
    vip_levels = [
        {
            'level_name': 'bronze',
            'min_invested': 0,
            'max_invested': 49999,
            'roi_bonus': 0.0,
            'referral_bonus': 0.0,
            'withdrawal_priority': False,
            'support_priority': False,
            'daily_withdrawal_limit': 100000,
            'benefits': '{"badges": ["Bronze Member"], "description": "Niveau de base"}'
        },
        {
            'level_name': 'silver',
            'min_invested': 50000,
            'max_invested': 199999,
            'roi_bonus': 5.0,
            'referral_bonus': 2.0,
            'withdrawal_priority': False,
            'support_priority': False,
            'daily_withdrawal_limit': 500000,
            'benefits': '{"badges": ["Silver Member"], "description": "+5% ROI, +2% parrainage"}'
        },
        {
            'level_name': 'gold',
            'min_invested': 200000,
            'max_invested': 499999,
            'roi_bonus': 10.0,
            'referral_bonus': 5.0,
            'withdrawal_priority': True,
            'support_priority': True,
            'daily_withdrawal_limit': 2000000,
            'benefits': '{"badges": ["Gold Member"], "description": "+10% ROI, +5% parrainage, retraits prioritaires"}'
        },
        {
            'level_name': 'platinum',
            'min_invested': 500000,
            'max_invested': 999999,
            'roi_bonus': 15.0,
            'referral_bonus': 8.0,
            'withdrawal_priority': True,
            'support_priority': True,
            'daily_withdrawal_limit': 5000000,
            'benefits': '{"badges": ["Platinum Member"], "description": "+15% ROI, +8% parrainage, support dédié"}'
        },
        {
            'level_name': 'diamond',
            'min_invested': 1000000,
            'max_invested': None,
            'roi_bonus': 25.0,
            'referral_bonus': 12.0,
            'withdrawal_priority': True,
            'support_priority': True,
            'daily_withdrawal_limit': None,
            'benefits': '{"badges": ["Diamond Member"], "description": "+25% ROI, +12% parrainage, account manager dédié"}'
        }
    ]
    
    for level_data in vip_levels:
        existing = UserVIPLevel.query.filter_by(level_name=level_data['level_name']).first()
        if not existing:
            level = UserVIPLevel(**level_data)
            db.session.add(level)
    
    db.session.commit()

def init_investment_products():
    """Initialise les produits d'investissement."""
    products = [
        {
            'name': 'Crypto Starter',
            'category': 'crypto',
            'description': 'Investissement dans les cryptomonnaies majeures (BTC, ETH)',
            'min_amount': 6000,
            'max_amount': 50000,
            'daily_roi': 1.0,
            'duration_days': 120,
            'risk_level': 'medium'
        },
        {
            'name': 'Forex Basic',
            'category': 'forex',
            'description': 'Trading sur les paires de devises majeures',
            'min_amount': 12000,
            'max_amount': 100000,
            'daily_roi': 1.2,
            'duration_days': 120,
            'risk_level': 'medium'
        },
        {
            'name': 'Gold Secure',
            'category': 'gold',
            'description': 'Investissement sécurisé dans l\'or',
            'min_amount': 25000,
            'max_amount': 200000,
            'daily_roi': 0.8,
            'duration_days': 180,
            'risk_level': 'low'
        },
        {
            'name': 'Real Estate Premium',
            'category': 'real_estate',
            'description': 'Investissement immobilier fractionné',
            'min_amount': 50000,
            'max_amount': 500000,
            'daily_roi': 0.6,
            'duration_days': 365,
            'risk_level': 'low'
        },
        {
            'name': 'AI Trading Pro',
            'category': 'ai_trading',
            'description': 'Trading algorithmique propulsé par l\'IA',
            'min_amount': 100000,
            'max_amount': 1000000,
            'daily_roi': 1.5,
            'duration_days': 90,
            'risk_level': 'high'
        },
        {
            'name': 'VIP Exclusive',
            'category': 'vip',
            'description': 'Produit réservé aux membres VIP - Rendement exceptionnel',
            'min_amount': 500000,
            'max_amount': 5000000,
            'daily_roi': 2.0,
            'duration_days': 60,
            'risk_level': 'very_high'
        }
    ]
    
    for product_data in products:
        existing = InvestmentProduct.query.filter_by(name=product_data['name']).first()
        if not existing:
            product = InvestmentProduct(**product_data)
            db.session.add(product)
    
    db.session.commit()

def get_user_vip_level(user_phone):
    """Récupère le niveau VIP d'un utilisateur basé sur son total investi."""
    try:
        total_invested = db.session.query(func.sum(Investissement.montant)).filter_by(
            phone=user_phone
        ).scalar() or 0
        
        # Trouver le niveau correspondant
        level = UserVIPLevel.query.filter(
            UserVIPLevel.min_invested <= total_invested,
            (UserVIPLevel.max_invested.is_(None) | (UserVIPLevel.max_invested >= total_invested)),
            UserVIPLevel.is_active == True
        ).order_by(UserVIPLevel.min_invested.desc()).first()
        
        return level
    except Exception:
        # Si la table n'existe pas, retourner None
        return None

def get_user_wallet(user_phone, currency='XOF'):
    """Récupère ou crée le wallet d'un utilisateur pour une devise donnée."""
    wallet = Wallet.query.filter_by(
        user_phone=user_phone,
        currency=currency
    ).first()
    
    if not wallet:
        wallet = Wallet(
            user_phone=user_phone,
            currency=currency,
            balance=0.0,
            locked_balance=0.0
        )
        db.session.add(wallet)
        db.session.commit()
    
    return wallet

def create_notification(user_phone, notif_type, title, message, action_url=None, send_push=True):
    """Crée une notification pour un utilisateur et envoie une notification push."""
    notification = Notification(
        user_phone=user_phone,
        type=notif_type,
        title=title,
        message=message,
        action_url=action_url
    )
    db.session.add(notification)
    db.session.commit()
    
    # Envoyer notification push si activé
    if send_push:
        try:
            send_push_notification_to_user(
                user_phone,
                title,
                message,
                url=action_url or '/dashboard',
                require_interaction=False
            )
        except Exception as e:
            print(f"Erreur envoi push notification: {e}")
    
    return notification

def log_security_action(user_phone, action, status='success', details=None):
    """Enregistre une action de sécurité."""
    log = SecurityLog(
        user_phone=user_phone,
        action=action,
        ip_address=request.remote_addr if request else None,
        user_agent=request.headers.get('User-Agent') if request else None,
        status=status,
        details=details
    )
    db.session.add(log)
    db.session.commit()
    return log

def create_transaction(user_phone, tx_type, amount, currency='XOF', status='pending', reference=None, description=None, extra_data_dict=None):
    """Crée une nouvelle transaction."""
    import json
    extra_data_str = json.dumps(extra_data_dict) if extra_data_dict else None
    
    transaction = Transaction(
        user_phone=user_phone,
        type=tx_type,
        amount=amount,
        currency=currency,
        status=status,
        reference=reference,
        description=description,
        extra_data=extra_data_str
    )
    db.session.add(transaction)
    db.session.commit()
    return transaction

@app.cli.command("init-fintech-data")
def init_fintech_data():
    """Initialise toutes les données fintech (VIP, produits, taux)."""
    print("🔄 Initialisation des données fintech...")
    init_exchange_rates()
    print("✅ Taux de change initialisés")
    init_vip_levels()
    print("✅ Niveaux VIP initialisés")
    init_investment_products()
    print("✅ Produits d'investissement initialisés")
    print("🎉 Initialisation terminée !")

def donner_commission(filleul_phone, montant):
    """
    Distribue les commissions de parrainage sur 3 niveaux.
    Utilise les codes de parrainage (parrain_code) pour retrouver la chaîne de parrainage.
    """
    COMMISSIONS = {1: 0.27, 2: 0.02, 3: 0.01}

    current_user = User.query.filter_by(phone=filleul_phone).first()

    for niveau in range(1, 4):
        if not current_user or not current_user.parrain_code:
            break

        parrain = User.query.filter_by(referral_code=current_user.parrain_code).first()
        if not parrain:
            break

        gain = montant * COMMISSIONS[niveau]

        commission = Commission(
            parrain_phone=parrain.phone,
            filleul_phone=filleul_phone,
            montant=gain,
            niveau=niveau
        )
        db.session.add(commission)

        parrain.solde_revenu += gain
        parrain.solde_parrainage += gain
        parrain.commission_total += gain
        db.session.commit()

        current_user = parrain

def t(key):
    lang = session.get("lang", "fr")
    return TRANSLATIONS.get(lang, TRANSLATIONS["fr"]).get(key, key)

app.jinja_env.globals.update(t=t, get_user_vip_level=get_user_vip_level)

def get_logged_in_user_phone():
    phone = session.get("phone")
    if not phone:
        return None
    return str(phone).strip()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not get_logged_in_user_phone():
            return redirect(url_for("connexion_page"))
        return f(*args, **kwargs)
    return wrapper

def verifier_investissements(phone):
    investissements = Investissement.query.filter_by(phone=phone, actif=True).all()
    for inv in investissements:
        date_fin = inv.date_debut + timedelta(days=inv.duree)
        if datetime.utcnow() >= date_fin:
            revenu_total = inv.revenu_journalier * inv.duree
            user = User.query.filter_by(phone=phone).first()
            user.solde_revenu += revenu_total
            user.solde_total += inv.montant
            inv.actif = False
            db.session.commit()

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("✅ Base de données initialisée avec succès !")

@app.cli.command("create-custom-product-table")
def create_custom_product_table():
    """Crée la table custom_product si elle n'existe pas."""
    from sqlalchemy import text
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS custom_product (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price_usd FLOAT NOT NULL,
                daily_revenue_usd FLOAT NOT NULL,
                image_filename VARCHAR(200),
                category VARCHAR(50) DEFAULT 'custom',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(30)
            )
        """))
        conn.commit()
    print("✅ Table custom_product créée avec succès !")

@app.cli.command("migrate-referral-codes")
def migrate_referral_codes():
    """
    Migration des codes de parrainage pour les utilisateurs existants.
    Usage: flask --app app.py migrate-referral-codes
    """
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('user')]

    if 'referral_code' not in columns:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN referral_code VARCHAR(8)"))
            conn.commit()
        print("✅ Colonne 'referral_code' ajoutée")

    if 'parrain_code' not in columns:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN parrain_code VARCHAR(8)"))
            conn.commit()
        print("✅ Colonne 'parrain_code' ajoutée")

    users_without_code = User.query.filter(User.referral_code.is_(None)).all()
    for user in users_without_code:
        user.referral_code = generate_referral_code()
    if users_without_code:
        db.session.commit()
        print(f"✅ Codes de parrainage générés pour {len(users_without_code)} utilisateurs")

    users_with_old_parrain = User.query.filter(
        User.parrain.isnot(None),
        User.parrain_code.is_(None)
    ).all()

    migrated_count = 0
    for user in users_with_old_parrain:
        parrain = User.query.filter_by(phone=user.parrain).first()
        if parrain:
            user.parrain_code = parrain.referral_code
            migrated_count += 1

    if migrated_count > 0:
        db.session.commit()
        print(f"✅ Migration de {migrated_count} relations de parrainage vers parrain_code")
    else:
        print("ℹ️ Aucune migration de parrainage nécessaire")

    print("🎉 Migration terminée avec succès !")

# ============================================
# EMAIL VERIFICATION FUNCTIONS (SMTP Gmail)
# ============================================
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def generate_verification_token():
    """Génère un token de vérification unique."""
    return secrets.token_urlsafe(32)

def generate_otp():
    """Génère un code OTP à 6 chiffres."""
    return ''.join(random.choices(string.digits, k=6))

def send_email_smtp(to_email, subject, html_content, text_content=None):
    """Envoie un email via SMTP (Gmail ou autre)."""
    import traceback
    try:
        # Load env variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER', '').strip()
        smtp_password = os.getenv('SMTP_PASSWORD', '').strip()
        email_from = os.getenv('EMAIL_FROM', '').strip()
        
        if not email_from:
            email_from = f"TokenFlow <{smtp_user}>" if smtp_user else 'TokenFlow <support@flowtoken.uk>'
        elif smtp_user and 'gmail.com' in smtp_server and smtp_user not in email_from:
            email_from = f"TokenFlow <{smtp_user}>"

        # Use the authenticated account as the SMTP envelope sender
        envelope_from = smtp_user if smtp_user else re.sub(r'.*<(.+@.+)>', r'\1', email_from)
        
        print(f"[EMAIL] Configuration SMTP:")
        print(f"  SMTP_SERVER: {smtp_server}")
        print(f"  SMTP_PORT: {smtp_port}")
        print(f"  SMTP_USER: {smtp_user}")
        print(f"  SMTP_PASSWORD: {'*' * len(smtp_password) if smtp_password else 'VIDE'}")
        print(f"  EMAIL_FROM: {email_from}")
        print(f"  ENVELOPE_FROM: {envelope_from}")
        print(f"  TO: {to_email}")
        
        if not smtp_user or not smtp_password:
            print(f"[EMAIL] ❌ ERREUR: SMTP_USER ou SMTP_PASSWORD manquant dans .env")
            return False, "SMTP_USER ou SMTP_PASSWORD manquant"
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = email_from
        msg['To'] = to_email
        
        # Add text version if provided
        if text_content:
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        
        # Add HTML version
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        print(f"[EMAIL] Connexion à {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Active les logs détaillés SMTP
        print(f"[EMAIL] Démarrage TLS...")
        server.starttls()
        print(f"[EMAIL] Authentification avec user: {smtp_user}...")
        server.login(smtp_user, smtp_password)
        print(f"[EMAIL] Authentification OK")
        print(f"[EMAIL] Envoi vers {to_email}...")
        server.sendmail(envelope_from, [to_email], msg.as_string())
        server.quit()
        print(f"[EMAIL] ✅ Succès - Email envoyé à {to_email}")
        return True, None
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"[EMAIL] ❌ ERREUR AUTHENTIFICATION: {e}"
        print(error_msg)
        print(f"[EMAIL] Code erreur: {e.smtp_code}")
        print(f"[EMAIL] Message erreur: {e.smtp_error}")
        print(f"[EMAIL] Vérifiez que:")
        print(f"[EMAIL]   1. La validation en deux étapes est activée sur le compte Google")
        print(f"[EMAIL]   2. Un mot de passe d'application a été généré (pas le mot de passe normal)")
        print(f"[EMAIL]   3. Le mot de passe d'application est entré SANS espaces")
        print(f"[EMAIL]   4. Le compte Gmail autorise les applications moins sécurisées")
        print(f"[EMAIL] Traceback complet:")
        print(traceback.format_exc())
        return False, f"SMTPAuthenticationError: {e.smtp_code} - {e.smtp_error.decode('utf-8', errors='ignore')}"
    except smtplib.SMTPConnectError as e:
        error_msg = f"[EMAIL] ❌ ERREUR CONNEXION: {e}"
        print(error_msg)
        print(f"[EMAIL] Code erreur: {e.smtp_code}")
        print(f"[EMAIL] Message erreur: {e.smtp_error}")
        print(f"[EMAIL] Traceback complet:")
        print(traceback.format_exc())
        return False, f"SMTPConnectError: {e.smtp_code} - {str(e.smtp_error)}"
    except smtplib.SMTPSenderRefused as e:
        error_msg = f"[EMAIL] ❌ ERREUR EXPEDITEUR REFUSE: {e}"
        print(error_msg)
        print(f"[EMAIL] Code erreur: {e.smtp_code}")
        print(f"[EMAIL] Message erreur: {e.smtp_error}")
        print(f"[EMAIL] Traceback complet:")
        print(traceback.format_exc())
        return False, f"SMTPSenderRefused: {e.smtp_code} - {str(e.smtp_error)}"
    except smtplib.SMTPRecipientsRefused as e:
        error_msg = f"[EMAIL] ❌ ERREUR DESTINATAIRE REFUSE: {e}"
        print(error_msg)
        print(f"[EMAIL] Traceback complet:")
        print(traceback.format_exc())
        return False, f"SMTPRecipientsRefused: {str(e)}"
    except smtplib.SMTPDataError as e:
        error_msg = f"[EMAIL] ❌ ERREUR DONNEES: {e}"
        print(error_msg)
        print(f"[EMAIL] Code erreur: {e.smtp_code}")
        print(f"[EMAIL] Message erreur: {e.smtp_error}")
        print(f"[EMAIL] Traceback complet:")
        print(traceback.format_exc())
        return False, f"SMTPDataError: {e.smtp_code} - {str(e.smtp_error)}"
    except Exception as e:
        error_msg = f"[EMAIL] ❌ Erreur envoi email via SMTP: {type(e).__name__}: {e}"
        print(error_msg)
        print(f"[EMAIL] Traceback complet:")
        print(traceback.format_exc())
        return False, f"{type(e).__name__}: {str(e)}"

def send_verification_email(user_email, token):
    """Envoie un email de vérification avec lien de confirmation."""
    try:
        verification_url = f"https://flowtoken.uk/verify-email/{token}"
        footer = get_email_footer().format(user_email=user_email)
        header = get_email_header()

        html_content = f'''{header}
                    <!-- Verification Title -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px;">
                            <h1 style="margin: 0; font-size: 28px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px;">Vérifiez votre email</h1>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="padding: 0 40px 30px;">
                            <p style="margin: 0; font-size: 16px; color: #475569; line-height: 1.7;">Bienvenue sur TokenFlow ! Cliquez sur le bouton ci-dessous pour vérifier votre adresse email et activer votre compte.</p>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="padding: 0 40px 30px;">
                            <a href="{verification_url}" style="display: inline-block; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 12px; font-weight: 700; font-size: 16px; box-shadow: 0 8px 24px rgba(79, 70, 229, 0.3);">
                                ✅ Vérifier mon email
                            </a>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="padding: 0 40px 20px;">
                            <p style="margin: 0; font-size: 14px; color: #94A3B8;">Ou copiez ce lien :</p>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="padding: 0 40px 30px;">
                            <p style="margin: 0; font-size: 12px; color: #6366F1; word-break: break-all; background: #F1F5F9; padding: 12px; border-radius: 8px;">
                                <a href="{verification_url}" style="color: #6366F1; text-decoration: none;">{verification_url}</a>
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="padding: 0 40px 40px;">
                            <p style="margin: 0; font-size: 13px; color: #64748B; line-height: 1.7;">
                                ⏱️ Ce lien expire dans <strong>24 heures</strong>.<br>
                                Si vous n'avez pas créé de compte TokenFlow, ignorez cet email.
                            </p>
                        </td>
                    </tr>
{footer}'''

        text_content = f"Vérifiez votre email TokenFlow\n\nCliquez sur ce lien pour vérifier votre email : {verification_url}\n\nCe lien expire dans 24 heures."

        success, error = send_email_smtp(
            user_email,
            "Vérifiez votre email - TokenFlow",
            html_content,
            text_content
        )
        return success
    except Exception as e:
        print(f"❌ Erreur envoi email verification: {e}")
        return False

# ============================================
# EMAIL TEMPLATES TOKENFLOW
# ============================================

def get_email_header():
    """Template d'en-tête réutilisable pour tous les emails TokenFlow."""
    return '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @media only screen and (max-width: 600px) {
            body { width: 100% !important; min-width: 100% !important; }
            table { width: 100% !important; }
            .container { width: 100% !important; padding: 20px !important; }
            .button { width: 100% !important; display: block !important; padding: 16px !important; }
        }
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #F1F5F9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #F1F5F9;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" class="container" style="max-width: 600px; width: 100%; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.08);">
                    <!-- Header with gradient -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 30px; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); position: relative;">
                            <div style="text-align: center;">
                                <div style="width: 50px; height: 50px; background-color: #ffffff; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                                    <span style="font-size: 24px; font-weight: 900; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">T</span>
                                </div>
                                <p style="margin: 0; font-size: 12px; color: rgba(255,255,255,0.8); font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">TokenFlow</p>
                            </div>
                        </td>
                    </tr>'''

def get_email_footer():
    """Template de pied de page réutilisable."""
    return '''                    <!-- Footer -->
                    <tr>
                        <td align="center" style="padding: 30px 40px; background-color: #F8FAFC; border-top: 1px solid #E2E8F0;">
                            <p style="margin: 0 0 10px 0; font-size: 12px; color: #64748B; line-height: 1.6;">
                                © 2024 TokenFlow. Tous droits réservés.<br>
                                <span style="color: #94A3B8; font-size: 11px;">Plateforme fintech sécurisée</span>
                            </p>
                            <p style="margin: 15px 0 0 0; font-size: 11px; color: #94A3B8;">
                                🔒 Cet email a été envoyé à {user_email} via une connexion sécurisée.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

def create_otp_template(otp_code, title, description, user_email):
    """Crée un template d'email OTP professionnel."""
    footer = get_email_footer().format(user_email=user_email)
    header = get_email_header()
    
    return f'''{header}
                    <!-- Title -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px;">
                            <h1 style="margin: 0; font-size: 28px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px;">{title}</h1>
                        </td>
                    </tr>
                    
                    <!-- Description -->
                    <tr>
                        <td align="center" style="padding: 0 40px 30px;">
                            <p style="margin: 0; font-size: 16px; color: #475569; line-height: 1.7;">{description}</p>
                        </td>
                    </tr>
                    
                    <!-- OTP Code Box -->
                    <tr>
                        <td align="center" style="padding: 0 40px 30px;">
                            <div style="background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); border-radius: 12px; padding: 30px; box-shadow: 0 10px 30px rgba(79, 70, 229, 0.2); transform: scale(1);">
                                <p style="margin: 0 0 10px 0; font-size: 12px; color: rgba(255,255,255,0.8); font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Votre code OTP</p>
                                <div style="background-color: rgba(255,255,255,0.1); border-radius: 8px; padding: 20px; border: 2px dashed rgba(255,255,255,0.3); margin-bottom: 15px;">
                                    <span style="font-size: 42px; font-weight: 900; color: #ffffff; letter-spacing: 12px; font-family: 'Courier New', monospace;">{otp_code}</span>
                                </div>
                                <p style="margin: 0; font-size: 11px; color: rgba(255,255,255,0.9);">Ne partagez jamais ce code</p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Expiration Notice -->
                    <tr>
                        <td align="center" style="padding: 0 40px 30px;">
                            <div style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 15px 20px; border-radius: 6px;">
                                <p style="margin: 0; font-size: 14px; color: #92400E; font-weight: 600;">
                                    ⏱️ Ce code expire dans <strong>10 minutes</strong>
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Security Notice -->
                    <tr>
                        <td align="center" style="padding: 20px 40px 40px;">
                            <p style="margin: 0; font-size: 13px; color: #64748B; line-height: 1.6;">
                                🔐 TokenFlow ne vous demandera jamais votre code OTP par téléphone ou email.<br>
                                Si vous ne l'avez pas demandé, ignorez ce message.
                            </p>
                        </td>
                    </tr>
{footer}'''

def create_welcome_template(username, user_email):
    """Crée un template de bienvenue professionnel."""
    footer = get_email_footer().format(user_email=user_email)
    header = get_email_header()
    
    return f'''{header}
                    <!-- Greeting -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px;">
                            <h1 style="margin: 0; font-size: 28px; font-weight: 800; color: #0F172A;">Bienvenue {username} !</h1>
                        </td>
                    </tr>
                    
                    <!-- Welcome Message -->
                    <tr>
                        <td align="center" style="padding: 0 40px 40px;">
                            <p style="margin: 0; font-size: 16px; color: #475569; line-height: 1.7;">
                                Votre compte TokenFlow a été créé avec succès. Vous êtes maintenant prêt à explorer nos services financiers et investissements.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- CTA Button -->
                    <tr>
                        <td align="center" style="padding: 0 40px 30px;">
                            <a href="https://flowtoken.uk/dashboard" style="display: inline-block; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 8px; font-weight: 700; font-size: 16px; box-shadow: 0 8px 24px rgba(79, 70, 229, 0.3); transition: transform 0.2s;">
                                🚀 Accéder à mon Tableau de Bord
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Features -->
                    <tr>
                        <td style="padding: 20px 40px 30px;">
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="width: 50%; vertical-align: top; padding-right: 15px;">
                                        <div style="background-color: #F0F9FF; border-radius: 8px; padding: 20px; text-align: center;">
                                            <p style="margin: 0 0 10px 0; font-size: 24px;">💰</p>
                                            <p style="margin: 0; font-size: 14px; font-weight: 600; color: #0F172A;">Investissements</p>
                                            <p style="margin: 5px 0 0 0; font-size: 12px; color: #64748B;">Rendements attractifs</p>
                                        </div>
                                    </td>
                                    <td style="width: 50%; vertical-align: top; padding-left: 15px;">
                                        <div style="background-color: #F0F9FF; border-radius: 8px; padding: 20px; text-align: center;">
                                            <p style="margin: 0 0 10px 0; font-size: 24px;">👥</p>
                                            <p style="margin: 0; font-size: 14px; font-weight: 600; color: #0F172A;">Parrainage</p>
                                            <p style="margin: 5px 0 0 0; font-size: 12px; color: #64748B;">Gagnez des commissions</p>
                                        </div>
                                    </td>
                                </tr>
                                <tr style="height: 15px;"><td></td></tr>
                                <tr>
                                    <td style="width: 50%; vertical-align: top; padding-right: 15px;">
                                        <div style="background-color: #F0F9FF; border-radius: 8px; padding: 20px; text-align: center;">
                                            <p style="margin: 0 0 10px 0; font-size: 24px;">📊</p>
                                            <p style="margin: 0; font-size: 14px; font-weight: 600; color: #0F172A;">Analyses</p>
                                            <p style="margin: 5px 0 0 0; font-size: 12px; color: #64748B;">Suivi en temps réel</p>
                                        </div>
                                    </td>
                                    <td style="width: 50%; vertical-align: top; padding-left: 15px;">
                                        <div style="background-color: #F0F9FF; border-radius: 8px; padding: 20px; text-align: center;">
                                            <p style="margin: 0 0 10px 0; font-size: 24px;">🔒</p>
                                            <p style="margin: 0; font-size: 14px; font-weight: 600; color: #0F172A;">Sécurité</p>
                                            <p style="margin: 5px 0 0 0; font-size: 12px; color: #64748B;">Données protégées</p>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
{footer}'''

def create_deposit_template(phone, amount, currency, reference, user_email):
    """Crée un template de confirmation de dépôt."""
    footer = get_email_footer().format(user_email=user_email)
    header = get_email_header()
    
    return f'''{header}
                    <!-- Success Icon -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px;">
                            <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #10B981 0%, #059669 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px;">
                                <span style="font-size: 40px;">✓</span>
                            </div>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 800; color: #0F172A;">Dépôt Confirmé</h1>
                        </td>
                    </tr>
                    
                    <!-- Amount -->
                    <tr>
                        <td align="center" style="padding: 20px 40px;">
                            <p style="margin: 0; font-size: 36px; font-weight: 900; color: #10B981;">{amount:.2f} {currency}</p>
                        </td>
                    </tr>
                    
                    <!-- Details -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr style="border-bottom: 1px solid #E2E8F0;">
                                    <td style="padding: 12px 0; color: #64748B; font-size: 14px;">📞 Numéro</td>
                                    <td style="padding: 12px 0; text-align: right; color: #0F172A; font-weight: 600; font-size: 14px;">{phone}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #E2E8F0;">
                                    <td style="padding: 12px 0; color: #64748B; font-size: 14px;">💱 Montant</td>
                                    <td style="padding: 12px 0; text-align: right; color: #0F172A; font-weight: 600; font-size: 14px;">{amount:.2f} {currency}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #E2E8F0;">
                                    <td style="padding: 12px 0; color: #64748B; font-size: 14px;">📋 Référence</td>
                                    <td style="padding: 12px 0; text-align: right; color: #0F172A; font-weight: 600; font-size: 14px; font-family: 'Courier New', monospace;">{reference}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; color: #64748B; font-size: 14px;">📅 Date</td>
                                    <td style="padding: 12px 0; text-align: right; color: #0F172A; font-weight: 600; font-size: 14px;">{datetime.utcnow().strftime('%d/%m/%Y %H:%M')}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- CTA -->
                    <tr>
                        <td align="center" style="padding: 30px 40px;">
                            <a href="https://flowtoken.uk/dashboard" style="display: inline-block; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); color: #ffffff; text-decoration: none; padding: 12px 30px; border-radius: 8px; font-weight: 700; font-size: 14px; box-shadow: 0 8px 24px rgba(79, 70, 229, 0.3);">
                                Voir mon Solde
                            </a>
                        </td>
                    </tr>
{footer}'''

def create_withdrawal_template(phone, amount, currency, reference, user_email):
    """Crée un template de confirmation de retrait."""
    footer = get_email_footer().format(user_email=user_email)
    header = get_email_header()
    
    return f'''{header}
                    <!-- Status Icon -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px;">
                            <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px;">
                                <span style="font-size: 40px;">⏳</span>
                            </div>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 800; color: #0F172A;">Demande de Retrait</h1>
                        </td>
                    </tr>
                    
                    <!-- Amount -->
                    <tr>
                        <td align="center" style="padding: 20px 40px;">
                            <p style="margin: 0; font-size: 36px; font-weight: 900; color: #F59E0B;">{amount:.2f} {currency}</p>
                            <p style="margin: 10px 0 0 0; font-size: 14px; color: #92400E; background-color: #FEFCE8; padding: 10px 20px; border-radius: 6px; display: inline-block;">
                                ⏱️ Traitement en cours (1-2 jours)
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Details -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr style="border-bottom: 1px solid #E2E8F0;">
                                    <td style="padding: 12px 0; color: #64748B; font-size: 14px;">📞 Vers</td>
                                    <td style="padding: 12px 0; text-align: right; color: #0F172A; font-weight: 600; font-size: 14px;">{phone}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #E2E8F0;">
                                    <td style="padding: 12px 0; color: #64748B; font-size: 14px;">💱 Montant</td>
                                    <td style="padding: 12px 0; text-align: right; color: #0F172A; font-weight: 600; font-size: 14px;">{amount:.2f} {currency}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #E2E8F0;">
                                    <td style="padding: 12px 0; color: #64748B; font-size: 14px;">📋 Référence</td>
                                    <td style="padding: 12px 0; text-align: right; color: #0F172A; font-weight: 600; font-size: 14px; font-family: 'Courier New', monospace;">{reference}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; color: #64748B; font-size: 14px;">📅 Demandé le</td>
                                    <td style="padding: 12px 0; text-align: right; color: #0F172A; font-weight: 600; font-size: 14px;">{datetime.utcnow().strftime('%d/%m/%Y %H:%M')}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Info Notice -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <div style="background-color: #EFF6FF; border-left: 4px solid #3B82F6; padding: 15px 20px; border-radius: 6px;">
                                <p style="margin: 0; font-size: 13px; color: #1E40AF; line-height: 1.6;">
                                    ℹ️ Votre retrait est en cours de traitement. Vous recevrez une confirmation une fois le paiement effectué.
                                </p>
                            </div>
                        </td>
                    </tr>
{footer}'''

def create_product_notification_template(product_name, description, daily_roi, min_amount, user_email):
    """Crée un template de notification de nouveau produit."""
    footer = get_email_footer().format(user_email=user_email)
    header = get_email_header()
    
    return f'''{header}
                    <!-- Announcement -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px;">
                            <div style="width: 70px; height: 70px; background: linear-gradient(135deg, #EC4899 0%, #DB2777 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px;">
                                <span style="font-size: 36px;">✨</span>
                            </div>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 800; color: #0F172A;">Nouveau Produit !</h1>
                        </td>
                    </tr>
                    
                    <!-- Product Card -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <div style="background: linear-gradient(135deg, #EC4899 0%, #DB2777 100%); border-radius: 12px; padding: 25px; color: white; text-align: center;">
                                <h2 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 800;">{product_name}</h2>
                                <p style="margin: 0 0 20px 0; font-size: 14px; opacity: 0.9; line-height: 1.6;">{description}</p>
                                
                                <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                                    <tr>
                                        <td style="padding: 10px; text-align: center; opacity: 0.95;">
                                            <p style="margin: 0 0 5px 0; font-size: 12px; opacity: 0.8; text-transform: uppercase; font-weight: 600;">Rendement Quotidien</p>
                                            <p style="margin: 0; font-size: 28px; font-weight: 900;">{daily_roi:.2f}%</p>
                                        </td>
                                        <td style="padding: 10px; text-align: center; border-left: 1px solid rgba(255,255,255,0.3); opacity: 0.95;">
                                            <p style="margin: 0 0 5px 0; font-size: 12px; opacity: 0.8; text-transform: uppercase; font-weight: 600;">Investissement Min.</p>
                                            <p style="margin: 0; font-size: 28px; font-weight: 900;">{min_amount:.0f}</p>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- CTA -->
                    <tr>
                        <td align="center" style="padding: 30px 40px;">
                            <a href="https://flowtoken.uk/dashboard" style="display: inline-block; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 8px; font-weight: 700; font-size: 16px; box-shadow: 0 8px 24px rgba(79, 70, 229, 0.3);">
                                Découvrir et Investir
                            </a>
                        </td>
                    </tr>
{footer}'''

def send_otp_email(user_email, otp_code, purpose="connexion"):
    """Envoie un email avec le code OTP via SMTP - Template professionnel TokenFlow.

    Returns:
        tuple(bool, str|None): (success, error_message)
    """
    try:
        # Déterminer le titre et la description selon le but
        if purpose == "inscription":
            title = "Code de vérification - Inscription"
            description = "Bienvenue sur TokenFlow ! Entrez ce code pour créer votre compte :"
            subject = "Créez votre compte TokenFlow"
        elif purpose == "connexion":
            title = "Code de vérification - Connexion"
            description = "Pour sécuriser votre accès, confirmez avec ce code :"
            subject = "Connexion à TokenFlow"
        elif purpose == "reset_password":
            title = "Code de réinitialisation"
            description = "Vous avez demandé à réinitialiser votre mot de passe. Voici votre code :"
            subject = "Réinitialiser votre mot de passe TokenFlow"
        else:
            title = "Code de vérification TokenFlow"
            description = "Voici votre code de vérification :"
            subject = "Code de vérification - TokenFlow"
        
        html_content = create_otp_template(otp_code, title, description, user_email)
        text_content = f"TokenFlow - {title}\n\n{description}\n\nCode OTP: {otp_code}\n\nCe code expire dans 10 minutes.\n\nNe partagez jamais ce code."
        
        success, error = send_email_smtp(user_email, subject, html_content, text_content)
        if not success:
            print(f"[OTP] Erreur envoi email OTP: {error}")
            return False, error
        return True, None
    except Exception as e:
        print(f"❌ Erreur envoi email OTP: {e}")
        print(traceback.format_exc())
        return False, str(e)

def send_welcome_email(username, user_email):
    """Envoie un email de bienvenue TokenFlow."""
    try:
        html_content = create_welcome_template(username, user_email)
        text_content = f"Bienvenue {username} !\n\nVotre compte TokenFlow a été créé avec succès.\n\nConsultez votre tableau de bord: https://flowtoken.uk/dashboard"
        
        success, error = send_email_smtp(
            user_email,
            "Bienvenue sur TokenFlow !",
            html_content,
            text_content
        )
        return success, error
    except Exception as e:
        print(f"❌ Erreur envoi email de bienvenue: {e}")
        return False, str(e)

def send_deposit_confirmation_email(phone, amount, currency, reference, user_email):
    """Envoie un email de confirmation de dépôt."""
    try:
        html_content = create_deposit_template(phone, amount, currency, reference, user_email)
        text_content = f"Dépôt confirmé\n\nMontant: {amount:.2f} {currency}\nRéférence: {reference}\nDate: {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}"
        
        success, error = send_email_smtp(
            user_email,
            f"Dépôt confirmé - {amount:.2f} {currency}",
            html_content,
            text_content
        )
        return success, error
    except Exception as e:
        print(f"❌ Erreur envoi email confirmation dépôt: {e}")
        return False, str(e)

def send_withdrawal_confirmation_email(phone, amount, currency, reference, user_email):
    """Envoie un email de confirmation de retrait."""
    try:
        html_content = create_withdrawal_template(phone, amount, currency, reference, user_email)
        text_content = f"Demande de retrait\n\nMontant: {amount:.2f} {currency}\nVers: {phone}\nRéférence: {reference}\n\nTraitement en cours (1-2 jours)"
        
        success, error = send_email_smtp(
            user_email,
            f"Demande de retrait - {amount:.2f} {currency}",
            html_content,
            text_content
        )
        return success, error
    except Exception as e:
        print(f"❌ Erreur envoi email confirmation retrait: {e}")
        return False, str(e)

def send_product_notification_email(user_email, product_name, description, daily_roi, min_amount):
    """Envoie une notification de nouveau produit."""
    try:
        html_content = create_product_notification_template(product_name, description, daily_roi, min_amount, user_email)
        text_content = f"Nouveau produit TokenFlow!\n\n{product_name}\n\n{description}\n\nRendement quotidien: {daily_roi:.2f}%\nInvestissement minimum: {min_amount:.0f}"
        
        success, error = send_email_smtp(
            user_email,
            f"✨ Nouveau produit: {product_name}",
            html_content,
            text_content
        )
        return success, error
    except Exception as e:
        print(f"❌ Erreur envoi notification produit: {e}")
        return False, str(e)

def send_product_notification_email_with_image(user_email, product_name, description, daily_roi, price, image_url, username):
    """Envoie un email de notification de produit avec image."""
    try:
        # Générer le token de désinscription
        unsub_token = secrets.token_urlsafe(32)
        
        # Vérifier si l'utilisateur est déjà désinscrit
        unsubscribed = Unsubscribe.query.filter_by(user_email=user_email).first()
        if unsubscribed:
            return False, "Utilisateur désinscrit"
        
        header = get_email_header()
        footer = get_email_footer().format(user_email=user_email)
        
        html_content = f'''{header}
                    <!-- Product Announcement -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px;">
                            <div style="width: 70px; height: 70px; background: linear-gradient(135deg, #EC4899 0%, #DB2777 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px;">
                                <span style="font-size: 36px;">✨</span>
                            </div>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 800; color: #0F172A;">Nouveau Produit Disponible!</h1>
                        </td>
                    </tr>
                    
                    <!-- Greeting -->
                    <tr>
                        <td align="center" style="padding: 0 40px 20px;">
                            <p style="margin: 0; font-size: 16px; color: #475569;">Bonjour {username},</p>
                        </td>
                    </tr>
                    
                    <!-- Product Image -->
                    <tr>
                        <td align="center" style="padding: 0 40px 20px;">
                            <img src="{image_url}" alt="{product_name}" style="max-width: 100%; width: 300px; height: auto; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
                        </td>
                    </tr>
                    
                    <!-- Product Details Card -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <div style="background: linear-gradient(135deg, #EC4899 0%, #DB2777 100%); border-radius: 16px; padding: 30px; color: white; text-align: center;">
                                <h2 style="margin: 0 0 15px 0; font-size: 26px; font-weight: 800;">{product_name}</h2>
                                <p style="margin: 0 0 25px 0; font-size: 15px; opacity: 0.95; line-height: 1.6;">{description}</p>
                                
                                <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 25px;">
                                    <tr>
                                        <td style="padding: 15px; text-align: center; background: rgba(255,255,255,0.15); border-radius: 12px;">
                                            <p style="margin: 0 0 5px 0; font-size: 12px; opacity: 0.85; text-transform: uppercase; font-weight: 600;">Prix</p>
                                            <p style="margin: 0; font-size: 28px; font-weight: 900;">${price:.2f} USD</p>
                                        </td>
                                        <td style="width: 15px;"></td>
                                        <td style="padding: 15px; text-align: center; background: rgba(255,255,255,0.15); border-radius: 12px;">
                                            <p style="margin: 0 0 5px 0; font-size: 12px; opacity: 0.85; text-transform: uppercase; font-weight: 600;">Revenu Journalier</p>
                                            <p style="margin: 0; font-size: 28px; font-weight: 900;">${daily_roi:.2f} USD</p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 0; font-size: 14px; opacity: 0.9;">
                                    📈 Rendement: {(daily_roi/price*100):.1f}% par jour
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- CTA Button -->
                    <tr>
                        <td align="center" style="padding: 30px 40px;">
                            <a href="https://flowtoken.uk/produits_rapide" style="display: inline-block; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); color: #ffffff; text-decoration: none; padding: 16px 48px; border-radius: 12px; font-weight: 700; font-size: 16px; box-shadow: 0 8px 24px rgba(79, 70, 229, 0.3);">
                                🚀 Investir Maintenant
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Info Box -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <div style="background-color: #F0F9FF; border-left: 4px solid #3B82F6; padding: 15px 20px; border-radius: 8px;">
                                <p style="margin: 0; font-size: 13px; color: #1E40AF; line-height: 1.6;">
                                    💡 <strong>Conseil:</strong> Les places sont limitées pour ce produit. Investissez maintenant pour sécuriser votre rendement quotidien!
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Unsubscribe -->
                    <tr>
                        <td align="center" style="padding: 20px 40px 30px;">
                            <p style="margin: 0 0 10px 0; font-size: 12px; color: #94A3B8;">
                                Vous recevez cet email car vous êtes membre de TokenFlow.
                            </p>
                            <a href="https://flowtoken.uk/unsubscribe/{unsub_token}" style="font-size: 12px; color: #6366F1; text-decoration: none;">
                                Je ne souhaite plus recevoir d'emails marketing
                            </a>
                        </td>
                    </tr>
{footer}'''
        
        text_content = f"""Nouveau Produit TokenFlow!

{product_name}

{description}

Prix: ${price:.2f} USD
Revenu journalier: ${daily_roi:.2f} USD
Rendement: {(daily_roi/price*100):.1f}% par jour

Investissez maintenant: https://flowtoken.uk/produits_rapide

---
Pour vous désinscrire: https://flowtoken.uk/unsubscribe/{unsub_token}
"""
        
        success, error = send_email_smtp(
            user_email,
            f"✨ Nouveau produit: {product_name}",
            html_content,
            text_content
        )
        return success, error
    except Exception as e:
        print(f"❌ Erreur envoi notification produit avec image: {e}")
        return False, str(e)

def broadcast_new_product_email_async(product_id):
    """
    Version asynchrone de broadcast - exécutée en arrière-plan via threading.
    Récupère le produit depuis la base de données.
    """
    from datetime import datetime
    import time
    
    with app.app_context():
        product = CustomProduct.query.get(product_id)
        if not product:
            print(f"❌ Produit {product_id} introuvable pour broadcast")
            return None
        
        return broadcast_new_product_email(product, scheduled=False)

def broadcast_new_product_email(product, scheduled=False):
    """
    Envoie automatiquement un email de notification à TOUS les utilisateurs actifs
    lors de la création d'un nouveau produit.
    
    Fonctionnalités professionnelles:
    - Envoi uniquement aux utilisateurs ACTIFS (non bloqués, email vérifié)
    - Image du produit dans l'email
    - Bouton de désinscription
    - Notifications push téléphone + navigateur
    - Rate limiting (100 emails/minute)
    - Statistiques détaillées
    - Compatible Gmail SMTP, Resend, Brevo, Zoho
    - File d'attente en arrière-plan (threading)
    
    Args:
        product: Objet CustomProduct ou dictionnaire avec name, description, price_usd, daily_revenue_usd, image_filename
        scheduled: Si True, la campagne est planifiée
        
    Returns:
        dict: {'sent': int, 'failed': int, 'total': int, 'errors': list, 'campaign_id': int}
    """
    from datetime import datetime
    import time
    
    # Gérer à la fois les objets CustomProduct et les dictionnaires
    if hasattr(product, 'name'):
        # C'est un objet CustomProduct (SQLAlchemy model)
        product_name = product.name
        description = product.description or ''
        price_usd = float(product.price_usd)
        daily_revenue_usd = float(product.daily_revenue_usd)
        image_filename = product.image_filename or 'ai.jpg'
        product_id = product.id
    else:
        # C'est un dictionnaire
        product_name = product.get('name', 'Inconnu')
        description = product.get('description', '')
        price_usd = float(product.get('price_usd', 0))
        daily_revenue_usd = float(product.get('daily_revenue_usd', 0))
        image_filename = product.get('image_filename', 'ai.jpg')
        product_id = product.get('id', None)
    
    results = {
        'sent': 0,
        'failed': 0,
        'total': 0,
        'push_sent': 0,
        'notifications': 0,
        'errors': [],
        'product_name': product_name,
        'campaign_id': None,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        
        print("=" * 60)
        print(f"📢 [BROADCAST] Démarrage notification nouveau produit: {product_name}")
        print(f"   Prix: ${price_usd:.2f} USD")
        print(f"   Revenu journalier: ${daily_revenue_usd:.2f} USD")
        print(f"   Image: {image_filename}")
        print("=" * 60)
        
        # 1. Créer la campagne email
        campaign = EmailCampaign(
            campaign_type='product',
            product_id=product_id,
            subject=f"🚀 Nouveau Produit: {product_name}",
            created_by=session.get('phone', 'system') if not scheduled else 'scheduled'
        )
        db.session.add(campaign)
        db.session.commit()
        results['campaign_id'] = campaign.id
        
        # 2. Récupérer TOUS les utilisateurs ACTIFS (critères stricts)
        users = User.query.filter(
            User.email.isnot(None),
            User.email != '',
            User.email_verified == True,
            User.is_banned == False
        ).all()
        
        results['total'] = len(users)
        campaign.total_recipients = len(users)
        campaign.status = 'sending'
        campaign.started_at = datetime.utcnow()
        db.session.commit()
        
        print(f"👥 {len(users)} utilisateurs actifs éligibles trouvés")
        
        # Taux de limitation: 100 emails/minute pour éviter blocage SMTP
        RATE_LIMIT_DELAY = 0.6  # secondes entre chaque email
        email_count = 0
        batch_start = time.time()
        
        # 3. Envoyer à chaque utilisateur
        for i, user in enumerate(users, 1):
            try:
                # Vérifier si l'utilisateur n'est pas désinscrit des emails marketing
                unsubscribed = Unsubscribe.query.filter_by(user_email=user.email).first()
                if unsubscribed:
                    results['failed'] += 1
                    continue
                
                # 1. Créer la notification in-app
                notification = Notification(
                    user_phone=user.phone,
                    type='product',
                    title='🚀 Nouveau Produit Disponible!',
                    message=f'Découvrez notre nouveau produit: {product_name}. ROI journalier: ${daily_revenue_usd:.2f} USD',
                    action_url=url_for('produits_rapide_page', _external=True)
                )
                db.session.add(notification)
                campaign.notifications_created += 1
                results['notifications'] += 1
                
                # 2. Envoyer l'email avec image du produit
                # Utiliser une URL absolue explicite pour garantir que l'image s'affiche dans l'email
                if image_filename:
                    image_url = f"https://{SERVER_NAME}/static/vlogs/{image_filename}"
                else:
                    image_url = f"https://{SERVER_NAME}/static/vlogs/ai.jpg"
                
                success, error = send_product_notification_email_with_image(
                    user.email,
                    product_name,
                    description or f"Investissement à {(daily_revenue_usd/price_usd*100):.1f}% de rendement journalier",
                    daily_revenue_usd,
                    price_usd,
                    image_url,
                    user.username or user.phone
                )
                
                # 3. Log l'envoi email
                email_log = EmailLog(
                    campaign_id=campaign.id,
                    user_phone=user.phone,
                    user_email=user.email,
                    status='sent' if success else 'failed',
                    error_message=error,
                    sent_at=datetime.utcnow() if success else None
                )
                db.session.add(email_log)
                
                if success:
                    results['sent'] += 1
                    campaign.emails_sent += 1
                else:
                    results['failed'] += 1
                    campaign.emails_failed += 1
                    error_msg = f"Échec email pour {user.email}: {error or 'Erreur inconnue'}"
                    results['errors'].append(error_msg)
                
                # 4. Envoyer notification push (téléphone + navigateur)
                try:
                    push_result = send_push_notification_to_user(
                        user.phone,
                        '🚀 Nouveau Produit Disponible!',
                        f'Découvrez {product_name} et commencez à gagner dès aujourd\'hui.',
                        url=url_for('produits_rapide_page', _external=True),
                        require_interaction=False
                    )
                    if push_result:
                        campaign.push_sent += 1
                        results['push_sent'] += 1
                except Exception as push_error:
                    print(f"   ⚠️ Push error for {user.phone}: {push_error}")
                
                db.session.commit()
                
                # Rate limiting: pause après 100 emails
                email_count += 1
                if email_count >= 100:
                    elapsed = time.time() - batch_start
                    if elapsed < 60:
                        sleep_time = 60 - elapsed
                        print(f"   ⏱️ Rate limit: pause de {sleep_time:.1f}s après 100 emails...")
                        time.sleep(sleep_time)
                    email_count = 0
                    batch_start = time.time()
                else:
                    time.sleep(RATE_LIMIT_DELAY)
                
                if results['sent'] % 10 == 0:
                    print(f"   📧 {results['sent']}/{len(users)} emails envoyés...")
                    
            except Exception as user_error:
                results['failed'] += 1
                campaign.emails_failed += 1
                error_msg = f"Exception pour {user.email}: {str(user_error)}"
                results['errors'].append(error_msg)
                print(f"   ❌ {error_msg}")
                db.session.commit()
                # Continuer avec l'utilisateur suivant
        
        # Résumé final
        campaign.status = 'completed'
        campaign.completed_at = datetime.utcnow()
        db.session.commit()
        
        print("=" * 60)
        print(f"📊 [BROADCAST] Résumé:")
        print(f"   Total: {results['total']}")
        print(f"   Emails envoyés: {results['sent']}")
        print(f"   Échecs: {results['failed']}")
        print(f"   Notifications in-app: {results['notifications']}")
        print(f"   Notifications push: {results['push_sent']}")
        print(f"   Taux de réussite: {(results['sent']/results['total']*100) if results['total'] > 0 else 0:.1f}%")
        print("=" * 60)
        
        return results
        
    except Exception as e:
        error_msg = f"Erreur générale broadcast: {str(e)}"
        print(f"❌ {error_msg}")
        results['errors'].append(error_msg)
        if 'campaign' in locals():
            campaign.status = 'failed'
            db.session.commit()
        return results

@app.route("/academy/agriculture")
@login_required
def formation_agri_page():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    if not user:
        flash("Session expirée, reconnectez-vous.", "danger")
        return redirect(url_for("connexion_page"))

    return render_template("agriculture.html", user=user)

def is_valid_phone(phone):
    """Valide le format d'un numéro de téléphone international."""
    import re
    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    # Must start with + followed by 7-15 digits (E.164 format)
    pattern = r'^\+[1-9]\d{6,14}$'
    return bool(re.match(pattern, cleaned))

@app.route("/inscription", methods=["GET", "POST"])
def inscription_page():
    code_ref = request.args.get("ref", "").strip().upper()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()
        pays = request.form.get("pays", "").strip()
        code_invitation = request.form.get("code_invitation", "").strip().upper()

        if not username or not email or not phone or not password:
            flash("⚠️ Tous les champs obligatoires doivent être remplis.", "danger")
            return redirect(url_for("inscription_page"))

        # Validate phone number format (security)
        if not is_valid_phone(phone):
            flash("❌ Numéro de téléphone invalide. Veuillez entrer un numéro avec indicatif pays (ex: +22997000000).", "danger")
            return redirect(url_for("inscription_page"))

        if password != confirm:
            flash("❌ Les mots de passe ne correspondent pas.", "danger")
            return redirect(url_for("inscription_page"))

        if User.query.filter_by(phone=phone).first():
            flash("⚠️ Ce numéro est déjà enregistré.", "danger")
            return redirect(url_for("inscription_page"))

        if User.query.filter_by(email=email).first():
            flash("⚠️ Cet email est déjà enregistré.", "danger")
            return redirect(url_for("inscription_page"))

        parrain_user = None
        parrain_code_value = None
        if code_invitation:
            parrain_user = User.query.filter_by(referral_code=code_invitation).first()
            if not parrain_user:
                flash("⚠️ Code d'invitation invalide.", "warning")
            else:
                parrain_code_value = parrain_user.referral_code

        # Generate OTP for registration verification
        otp = generate_otp()
        otp_expires = datetime.utcnow() + timedelta(minutes=10)

        # Store OTP in session temporarily (user not created yet)
        session['pending_registration'] = {
            'username': username,
            'email': email,
            'phone': phone,
            'password': password,
            'pays': pays,
            'parrain_code': parrain_code_value,
            'otp': otp,
            'otp_expires': otp_expires.isoformat()
        }

        # Send OTP email
        success, error = send_otp_email(email, otp, "inscription")
        if not success:
            flash(f"⚠️ Erreur envoi email OTP. {error or 'Essayez encore.'}", "warning")
            return redirect(url_for("inscription_page"))
        flash("✅ Un code OTP a été envoyé à votre email. Veuillez le saisir pour compléter l'inscription.", "info")

        return redirect(url_for("verify_otp_page", action="inscription"))

    return render_template("inscription.html", code_ref=code_ref)

@app.route("/verify-otp/<action>", methods=["GET", "POST"])
def verify_otp_page(action):
    if action not in ["inscription", "connexion", "reset_password"]:
        flash("Action invalide.", "danger")
        return redirect(url_for("connexion_page"))

    if request.method == "POST":
        otp_input = request.form.get("otp", "").strip()

        if not otp_input:
            flash("Veuillez entrer le code OTP.", "danger")
            return redirect(url_for("verify_otp_page", action=action))

        if action == "inscription":
            pending = session.get('pending_registration')
            if not pending:
                flash("Session expirée. Veuillez vous réinscrire.", "danger")
                return redirect(url_for("inscription_page"))

            # Check OTP
            if otp_input != pending['otp']:
                flash("Code OTP incorrect.", "danger")
                return redirect(url_for("verify_otp_page", action=action))

            # Check expiration
            otp_expires = datetime.fromisoformat(pending['otp_expires'])
            if datetime.utcnow() > otp_expires:
                flash("Code OTP expiré. Veuillez vous réinscrire.", "danger")
                session.pop('pending_registration', None)
                return redirect(url_for("inscription_page"))

            # Check if user is among first 200 registrations for welcome bonus
            total_users = User.query.count()
            welcome_bonus = 1.0 if total_users < 200 else 0.0
            
            # Create user
            new_user = User(
                username=pending['username'],
                email=pending['email'],
                phone=pending['phone'],
                password=pending['password'],
                wallet_country=pending['pays'],
                solde_total=welcome_bonus,
                solde_depot=welcome_bonus,
                solde_revenu=0,
                solde_parrainage=0,
                parrain_code=pending['parrain_code'],
                otp_verified=True
            )

            db.session.add(new_user)
            db.session.commit()

            # Generate verification token and send email
            token = generate_verification_token()
            new_user.email_verification_token = token
            new_user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()

            # Send verification email
            try:
                send_verification_email(pending['email'], token)
            except Exception as e:
                print(f"Erreur envoi email verification: {e}")

            # Send welcome email
            try:
                send_welcome_email(pending['username'], pending['email'])
            except Exception as e:
                print(f"Erreur envoi email de bienvenue: {e}")

            # Clear pending registration
            session.pop('pending_registration', None)

            flash("🎉 Inscription réussie ! Vérifiez votre email et connectez-vous.", "success")
            return redirect(url_for("connexion_page"))

        elif action == "connexion":
            phone = session.get('pending_login_phone')
            if not phone:
                flash("Session expirée. Veuillez vous reconnecter.", "danger")
                return redirect(url_for("connexion_page"))

            user = User.query.filter_by(phone=phone).first()
            if not user:
                flash("Utilisateur introuvable.", "danger")
                session.pop('pending_login_phone', None)
                return redirect(url_for("connexion_page"))

            # Check OTP
            if not user.otp_code or otp_input != user.otp_code:
                flash("Code OTP incorrect.", "danger")
                return redirect(url_for("verify_otp_page", action=action))

            # Check expiration
            if user.otp_expires and datetime.utcnow() > user.otp_expires:
                flash("Code OTP expiré. Veuillez vous reconnecter.", "danger")
                user.otp_code = None
                user.otp_expires = None
                db.session.commit()
                session.pop('pending_login_phone', None)
                return redirect(url_for("connexion_page"))

            # Clear OTP and log in
            user.otp_code = None
            user.otp_expires = None
            user.otp_verified = True
            db.session.commit()

            session['phone'] = user.phone
            session.pop('pending_login_phone', None)

            flash("✅ Connexion réussie ! Bienvenue sur TokenFlow.", "success")
            return redirect(url_for("dashboard_page"))

        elif action == "reset_password":
            reset_email = session.get('reset_email')
            if not reset_email:
                flash("Session expirée. Veuillez recommencer.", "danger")
                return redirect(url_for("forgot_password_page"))
            
            user = User.query.filter_by(email=reset_email).first()
            if not user:
                flash("Utilisateur introuvable.", "danger")
                session.pop('reset_email', None)
                return redirect(url_for("forgot_password_page"))
            
            # Check OTP
            if not user.otp_code or otp_input != user.otp_code:
                flash("Code OTP incorrect.", "danger")
                return redirect(url_for("verify_otp_page", action=action))
            
            # Check expiration
            if user.otp_expires and datetime.utcnow() > user.otp_expires:
                flash("Code OTP expiré. Veuillez recommencer.", "danger")
                user.otp_code = None
                user.otp_expires = None
                db.session.commit()
                session.pop('reset_email', None)
                return redirect(url_for("forgot_password_page"))
            
            # OTP verified, redirect to reset password page
            user.otp_code = None
            user.otp_expires = None
            db.session.commit()
            
            flash("✅ Code OTP vérifié ! Vous pouvez maintenant réinitialiser votre mot de passe.", "success")
            return redirect(url_for("reset_password_page"))

    return render_template("verify_otp.html", action=action)

@app.route("/resend-otp/<action>", methods=["POST"])
def resend_otp_page(action):
    if action == "inscription":
        pending = session.get('pending_registration')
        if pending:
            otp = generate_otp()
            pending['otp'] = otp
            pending['otp_expires'] = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            session['pending_registration'] = pending
            success, error = send_otp_email(pending['email'], otp, "inscription")
            if success:
                flash("✅ Nouveau code OTP envoyé !", "success")
            else:
                flash(f"⚠️ Impossible de renvoyer le code OTP. {error or 'Réessayez plus tard.'}", "warning")
    elif action == "connexion":
        phone = session.get('pending_login_phone')
        if phone:
            user = User.query.filter_by(phone=phone).first()
            if user:
                otp = generate_otp()
                user.otp_code = otp
                user.otp_expires = datetime.utcnow() + timedelta(minutes=10)
                db.session.commit()
                success, error = send_otp_email(user.email, otp, "connexion")
                if success:
                    flash("✅ Nouveau code OTP envoyé !", "success")
                else:
                    flash(f"⚠️ Impossible de renvoyer le code OTP. {error or 'Réessayez plus tard.'}", "warning")
    return redirect(url_for("verify_otp_page", action=action))

@app.route("/unsubscribe/<token>")
def unsubscribe_page(token):
    """Page de désinscription des emails marketing."""
    unsub = Unsubscribe.query.filter_by(unsubscribe_token=token).first()
    
    if not unsub:
        flash("Lien de désinscription invalide.", "danger")
        return redirect(url_for("index_page"))
    
    # Si l'utilisateur est connecté, on met à jour son statut
    if session.get('phone'):
        user = User.query.filter_by(phone=session['phone']).first()
        if user and user.email == unsub.user_email:
            unsub.user_phone = user.phone
            db.session.commit()
    
    flash("✅ Vous avez été désinscrit avec succès des emails marketing.", "success")
    return render_template("unsubscribe.html", user_email=unsub.user_email)

@app.route("/verify-email/<token>")
def verify_email(token):
    """Route pour vérifier l'email d'un utilisateur via le token de vérification."""
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        flash("Lien de vérification invalide ou expiré.", "danger")
        return redirect(url_for("connexion_page"))
    
    # Vérifier si le token a expiré (24 heures)
    if user.verification_token_expires and datetime.utcnow() > user.verification_token_expires:
        flash("Lien de vérification expiré. Veuillez vous reconnecter pour en recevoir un nouveau.", "danger")
        # Réinitialiser le token pour permettre une nouvelle vérification
        user.email_verification_token = None
        user.verification_token_expires = None
        db.session.commit()
        return redirect(url_for("connexion_page"))
    
    # Vérifier si l'email est déjà vérifié
    if user.email_verified:
        flash("Votre email est déjà vérifié.", "success")
        return redirect(url_for("dashboard_page"))
    
    # Marquer l'email comme vérifié
    user.email_verified = True
    user.email_verification_token = None
    user.verification_token_expires = None
    db.session.commit()
    
    flash("✅ Votre email a été vérifié avec succès !", "success")
    
    # Si l'utilisateur est connecté, le rediriger vers le dashboard
    if session.get('phone'):
        return redirect(url_for("dashboard_page"))
    
    # Sinon, le rediriger vers la page de connexion
    return redirect(url_for("connexion_page"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password_page():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        
        if not email:
            flash("Veuillez entrer votre email.", "danger")
            return redirect(url_for("forgot_password_page"))
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash("Aucun compte trouvé avec cet email.", "warning")
            return redirect(url_for("forgot_password_page"))
        
        # Generate OTP for password reset
        otp = generate_otp()
        user.otp_code = otp
        user.otp_expires = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()
        
        # Store email in session for reset verification
        session['reset_email'] = email
        
        # Send OTP email
        success, error = send_otp_email(email, otp, "reset_password")
        if not success:
            flash(f"⚠️ Erreur envoi email OTP. {error or 'Réessayez.'}", "warning")
            return redirect(url_for("forgot_password_page"))
        flash("✅ Un code OTP a été envoyé à votre email. Veuillez le saisir pour réinitialiser votre mot de passe.", "info")
        
        return redirect(url_for("verify_otp_page", action="reset_password"))
    
    return render_template("forgot_password.html")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password_page():
    # Check if user has verified OTP for reset
    reset_email = session.get('reset_email')
    
    if not reset_email:
        flash("Session expirée. Veuillez recommencer la réinitialisation.", "danger")
        return redirect(url_for("forgot_password_page"))
    
    user = User.query.filter_by(email=reset_email).first()
    
    if not user:
        flash("Utilisateur introuvable.", "danger")
        session.pop('reset_email', None)
        return redirect(url_for("forgot_password_page"))
    
    if request.method == "POST":
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        
        if not new_password or not confirm_password:
            flash("Veuillez remplir tous les champs.", "danger")
            return redirect(url_for("reset_password_page"))
        
        if new_password != confirm_password:
            flash("Les mots de passe ne correspondent pas.", "danger")
            return redirect(url_for("reset_password_page"))
        
        if len(new_password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères.", "danger")
            return redirect(url_for("reset_password_page"))
        
        # Update password
        user.password = new_password
        db.session.commit()
        
        # Clear session
        session.pop('reset_email', None)
        
        flash("✅ Mot de passe réinitialisé avec succès ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for("connexion_page"))
    
    return render_template("reset_password.html")

@app.route("/connexion", methods=["GET", "POST"])
def connexion_page():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()

        if not identifier or not password:
            flash({"title": "Erreur", "message": "Veuillez remplir tous les champs."}, "danger")
            return redirect(url_for("connexion_page"))

        # Déterminer si l'identifiant est un email ou un numéro
        user = None
        if "@" in identifier:
            user = User.query.filter_by(email=identifier.lower()).first()
        else:
            user = User.query.filter_by(phone=identifier).first()

        if not user:
            flash({"title": "Erreur", "message": "Identifiant introuvable."}, "danger")
            return redirect(url_for("connexion_page"))

        if user.password != password:
            flash({"title": "Erreur", "message": "Mot de passe incorrect."}, "danger")
            return redirect(url_for("connexion_page"))

        # Toujours exiger la vérification par email
        if not getattr(user, 'email_verified', False):
            try:
                token = generate_verification_token()
                user.email_verification_token = token
                user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
                db.session.commit()
                sent = send_verification_email(user.email, token)
                if sent:
                    flash("⚠️ Votre email n'est pas vérifié. Un email de vérification vient d'être envoyé.", "warning")
                else:
                    flash("⚠️ Impossible d'envoyer l'email de vérification. Contactez le support.", "warning")
            except Exception as e:
                print(f"Erreur envoi email de vérification: {e}")
                flash("⚠️ Erreur lors de l'envoi du mail de vérification.", "warning")
            return redirect(url_for("connexion_page"))

        # Generate and send OTP before login
        otp = generate_otp()
        user.otp_code = otp
        user.otp_expires = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()

        # Store phone in session for OTP verification
        session['pending_login_phone'] = user.phone

        # Send OTP email
        success, error = send_otp_email(user.email, otp, "connexion")
        if not success:
            flash(f"⚠️ Erreur envoi email OTP. {error or 'Réessayez.'}", "warning")
            return redirect(url_for("connexion_page"))
        flash("✅ Un code OTP a été envoyé à votre email. Veuillez le saisir pour compléter la connexion.", "info")

        return redirect(url_for("verify_otp_page", action="connexion"))

    return render_template("connexion.html")

@app.route("/logout")
def logout_page():
    session.clear()
    flash("Déconnexion effectuée.", "info")
    return redirect(url_for("connexion_page"))

@app.route("/")
def index_page():
    """Page d'accueil - redirige vers connexion si déjà connecté, sinon affiche landing page"""
    phone = get_logged_in_user_phone()
    if phone:
        return redirect(url_for("dashboard_page"))
    return render_template("index.html")

@app.route("/contact")
def contact_page():
    """Page de contact"""
    return render_template("contact.html")

@app.route("/partner")
def partner_page():
    """Page devenir partenaire"""
    return render_template("partner.html")

@app.route("/test-email")
def test_email_page():
    """Route de test pour déboguer l'envoi d'emails."""
    to_email = request.args.get('to', 'test@example.com')
    
    print("=" * 60)
    print("[EMAIL TEST] Démarrage du test d'envoi d'email...")
    print("=" * 60)
    
    # Debug: afficher toutes les sources de configuration
    print("[DEBUG] Sources de configuration SMTP:")
    print(f"  os.getenv('SMTP_SERVER') = {os.getenv('SMTP_SERVER')}")
    print(f"  os.getenv('SMTP_PORT') = {os.getenv('SMTP_PORT')}")
    print(f"  os.getenv('SMTP_USER') = {os.getenv('SMTP_USER')}")
    print(f"  os.getenv('SMTP_PASSWORD') = {'*' * len(os.getenv('SMTP_PASSWORD', '')) if os.getenv('SMTP_PASSWORD') else 'None'}")
    print(f"  os.getenv('EMAIL_FROM') = {os.getenv('EMAIL_FROM')}")
    
    # Vérifier si le .env est chargé
    print(f"[DEBUG] load_dotenv() a été appelé: {load_dotenv.called if hasattr(load_dotenv, 'called') else 'N/A'}")
    
    # Test the email function
    subject = "Test Email TokenFlow"
    html_content = "<h1>Test Email</h1><p>Si you recevez cet email, le système SMTP fonctionne !</p>"
    text_content = "Test Email - Si you recevez cet email, le système SMTP fonctionne !"
    
    success = send_email_smtp(to_email, subject, html_content, text_content)
    
    if success:
        result = f"✅ Email envoyé avec succès à {to_email}"
    else:
        result = f"❌ Échec de l'envoi d'email à {to_email}"
    
    print("=" * 60)
    print(f"[EMAIL TEST] Résultat: {result}")
    print("=" * 60)
    
    return f"""
    <html>
    <head><title>Test Email</title></head>
    <body style="font-family: sans-serif; padding: 40px;">
        <h1>Test d'Envoi d'Email</h1>
        <p><strong>Email envoyé à:</strong> {to_email}</p>
        <p><strong>Résultat:</strong> {result}</p>
        <hr>
        <h2>Configuration SMTP actuelle:</h2>
        <ul>
            <li><strong>SMTP_SERVER:</strong> {os.getenv('SMTP_SERVER', 'smtp.gmail.com')}</li>
            <li><strong>SMTP_PORT:</strong> {os.getenv('SMTP_PORT', '587')}</li>
            <li><strong>SMTP_USER:</strong> {os.getenv('SMTP_USER', 'NON CONFIGURÉ')}</li>
            <li><strong>SMTP_PASSWORD:</strong> {'*' * len(os.getenv('SMTP_PASSWORD', '')) if os.getenv('SMTP_PASSWORD') else 'NON CONFIGURÉ'}</li>
            <li><strong>EMAIL_FROM:</strong> {os.getenv('EMAIL_FROM', 'TokenFlow <support@flowtoken.uk>')}</li>
        </ul>
        <hr>
        <h2>Instructions:</h2>
        <ol>
            <li>Vérifiez que SMTP_USER est votre adresse Gmail complète</li>
            <li>Vérifiez que SMTP_PASSWORD est un mot de passe d'application (16 caractères, sans espaces)</li>
            <li>Vérifiez que la validation en deux étapes est activée sur votre compte Google</li>
            <li>Regardez la console du terminal pour les logs détaillés</li>
        </ol>
        <hr>
        <p><a href="/test-email?to={to_email}">🔄 Réessayer</a></p>
    </body>
    </html>
    """

@app.route("/sitemap.xml")
def sitemap():
    """Génère le sitemap XML pour le SEO Google"""
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://flowtoken.uk/</loc>
        <lastmod>2026-05-19</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://flowtoken.uk/inscription</loc>
        <lastmod>2026-05-19</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://flowtoken.uk/connexion</loc>
        <lastmod>2026-05-19</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://flowtoken.uk/nous</loc>
        <lastmod>2026-05-19</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://flowtoken.uk/contact</loc>
        <lastmod>2026-05-19</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://flowtoken.uk/produits_rapide</loc>
        <lastmod>2026-05-19</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://flowtoken.uk/team</loc>
        <lastmod>2026-05-19</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>
</urlset>'''
    return app.response_class(xml, mimetype='text/xml')

def get_global_stats():
    total_users = db.session.query(func.count(User.id)).scalar() or 0
    total_deposits = db.session.query(func.sum(Depot.montant)).scalar() or 0
    total_invested = db.session.query(func.sum(Investissement.montant)).scalar() or 0
    total_withdrawn = db.session.query(func.sum(Retrait.montant)).scalar() or 0
    return total_users, total_deposits, total_invested, total_withdrawn

@app.route("/dashboard")
@login_required
def dashboard_page():
    """Dashboard par défaut - utilise l'ancien template"""
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    if not user:
        session.clear()
        flash("Session invalide, veuillez vous reconnecter.", "danger")
        return redirect(url_for("connexion_page"))

    total_users, total_deposits, total_invested, total_withdrawn = get_global_stats()
    revenu_cumule = (user.solde_parrainage or 0) + (user.solde_revenu or 0)

    investissements_actifs = []
    now = datetime.utcnow()
    actifs_raw = Investissement.query.filter_by(phone=phone, actif=True).all()
    
    for inv in actifs_raw:
        jours_passes = (now - inv.date_debut).days
        progression = min(int((jours_passes / inv.duree) * 100), 100) if inv.duree > 0 else 100
        investissements_actifs.append({
            "nom_produit": f"Plan Fly {int(inv.montant)}",
            "montant": inv.montant,
            "revenu_journalier": inv.revenu_journalier,
            "jours_restants": max(inv.duree - jours_passes, 0),
            "progression": progression
        })
    
    transactions_recentes = []
    recent_depots = Depot.query.filter_by(phone=phone).order_by(Depot.date.desc()).limit(3).all()
    for d in recent_depots:
        transactions_recentes.append({
            "type": "deposit", "icon": "fa-plus", "description": "Dépôt de fonds",
            "date": d.date.strftime("%d %b"), "montant": d.montant, "amount_type": "plus"
        })
    
    recent_retraits = Retrait.query.filter_by(phone=phone).order_by(Retrait.date.desc()).limit(3).all()
    for r in recent_retraits:
        transactions_recentes.append({
            "type": "withdraw", "icon": "fa-paper-plane", "description": "Retrait de fonds",
            "date": r.date.strftime("%d %b"), "montant": r.montant, "amount_type": "minus"
        })
    
    user.investissements_actifs = sorted(investissements_actifs, key=lambda x: x['progression'], reverse=True)
    investissements_actifs_top = user.investissements_actifs[:5]
    user.transactions_recentes = sorted(transactions_recentes, key=lambda x: x['date'], reverse=True)[:5]
    
    # Compter les membres de l'équipe via parrain_code
    user_referral_code = user.referral_code if user.referral_code else phone
    user.team_members = User.query.filter_by(parrain_code=user_referral_code).count()

    return render_template(
        "dashboard.html",
        user=user,
        revenu_cumule=revenu_cumule,
        total_users=total_users,
        total_invested=total_invested,
        investissements_actifs_top=investissements_actifs_top,
    )

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        phone = session.get("phone")
        user = User.query.filter_by(phone=phone).first() if phone else None
        if not user or not user.is_admin:
            flash("Accès réservé aux administrateurs.", "danger")
            return redirect(url_for("connexion_page"))
        return f(*args, **kwargs)
    return decorated

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login_page():
    """Page de connexion dédiée pour les administrateurs."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Veuillez remplir tous les champs.", "error")
            return redirect(url_for("admin_login_page"))

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Aucun compte trouvé avec cet email.", "error")
            return redirect(url_for("admin_login_page"))

        if not user.is_admin:
            flash("Accès refusé. Cet email n'a pas les privilèges administrateur.", "error")
            return redirect(url_for("admin_login_page"))

        if user.password != password:
            flash("Mot de passe incorrect.", "error")
            return redirect(url_for("admin_login_page"))

        if user.is_banned:
            flash("Ce compte administrateur est suspendu.", "error")
            return redirect(url_for("admin_login_page"))

        # Connexion réussie
        session["phone"] = user.phone
        flash("✅ Connexion administrateur réussie !", "success")
        return redirect(url_for("admin_dashboard"))

    # GET request - show login page
    # Check if already logged in as admin
    phone = get_logged_in_user_phone()
    if phone:
        user = User.query.filter_by(phone=phone).first()
        if user and user.is_admin:
            return redirect(url_for("admin_dashboard"))

    return render_template("admin_login.html")

@app.route("/admin")
@login_required
def admin_dashboard():
    # Check if user is admin
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()
    if not user or not user.is_admin:
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("connexion_page"))
    
    # Calculate comprehensive stats
    total_users = User.query.count()
    active_users = User.query.filter_by(is_banned=False).count()
    banned_users = User.query.filter_by(is_banned=True).count()
    verified_users = User.query.filter_by(email_verified=True).count()
    
    # Get deposits - amounts are now stored in USD directly (no XOF conversion)
    total_deposits = db.session.query(db.func.sum(Depot.montant)).filter_by(statut="valide").scalar() or 0
    pending_deposits = db.session.query(db.func.sum(Depot.montant)).filter_by(statut="pending").scalar() or 0
    
    total_withdrawals = db.session.query(db.func.sum(Retrait.montant)).filter_by(statut="validé").scalar() or 0
    pending_withdrawals = db.session.query(db.func.sum(Retrait.montant)).filter_by(statut="en_attente").scalar() or 0
    
    total_referral_withdrawals = db.session.query(db.func.sum(Retrait.montant)).join(User, User.phone == Retrait.phone).filter(
        Retrait.statut == "validé",
        User.solde_parrainage != None
    ).scalar() or 0
    
    total_commissions = db.session.query(db.func.sum(Commission.montant)).scalar() or 0
    
    total_invested = db.session.query(db.func.sum(Investissement.montant)).scalar() or 0
    active_investments = Investissement.query.filter_by(actif=True).count()
    
    # Total referrals (users with parrain_code)
    total_referrals = User.query.filter(User.parrain_code.isnot(None)).count()
    
    # Top referrer
    from sqlalchemy import func, distinct
    top_referrer = db.session.query(
        User.phone,
        User.username,
        User.referral_code,
        func.count(User.id).label('referral_count')
    ).filter(User.parrain_code.isnot(None)).group_by(
        User.parrain_code, User.phone, User.username, User.referral_code
    ).order_by(func.count(User.id).desc()).first()
    
    # Get top 10 referrers with their commission data
    # First, get all users who have referred others
    top_referrers_query = db.session.query(
        User.parrain_code,
        func.count(User.id).label('referral_count')
    ).filter(
        User.parrain_code.isnot(None)
    ).group_by(
        User.parrain_code
    ).order_by(
        func.count(User.id).desc()
    ).limit(10).all()
    
    # Build top referrers list by looking up each referrer
    top_referrers = []
    for r in top_referrers_query:
        referrer = User.query.filter_by(referral_code=r.parrain_code).first()
        if referrer:
            top_referrers.append({
                'id': referrer.id,
                'phone': referrer.phone,
                'username': referrer.username,
                'referral_code': referrer.referral_code,
                'total_commissions': referrer.commission_total or 0,
                'referral_count': r.referral_count
            })
    
    # Recent commissions
    recent_commissions = Commission.query.order_by(Commission.date.desc()).limit(20).all()
    
    # Get recent data for the dashboard
    users = User.query.order_by(User.date_creation.desc()).limit(50).all()
    deposits = Depot.query.order_by(Depot.date.desc()).limit(50).all()
    withdrawals = Retrait.query.order_by(Retrait.date.desc()).limit(50).all()
    
    stats = {
        "total_users": total_users,
        "active_users": active_users,
        "banned_users": banned_users,
        "verified_users": verified_users,
        "total_deposits": total_deposits,
        "pending_deposits": pending_deposits,
        "total_withdrawals": total_withdrawals,
        "pending_withdrawals": pending_withdrawals,
        "total_referral_withdrawals": total_referral_withdrawals,
        "total_commissions": total_commissions,
        "total_invested": total_invested,
        "active_investments": active_investments,
        "total_referrals": total_referrals,
        "top_referrer_username": top_referrer.username if top_referrer else "N/A",
        "top_referrer_count": top_referrer.referral_count if top_referrer else 0
    }
    
    # Get custom products for the products section
    products = CustomProduct.query.order_by(CustomProduct.created_at.desc()).all()
    
    return render_template(
        "admin_dashboard.html",
        stats=stats,
        users=users,
        deposits=deposits,
        withdrawals=withdrawals,
        top_referrers=top_referrers,
        recent_commissions=recent_commissions,
        products=products
    )

@app.route("/rules")
@login_required
def rules_page():
    return render_template("rules.html")

@app.route("/admin/users")
@login_required
def admin_users():
    users = User.query.order_by(User.date_creation.desc()).all()
    return render_template("admin/users.html", users=users)

@app.route("/admin/user/<int:user_id>/balance", methods=["POST"])
@login_required
def admin_balance(user_id):
    user = User.query.get_or_404(user_id)
    action = request.form.get("action")
    try:
        montant = float(request.form.get("montant", 0))
    except ValueError:
        flash("Montant invalide", "danger")
        return redirect(request.referrer)

    if montant <= 0:
        flash("Montant invalide", "danger")
        return redirect(request.referrer)

    if action == "credit":
        user.solde_total += montant
    elif action == "debit":
        if user.solde_total < montant:
            flash("Solde insuffisant", "danger")
            return redirect(request.referrer)
        user.solde_total -= montant

    db.session.commit()
    flash("Opération réussie ✅", "success")
    return redirect(request.referrer)

@app.route("/admin/user/balance", methods=["POST"])
@login_required
def admin_user_balance():
    """Permet à l'admin de créditer ou débiter un utilisateur."""
    phone = get_logged_in_user_phone()
    user_admin = User.query.filter_by(phone=phone).first()
    
    if not user_admin or not user_admin.is_admin:
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("connexion_page"))
    
    user_id = request.form.get("user_id")
    action = request.form.get("action")
    
    try:
        montant = float(request.form.get("montant", 0))
    except ValueError:
        flash("❌ Montant invalide", "danger")
        return redirect(request.referrer)
    
    if montant <= 0:
        flash("❌ Le montant doit être supérieur à 0", "danger")
        return redirect(request.referrer)
    
    user = User.query.get(int(user_id))
    if not user:
        flash("❌ Utilisateur introuvable", "danger")
        return redirect(request.referrer)
    
    if action == "credit":
        user.solde_total += montant
        flash(f"✅ {montant} USD crédités à {user.phone}. Nouveau solde: ${user.solde_total:.2f}", "success")
    elif action == "debit":
        if user.solde_total < montant:
            flash(f"❌ Solde insuffisant. Solde actuel: ${user.solde_total:.2f}", "danger")
            return redirect(request.referrer)
        user.solde_total -= montant
        flash(f"✅ {montant} USD débités de {user.phone}. Nouveau solde: ${user.solde_total:.2f}", "success")
    else:
        flash("❌ Action invalide", "danger")
        return redirect(request.referrer)
    
    db.session.commit()
    return redirect(request.referrer)

@app.route("/admin/user/<int:user_id>/toggle-ban")
@login_required
def toggle_ban(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = not getattr(user, "is_banned", False)
    db.session.commit()
    flash(
        "Compte suspendu ⛔" if user.is_banned else "Compte réactivé ✅",
        "warning" if user.is_banned else "success"
    )
    return redirect(request.referrer)

@app.route("/admin/user/<int:user_id>/quick-invest", methods=["POST"])
@login_required
def quick_invest(user_id):
    user = User.query.get_or_404(user_id)
    try:
        montant = float(request.form.get("montant"))
        duree = int(request.form.get("duree"))
        revenu_journalier = float(request.form.get("revenu_journalier"))
    except (ValueError, TypeError):
        flash("Valeurs invalides", "danger")
        return redirect(request.referrer)

    inv = Investissement(
        phone=user.phone,
        montant=montant,
        revenu_journalier=revenu_journalier,
        duree=duree
    )
    db.session.add(inv)
    db.session.commit()
    flash("Investissement activé ✅", "success")
    return redirect(request.referrer)

@app.before_request
def check_banned_user():
    if "phone" in session:
        user = User.query.filter_by(phone=session["phone"]).first()
        if user and getattr(user, "is_banned", False):
            flash("⛔ Votre compte est suspendu", "danger")
            session.pop("phone", None)
            return redirect(url_for("connexion_page"))

# La fonction get_logged_in_user_phone est déjà définie plus haut
# Suppression de la définition dupliquée

@app.route("/deposit", methods=["GET"])
@login_required
def deposit_page():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    if not user:
        flash("Utilisateur introuvable", "danger")
        return redirect(url_for("connexion_page"))

    return render_template("deposit.html", user=user)

# ============================================
# FONCTIONS DE CRYPTAGE POUR DONNÉES SENSIBLES
# ============================================
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Clé de cryptage dérivée d'une clé secrète
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'tokenflow-secret-key-change-in-production')

def get_fernet():
    """Crée une instance Fernet pour le cryptage/décryptage."""
    # Dériver une clé de 32 bytes à partir de la clé secrète
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'tokenflow-salt',
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY.encode()))
    return Fernet(key)

def encrypt_sensitive_data(data):
    """Crypte une donnée sensible."""
    try:
        f = get_fernet()
        return f.encrypt(data.encode()).decode()
    except Exception:
        return None

def decrypt_sensitive_data(encrypted_data):
    """Décrypte une donnée sensible."""
    try:
        f = get_fernet()
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return None

def hash_cvc(cvc):
    """Hash le CVC (ne devrait jamais être stocké en clair ou decryptable)."""
    return hashlib.sha256(cvc.encode()).hexdigest()

# ============================================
# SOLEASPAY API INTEGRATION
# ============================================

def soleaspay_create_payment(amount, phone, country_code, service_id, reference, fullname="", email=""):
    """
    Crée une demande de paiement via l'API SoleasPay.
    Retourne un dictionnaire avec le statut et les informations de réponse.
    """
    import json
    
    # Récupérer les infos du service
    service = get_service_by_id(country_code, service_id)
    if not service:
        print(f"Service introuvable pour country_code={country_code}, service_id={service_id}")
        return {"success": False, "message": "Service introuvable"}
    
    headers = {
        'x-api-key': SOLEAS_API_KEY,
        'operation': '2',
        'service': str(service_id),
        'Content-Type': 'application/json'
    }
    
    payload = {
        'wallet': phone,  # Numéro saisi par l'utilisateur
        'amount': amount,
        'currency': 'XOF',
        'order_id': reference,
        'description': f"Dépôt TokenFlow reference={reference}",
        'payer': fullname,
        'payerEmail': email,
        'successUrl': url_for('deposit_page', _external=True),
        'failureUrl': url_for('deposit_page', _external=True),
    }
    
    try:
        response = requests.post(
            'https://soleaspay.com/api/agent/bills/v3',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        result = response.json()
        print(f"Réponse SoleasPay: {result}")
        
        # Retourner la réponse complète pour analyse
        return {
            "success": result.get('succès') or result.get('success') or response.status_code == 200,
            "data": result,
            "message": result.get('message', 'Paiement initié avec succès')
        }
    except Exception as e:
        print(f"Exception SoleasPay: {e}")
        return {"success": False, "message": str(e)}

def verify_soleaspay_webhook(signature, payload):
    """Vérifie la signature du webhook SoleasPay."""
    expected_signature = hmac.new(
        SOLEAS_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

@app.route("/api/soleaspay/countries", methods=["GET"])
@login_required
def api_soleaspay_countries():
    """Retourne la liste des pays et opérateurs disponibles."""
    countries = get_available_countries()
    return jsonify(countries)

@app.route("/api/soleaspay/services/<country_code>", methods=["GET"])
@login_required
def api_soleaspay_services(country_code):
    """Retourne les services disponibles pour un pays donné."""
    services = SOLEAS_SERVICES.get(country_code.upper(), [])
    return jsonify(services)

@app.route("/webhook/soleaspay", methods=["POST"])
def soleaspay_webhook():
    """Webhook pour les notifications de paiement SoleasPay."""
    import json

    # Vérifier la signature
    signature = request.headers.get('X-SoleasPay-Signature', '')
    payload = request.get_data()

    if not verify_soleaspay_webhook(signature, payload):
        return jsonify({'error': 'Invalid signature'}), 401

    data = request.get_json()

    event_type = data.get('event')
    reference = data.get('reference')

    if event_type == 'payment.completed':
        # Trouver le dépôt par référence
        depot = Depot.query.filter_by(reference=reference).first()

        if depot and depot.statut == 'pending':
            user = User.query.filter_by(phone=depot.phone).first()

            if user:
                # CORRECTION PARRAINAGE : On compte les dépôts validés AVANT d'activer celui-ci
                nb_depots_valides = Depot.query.filter_by(phone=user.phone, statut='valide').count()

                # Validation du dépôt actuel
                depot.statut = 'valide'
                
                # Gestion des devises :
                # Si depot.montant est en XOF dans ta BDD, conversion en USD pour les soldes de l'User
                # Si depot.montant est DEJA en USD, laisse : user.solde_depot += depot.montant
                montant_usd = float(depot.montant) / 625  # À retirer si le montant en BDD est déjà en USD
                
                user.solde_depot = (user.solde_depot or 0) + montant_usd
                user.solde_total = (user.solde_total or 0) + montant_usd

                # Déclenchement de la commission si c'est strictement son premier dépôt
                if nb_depots_valides == 0 and user.parrain_code:
                    # On envoie le montant converti ou brut selon ce qu'attend ta fonction
                    donner_commission(user.phone, montant_usd)

                db.session.commit()

                # Créer une notification textuelle propre et claire
                create_notification(
                    user.phone,
                    'deposit',
                    'Dépôt validé',
                    f'Votre dépôt de ${montant_usd:.2f} USD a été validé avec succès.'
                )

    return jsonify({'status': 'ok'}), 200

# No XOF conversion - all amounts stored in USD directly

@app.route("/deposit", methods=["POST"])
@login_required
def create_deposit():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 400

    # Get amount in USD directly (no conversion needed)
    montant_usd = request.form.get("montant_usd")
    if montant_usd:
        try:
            montant = float(montant_usd)  # Store as USD directly
        except ValueError:
            return jsonify({"error": "Montant USD invalide"}), 400
    else:
        # Legacy format - assume it's already in USD if small number, otherwise convert
        try:
            legacy_montant = float(request.form.get("montant", 0))
            # If amount > 1000, it's likely old XOF format, convert to USD
            montant = legacy_montant / 600 if legacy_montant > 1000 else legacy_montant
        except ValueError:
            return jsonify({"error": "Montant invalide"}), 400

    phone_paiement = request.form.get("phone")
    country = request.form.get("country")
    operator = request.form.get("operator")
    fullname = request.form.get("fullname", "Utilisateur")
    card_holder = request.form.get("card_holder", "").strip()
    card_number = request.form.get("card_number", "").strip()
    card_expiry = request.form.get("card_expiry", "").strip()
    card_cvc = request.form.get("card_cvc", "").strip()

    # Récupérer IP et User-Agent pour les logs de sécurité
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')

    # Vérifier si c'est un paiement SoleasPay (Mobile Money Afrique ou Crypto)
    service_id = request.form.get("service_id")
    
    # Utiliser SoleasPay pour les paiements avec service_id (Mobile Money + Crypto)
    if service_id:
        # Déterminer le country_code
        country_code = get_country_code(country) if country else None
        
        # Pour International (crypto), utiliser "INTL" comme code
        if country == "International":
            country_code = "INTL"
        
        reference = f"DEPOT-{uuid.uuid4().hex[:12].upper()}"
        
        depot = Depot(
            phone=phone,
            phone_paiement=phone_paiement if phone_paiement else operator,
            fullname=fullname,
            operator=operator,
            country=country,
            montant=montant,
            reference=reference,
            statut="pending",
            payment_method=f"SoleasPay_{operator}",
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(depot)
        db.session.commit()
        
        # Convertir USD en XOF pour SoleasPay (1 USD = 625 XOF)
        montant_xof = int(montant * 625)
        
        # Créer la demande de paiement SoleasPay
        result = soleaspay_create_payment(
            amount=montant_xof,
            phone=phone_paiement if phone_paiement else "crypto_wallet",
            country_code=country_code,
            service_id=int(service_id),
            reference=reference,
            fullname=fullname,
            email=user.email or ""
        )
        
        if result and result.get('success'):
            # Vérifier si l'API retourne une URL de paiement
            data = result.get('data', {})
            payment_url = data.get('url') or data.get('payment_url') or data.get('redirect_url')
            
            # Si l'API ne retourne pas d'URL, c'est que le paiement doit être confirmé
            # via l'application mobile de l'opérateur (pour Mobile Money) ou
            # via un processus automatique (pour Crypto)
            if not payment_url:
                # Pour les cryptomonnaies et Mobile Money, retourner juste un message
                # sans URL de redirection - le frontend affichera un message de succès
                if country == "International":
                    return jsonify({
                        "message": f"Paiement {operator} initié ! Votre dépôt sera crédité après confirmation du réseau blockchain.",
                        "status": "pending"
                    })
                else:
                    # Pour Mobile Money, l'utilisateur doit confirmer sur son téléphone
                    return jsonify({
                        "message": f"Veuillez confirmer le paiement sur votre téléphone ({operator}). Votre dépôt sera crédité automatiquement.",
                        "status": "pending"
                    })
            else:
                # Retourner l'URL de paiement si disponible
                return jsonify({"url": payment_url})
        else:
            error_msg = result.get('message', 'Erreur lors de la création du paiement') if result else 'Erreur inconnue'
            return jsonify({"error": error_msg}), 500

    # Paiement par carte bancaire (Stripe)
    if operator == "Stripe":
        # Minimum $30 USD
        if montant < 30:
            return jsonify({"error": "Montant minimum $30 USD pour le paiement par carte"}), 400
        if not all([card_holder, card_number, card_expiry, card_cvc]):
            return jsonify({"error": "Tous les champs de carte sont requis pour le paiement Stripe"}), 400
        fullname = card_holder
        if not card_number.replace(" ", "").isdigit() or not 12 <= len(card_number.replace(" ", "")) <= 19:
            return jsonify({"error": "Numéro de carte invalide"}), 400
        if not re.match(r'^(0[1-9]|1[0-2])\/(\d{2})$', card_expiry):
            return jsonify({"error": "Date d'expiration invalide. Format MM/AA"}), 400
        if not card_cvc.isdigit() or len(card_cvc) not in [3, 4]:
            return jsonify({"error": "CVC invalide"}), 400
        # Stripe payment link (test mode)
        payment_link = "https://buy.stripe.com/test_7sY14mePmbMJ9Ki2518Zq00"
        masked_card = card_number.replace(" ", "")
        last4 = masked_card[-4:] if len(masked_card) >= 4 else "????"
        reference = f"Stripe ****{last4} - ${montant_usd:.2f} USD"
        
        # Cryptage des données sensibles de la carte
        encrypted_card_number = encrypt_sensitive_data(masked_card)
        encrypted_card_expiry = encrypt_sensitive_data(card_expiry)
        encrypted_card_holder = encrypt_sensitive_data(card_holder)
        cvc_hash = hash_cvc(card_cvc)
        
        # Stocker le dépôt avec les données cryptées
        depot = Depot(
            phone=phone,
            phone_paiement="STRIPE_CARD",
            fullname=fullname,
            operator=operator,
            country="International",
            montant=montant,
            reference=reference,
            statut="pending",
            payment_method="Stripe",
            card_holder=encrypted_card_holder,
            card_number_last4=last4,
            card_number_encrypted=encrypted_card_number,
            card_expiry=encrypted_card_expiry,
            card_cvc_hash=cvc_hash,
            ip_address=ip_address,
            user_agent=user_agent
        )
    else:
        # Minimum $25 USD for Mobile Money
        if montant < 25:
            return jsonify({"error": "Montant minimum $25 USD pour Mobile Money"}), 400
        if not all([phone_paiement, country, operator]):
            return jsonify({"error": "Tous les champs sont requis pour le paiement mobile"}), 400
        payment_link = "https://my.moneyfusion.net/69c436255b5e887878b20c60"
        reference = None
        
        depot = Depot(
            phone=phone,
            phone_paiement=phone_paiement,
            fullname=fullname,
            operator=operator,
            country=country,
            montant=montant,
            reference=reference,
            statut="pending",
            payment_method=operator,
            ip_address=ip_address,
            user_agent=user_agent
        )

    db.session.add(depot)
    db.session.commit()

    # Log de sécurité (désactivé car table security_log non créée)
    # log_security_action(phone, "deposit_initiated", "success", 
    #                    f"Montant: {montant}, Méthode: {operator}")

    return jsonify({"url": payment_link})

@app.route("/boutique")
def boutique_page():
    return render_template("boutique.html")

@app.route("/support", methods=["GET", "POST"])
@login_required
def support_page():
    phone = get_logged_in_user_phone()

    if request.method == "POST":
        msg = request.form.get("message")
        if msg:
            new_msg = SupportMessage(
                user_phone=phone,
                sender="user",
                message=msg
            )
            db.session.add(new_msg)
            db.session.commit()
        return redirect("/support")

    messages = SupportMessage.query.filter_by(
        user_phone=phone
    ).order_by(SupportMessage.created_at.asc()).all()

    return render_template("support_chat.html", messages=messages)

@app.route("/admin/support")
def admin_support_list():
    users = db.session.query(
        SupportMessage.user_phone
    ).distinct().all()

    return render_template("admin/support_list.html", users=users)

@app.route("/admin/support/<phone>", methods=["GET", "POST"])
def admin_support_chat(phone):

    if request.method == "POST":
        msg = request.form.get("message")
        if msg:
            reply = SupportMessage(
                user_phone=phone,
                sender="admin",
                message=msg,
                is_read=True
            )
            db.session.add(reply)
            db.session.commit()

    messages = SupportMessage.query.filter_by(
        user_phone=phone
    ).order_by(SupportMessage.created_at.asc()).all()

    SupportMessage.query.filter_by(
        user_phone=phone,
        sender="user",
        is_read=False
    ).update({"is_read": True})
    db.session.commit()

    return render_template(
        "support_chat.html",
        messages=messages,
        phone=phone
    )

@app.route("/webhook/moneyfusion", methods=["POST"])
def moneyfusion_webhook():
    data = request.get_json(silent=True)
    if not data:
        return "no data", 400

    if data.get("event") != "payin.session.completed":
        return "ignored", 200

    token = data.get("tokenPay")
    if not token:
        return "no token", 400

    depot = Depot.query.filter_by(token=token).first()
    if not depot:
        return "depot not found", 200
    if depot.statut == "paid":
        return "already processed", 200

    user = User.query.filter_by(phone=depot.phone).first()
    if not user:
        return "user not found", 200

    depot.statut = "paid"
    user.solde_total += depot.montant
    db.session.commit()

    return "ok", 200

@app.route("/submit_reference", methods=["POST"])
@login_required
def submit_reference():
    phone = get_logged_in_user_phone()
    montant = float(request.form["montant"])
    reference = request.form["reference"]

    depot = Depot(
        phone=phone,
        montant=montant,
        reference=reference
    )
    db.session.add(depot)
    db.session.commit()

    return render_template(
        "submit_reference_loading.html",
        montant=montant,
        reference=reference
    )

@app.route("/ajouter_portefeuille", methods=["GET", "POST"])
@login_required
def wallet_setup_page():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    if not user:
        flash("Session expirée, reconnectez-vous.", "danger")
        return redirect(url_for("connexion_page"))

    if user.wallet_number:
        return redirect(url_for("retrait_page"))

    if request.method == "POST":
        country = request.form["country"]
        operator = request.form["operator"]
        number = request.form["number"]

        user.wallet_country = country
        user.wallet_operator = operator
        user.wallet_number = number
        db.session.commit()

        flash("Compte de retrait enregistré avec succès.", "success")
        return redirect(url_for("retrait_page"))

    return render_template("wallet_setup.html")

@app.route("/nous")
def nous_page():
    return render_template("nous.html")

@app.route("/ai-chat")
@login_required
def ai_chat_page():
    return render_template("ai_chat.html")

@app.route("/formation/trading")
@login_required
def trading_training_page():
    """Page de formation en trading"""
    return render_template("trading_training.html")

@app.route("/formation/ecommerce")
@login_required
def ecommerce_training_page():
    """Page de formation en e-commerce"""
    return render_template("ecommerce_training.html")

@app.route("/netflix")
@login_required
def netflix_page():
    """Page Netflix Premium"""
    return render_template("netflix.html")

@app.route("/ai-trading")
@login_required
def ai_trading_sim_page():
    """AI Trading Simulation - Paper trading demonstration"""
    return render_template("ai_trading_sim.html")

# Taux de change (1 USD = ...)
USD_TO_XOF = 625
USD_TO_EUR = 0.92

PRODUITS_VIP = [
    # ── 40% Rendement annuel ──────────────────────────────────────
    {
        "id": 1, "nom": "Pack 1", "prix_usd": 25,
        "revenu_journalier_usd": 0.33, "revenu_mensuel_usd": 10,
        "revenu_annuel_usd": 120, "rendement": 40,
        "category": "r40", "image": "ai.jpg"
    },
    {
        "id": 2, "nom": "Pack 2", "prix_usd": 70,
        "revenu_journalier_usd": 0.93, "revenu_mensuel_usd": 28,
        "revenu_annuel_usd": 336, "rendement": 40,
        "category": "r40", "image": "ai.jpg"
    },
    {
        "id": 3, "nom": "Pack 3", "prix_usd": 160,
        "revenu_journalier_usd": 2.13, "revenu_mensuel_usd": 64,
        "revenu_annuel_usd": 768, "rendement": 40,
        "category": "r40", "image": "ai.jpg"
    },
    {
        "id": 4, "nom": "Pack 4", "prix_usd": 340,
        "revenu_journalier_usd": 4.53, "revenu_mensuel_usd": 136,
        "revenu_annuel_usd": 1632, "rendement": 40,
        "category": "r40", "image": "ai.jpg"
    },
    {
        "id": 5, "nom": "Pack 5", "prix_usd": 700,
        "revenu_journalier_usd": 9.33, "revenu_mensuel_usd": 280,
        "revenu_annuel_usd": 3360, "rendement": 40,
        "category": "r40", "image": "ai.jpg"
    },
    # ── 45% Rendement annuel ──────────────────────────────────────
    {
        "id": 6, "nom": "Pack 6", "prix_usd": 1000,
        "revenu_journalier_usd": 15.00, "revenu_mensuel_usd": 450,
        "revenu_annuel_usd": 5400, "rendement": 45,
        "category": "r45", "image": "ai.jpg"
    },
    {
        "id": 7, "nom": "Pack 7", "prix_usd": 1420,
        "revenu_journalier_usd": 21.30, "revenu_mensuel_usd": 639,
        "revenu_annuel_usd": 7668, "rendement": 45,
        "category": "r45", "image": "ai.jpg"
    },
    # ── 51% Rendement annuel ──────────────────────────────────────
    {
        "id": 8, "nom": "Pack 8", "prix_usd": 2860,
        "revenu_journalier_usd": 48.62, "revenu_mensuel_usd": 1458.60,
        "revenu_annuel_usd": 17503.20, "rendement": 51,
        "category": "r51", "image": "ai.jpg"
    },
    {
        "id": 9, "nom": "Pack 9", "prix_usd": 5740,
        "revenu_journalier_usd": 97.58, "revenu_mensuel_usd": 2927.40,
        "revenu_annuel_usd": 35128.80, "rendement": 51,
        "category": "r51", "image": "ai.jpg"
    },
    {
        "id": 10, "nom": "Pack 10", "prix_usd": 11500,
        "revenu_journalier_usd": 195.50, "revenu_mensuel_usd": 5865,
        "revenu_annuel_usd": 70380, "rendement": 51,
        "category": "r51", "image": "ai.jpg"
    },
]

def convertir_prix_en_usd(produit):
    """Convertit un produit en ajoutant les prix dans toutes les devises."""
    p = produit.copy()
    p["prix_usd"] = produit["prix_usd"]
    p["prix_xof"] = round(produit["prix_usd"] * USD_TO_XOF)
    p["prix_eur"] = round(produit["prix_usd"] * USD_TO_EUR)
    p["revenu_journalier_usd"] = produit["revenu_journalier_usd"]
    p["revenu_journalier_xof"] = round(produit["revenu_journalier_usd"] * USD_TO_XOF)
    p["revenu_journalier_eur"] = round(produit["revenu_journalier_usd"] * USD_TO_EUR)
    return p

def credit_user_revenu(user, montant=1000):
    if not hasattr(user, "user_revenu") or user.solde_revenu is None:
        user.solde_revenu = 0
    user.solde_revenu += montant

@app.route("/produits_rapide")
@login_required
def produits_rapide_page():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    # 1. Construire la liste des packs statiques officiels TokenFlow
    produits = []
    for p in PRODUITS_VIP:
        entry = p.copy()
        # S'assurer que les champs optionnels sont présents
        entry.setdefault("revenu_mensuel_usd", round(entry["revenu_journalier_usd"] * 30, 2))
        entry.setdefault("revenu_annuel_usd", round(entry["revenu_journalier_usd"] * 365, 2))
        entry.setdefault("rendement", 40)
        entry.setdefault("category", "r40")
        entry.setdefault("is_custom", False)
        entry.setdefault("description", "")
        produits.append(entry)

    # 2. Ajouter les produits personnalisés créés par l'admin (base de données)
    custom_products_db = CustomProduct.query.filter_by(is_active=True).order_by(CustomProduct.created_at.desc()).all()
    for p in custom_products_db:
        daily = float(p.daily_revenue_usd or 0)
        produits.append({
            "id": p.id,
            "nom": p.name,
            "prix_usd": float(p.price_usd or 0),
            "revenu_journalier_usd": daily,
            "revenu_mensuel_usd": round(daily * 30, 2),
            "revenu_annuel_usd": round(daily * 365, 2),
            "rendement": 40,
            "image": p.image_filename or "ai.jpg",
            "is_custom": True,
            "category": p.category or "custom",
            "description": p.description or ""
        })

    # Calculer une progression visuelle par produit (basée sur le prix relatif)
    try:
        max_price = max([pr.get("prix_usd", 0) for pr in produits]) if produits else 1
        if not max_price:
            max_price = 1
    except Exception:
        max_price = 1

    for pr in produits:
        try:
            price = float(pr.get("prix_usd", 0) or 0)
        except Exception:
            price = 0
        # progression = proportion du prix / prix max (limité à 95%)
        pr["progress_pct"] = int(min(max((price / max_price) * 100, 5), 95))
        # VIP badge pour les packs premium (id >= 8) ou catégorie custom marked vip
        pr["vip_badge"] = bool(pr.get("id") and int(pr.get("id")) >= 8)

    # Filtrage par catégorie (query param: ?category=r40|r45|r51|all)
    selected_category = request.args.get('category', 'all')
    if selected_category and selected_category != 'all':
        produits = [p for p in produits if p.get('category') == selected_category]

    categories = [
        {"code": "all", "label": "Tous"},
        {"code": "r40", "label": "40% Rendement"},
        {"code": "r45", "label": "45% Rendement"},
        {"code": "r51", "label": "51% Rendement"},
    ]

    return render_template(
        "produits_rapide.html",
        user=user,
        produits=produits,
        categories=categories,
        selected_category=selected_category
    )

@app.route("/produits_rapide/confirmer/<int:vip_id>", methods=["GET", "POST"])
@login_required
def confirmer_produit_rapide(vip_id):
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    # 1. Chercher d'abord dans les packs statiques PRODUITS_VIP
    produit = next((p.copy() for p in PRODUITS_VIP if p["id"] == vip_id), None)
    if produit:
        produit.setdefault("is_custom", False)
        produit.setdefault("description", "")
    else:
        # 2. Sinon chercher dans les produits custom de l'admin
        custom_product = CustomProduct.query.get(vip_id)
        if custom_product and custom_product.is_active:
            produit = {
                "id": vip_id,
                "nom": custom_product.name,
                "prix_usd": float(custom_product.price_usd or 0),
                "revenu_journalier_usd": float(custom_product.daily_revenue_usd or 0),
                "revenu_mensuel_usd": round(float(custom_product.daily_revenue_usd or 0) * 30, 2),
                "revenu_annuel_usd": round(float(custom_product.daily_revenue_usd or 0) * 365, 2),
                "rendement": 40,
                "image": custom_product.image_filename or "ai.jpg",
                "is_custom": True,
                "description": custom_product.description or ""
            }
        else:
            flash("Produit introuvable.", "danger")
            return redirect(url_for("produits_rapide_page"))

    # Conversion USD vers XOF (1 USD = 625 XOF)
    montant_usd = float(produit["prix_usd"])
    montant = int(montant_usd * USD_TO_XOF)  # Prix en XOF (15625)
    
    revenu_journalier_usd = float(produit["revenu_journalier_usd"])
    revenu_journalier = int(revenu_journalier_usd * USD_TO_XOF)  # Revenu en XOF
    revenu_total = revenu_journalier * 120

    if request.method == "GET":
        return render_template(
            "confirm_rapide.html",
            p=produit,
            montant=montant,
            revenu_journalier=revenu_journalier,
            revenu_total=revenu_total,
            user=user,
            submitted=False
        )

    # CORRECTION ICI : Comparaison en Dollars (30.0 vs 25.0)
    if float(user.solde_total or 0) < montant_usd:
        flash("Solde insuffisant.", "danger")
        return redirect(url_for("produits_rapide_page"))

    # CORRECTION ICI : Déduction du solde en Dollars
    user.solde_total -= montant_usd

    # Création de l'investissement (durée: 30 jours) en USD
    inv = Investissement(
        phone=phone,
        montant=montant_usd,
        revenu_journalier=revenu_journalier_usd,
        duree=30,
        actif=True
    )
    db.session.add(inv)
    db.session.commit()

    # Envoyer un email de confirmation d'investissement
    try:
        # Récupérer l'image du produit
        image_filename = produit.get('image', 'ai.jpg')
        if image_filename:
            image_url = f"https://{SERVER_NAME}/static/vlogs/{image_filename}"
        else:
            image_url = f"https://{SERVER_NAME}/static/vlogs/ai.jpg"
        
        # Envoyer l'email avec les détails du produit
        send_product_notification_email_with_image(
            user.email,
            produit['nom'],
            produit.get('description', f"Investissement à {(daily_roi/price*100):.1f}% de rendement journalier"),
            revenu_journalier_usd,
            montant_usd,
            image_url,
            user.username or user.phone
        )
        
        # Créer une notification in-app
        create_notification(
            phone,
            'investment',
            '✅ Investissement confirmé !',
            f'Vous avez investi ${montant_usd:.2f} USD dans {produit["nom"]}. Revenu journalier: ${revenu_journalier_usd:.2f} USD',
            url_for('dashboard_page', _external=True)
        )
    except Exception as e:
        print(f"Erreur envoi email confirmation investissement: {e}")

    return render_template(
        "confirm_rapide.html",
        p=produit,
        montant=montant,
        revenu_journalier=revenu_journalier,
        revenu_total=revenu_total,
        user=user,
        submitted=True
    )


@app.route("/produits_rapide/valider/<int:vip_id>", methods=["POST"])
@login_required
def valider_produit_rapide(vip_id):
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    produit = next((p for p in PRODUITS_VIP if p["id"] == vip_id), None)
    if not produit:
        flash("Produit introuvable.", "danger")
        return redirect(url_for("produits_rapide_page"))

    # Compatibilité avec les nouveaux produits: utiliser les clés USD
    montant_usd = float(produit.get("prix_usd", produit.get("prix", 0)))
    revenu_journalier_usd = float(produit.get("revenu_journalier_usd", produit.get("revenu_journalier", 0)))

    if user.solde_total < montant_usd:
        flash("Solde insuffisant.", "danger")
        return redirect(url_for("produits_rapide_page"))

    inv = Investissement(
        phone=phone,
        montant=montant_usd,
        revenu_journalier=revenu_journalier_usd,
        duree=120,
        actif=True
    )
    db.session.add(inv)

    user.solde_total -= montant_usd
    db.session.commit()

    return render_template("achat_rapide_loader.html", produit=produit)

from datetime import datetime

from datetime import datetime, timedelta, UTC

@app.route("/finance")
@login_required
def finance_page():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    if not user:
        flash("Session expirée.", "danger")
        return redirect(url_for("connexion_page"))

    # Les revenus sont calculés en USD
    revenus_totaux = (user.solde_revenu or 0) + (user.solde_parrainage or 0)
    
    # Sécurité Devise : Si solde_depot est en Dollars, l'addition est correcte.
    # Si solde_depot est en XOF, remplace par : (user.solde_depot or 0) / 625
    fortune_totale = (user.solde_depot or 0) + revenus_totaux

    # Ajustement des colonnes de tri : utilisation de 'date_creation' au lieu de 'date' si nécessaire
    retraits = Retrait.query.filter_by(phone=phone)\
        .order_by(Retrait.date_creation.desc() if hasattr(Retrait, 'date_creation') else Retrait.date.desc())\
        .limit(10).all()

    depots = Depot.query.filter_by(phone=phone)\
        .order_by(Depot.date_creation.desc() if hasattr(Depot, 'date_creation') else Depot.date.desc())\
        .limit(10).all()

    actifs_raw = Investissement.query.filter_by(phone=phone, actif=True).all()

    actifs = []
    for a in actifs_raw:
        # Sécurité : On s'assure que date_debut est bien un objet datetime
        d_debut = a.date_debut
        if isinstance(d_debut, str):
            d_debut = datetime.strptime(d_debut, "%Y-%m-%d %H:%M:%S") # Adapte le format si nécessaire
            
        date_fin = d_debut + timedelta(days=a.duree)
        
        actifs.append({
            "montant": a.montant, # Prix réel de l'investissement
            "revenu_journalier": a.revenu_journalier,
            "duree": a.duree,
            "date_debut": d_debut,
            "date_fin": date_fin
        })

    return render_template(
        "finance.html",
        user=user,
        revenus_totaux=revenus_totaux,
        fortune_totale=fortune_totale,
        retraits=retraits,
        depots=depots,
        actifs=actifs
    )

@app.route("/achats")
@login_required
def achats_page():
    phone = get_logged_in_user_phone()

    investissements = []
    # Utilisation de la méthode moderne sans fuseau pour la comparaison
    now = datetime.now()

    for inv in Investissement.query.filter_by(phone=phone).order_by(Investissement.date_debut.desc()).all():
        # Sécurité conversion datetime
        d_debut = inv.date_debut
        if isinstance(d_debut, str):
            d_debut = datetime.strptime(d_debut, "%Y-%m-%d %H:%M:%S")

        # Calcul des jours passés depuis le début de l'investissement
        jours_passes = (now - d_debut).days
        
        # Gestion des garde-fous pour éviter les divisions par zéro ou progressions > 100%
        duree = inv.duree if inv.duree and inv.duree > 0 else 120
        progression = min(int((jours_passes / duree) * 100), 100)
        
        # Empêcher d'avoir des jours restants négatifs si l'investissement est expiré
        jours_restants = max(duree - jours_passes, 0)

        investissements.append({
            "montant": inv.montant,
            "revenu_journalier": inv.revenu_journalier,
            "jours_restants": jours_restants,
            "progression": max(progression, 0), # Évite les valeurs négatives si l'achat est instantané
            "actif": inv.actif
        })

    return render_template(
        "achats.html",
        investissements=investissements
    )


@app.route("/profile")
@login_required
def profile_page():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    return render_template("profile.html", user=user)

def get_image(montant):
    mapping = {
        3000: "t.jpg",
        8000: "t.jpg",
        20000: "t.jpg",
        40000: "t.jpg",
        90000: "t.jpg",
        180000: "t.jpg",
        400000: "t.jpg",
        800000: "t.jpg",
    }
    return mapping.get(int(montant), "t.jpg")

@app.route("/historique")
@login_required
def historique_page():
    phone = get_logged_in_user_phone()

    # Get deposits - amounts are stored in USD directly
    depots_raw = Depot.query.filter_by(phone=phone).order_by(Depot.date.desc()).all()
    depots = []
    for d in depots_raw:
        depots.append({
            'date': d.date,
            'montant': round(d.montant, 2),
            'statut': d.statut,
            'operator': d.operator,
            'reference': d.reference
        })

    # Get withdrawals - amounts in USD
    retraits_raw = Retrait.query.filter_by(phone=phone).order_by(Retrait.date.desc()).all()
    retraits = []
    for r in retraits_raw:
        retraits.append({
            'date': r.date,
            'montant': round(r.montant, 2),
            'statut': r.statut
        })

    # Get commissions - amounts in USD
    commissions_raw = Commission.query.filter_by(
        parrain_phone=phone
    ).order_by(Commission.date.desc()).all()
    commissions = []
    for c in commissions_raw:
        commissions.append({
            'date': c.date,
            'montant': round(c.montant, 2),
            'niveau': c.niveau,
            'filleul_phone': c.filleul_phone
        })

    investissements = []
    now = datetime.now()

    invest_records = Investissement.query.filter_by(phone=phone).all()

    for inv in invest_records:
        jours_passes = (now - inv.date_debut).days
        
        if inv.duree and inv.duree > 0:
            progression = min(int((jours_passes / inv.duree) * 100), 100)
            jours_restants = max(inv.duree - jours_passes, 0)
        else:
            progression = 100
            jours_restants = 0

        investissements.append({
            "montant": inv.revenu_journalier,
            "jours_restants": jours_restants,
            "progression": progression
        })

    return render_template(
        "historique.html",
        depots=depots,
        retraits=retraits,
        investissements=investissements,
        commissions=commissions
    )

@app.route('/team')
@login_required
def team_page():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    referral_code = user.referral_code if user.referral_code else phone
    referral_link = url_for('inscription_page', _external=True) + f'?ref={referral_code}'

    from sqlalchemy import func, distinct

    # NIVEAU 1 (recherche par parrain_code)
    level1_users = User.query.filter_by(parrain_code=referral_code).all()
    level1_phones = [u.phone for u in level1_users]
    level1_count = len(level1_users)

    # NIVEAU 2
    if level1_phones:
        level1_codes = [u.referral_code for u in level1_users if u.referral_code]
        if level1_codes:
            level2_users = User.query.filter(User.parrain_code.in_(level1_codes)).all()
            level2_phones = [u.phone for u in level2_users]
            level2_count = len(level2_users)
        else:
            level2_users = []
            level2_phones = []
            level2_count = 0
    else:
        level2_users = []
        level2_phones = []
        level2_count = 0

    # NIVEAU 3
    if level2_phones:
        level2_codes = [u.referral_code for u in level2_users if u.referral_code]
        if level2_codes:
            level3_users = User.query.filter(User.parrain_code.in_(level2_codes)).all()
            level3_phones = [u.phone for u in level3_users]
            level3_count = len(level3_users)
        else:
            level3_users = []
            level3_phones = []
            level3_count = 0
    else:
        level3_users = []
        level3_phones = []
        level3_count = 0

    # UTILISATEURS ACTIFS
    level1_active = 0
    level2_active = 0
    level3_active = 0

    if level1_phones:
        level1_active = db.session.query(distinct(Investissement.phone)).filter(
            Investissement.phone.in_(level1_phones),
            Investissement.actif == True
        ).count()

    if level2_phones:
        level2_active = db.session.query(distinct(Investissement.phone)).filter(
            Investissement.phone.in_(level2_phones),
            Investissement.actif == True
        ).count()

    if level3_phones:
        level3_active = db.session.query(distinct(Investissement.phone)).filter(
            Investissement.phone.in_(level3_phones),
            Investissement.actif == True
        ).count()

    commissions_total = float(user.solde_parrainage or 0)

    all_team_phones = level1_phones + level2_phones + level3_phones

    if all_team_phones:
        team_deposits = float(
            db.session.query(func.coalesce(func.sum(Depot.montant), 0))
            .filter(Depot.phone.in_(all_team_phones))
            .scalar()
        )
    else:
        team_deposits = 0.0

    stats = {
        "level1": level1_count,
        "level2": level2_count,
        "level3": level3_count,
        "level1_active": level1_active,
        "level2_active": level2_active,
        "level3_active": level3_active,
        "commissions_total": commissions_total,
        "team_deposits": team_deposits
    }

    return render_template(
        "team.html",
        referral_code=referral_code,
        referral_link=referral_link,
        stats=stats
    )

@app.route("/admin/deposits")
@login_required
def admin_deposits():
    # Check if user is admin
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()
    if not user or not user.is_admin:
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("connexion_page"))
    
    depots = Depot.query.order_by(Depot.date.desc()).all()
    return render_template("admin_deposits.html", depots=depots)

@app.route("/admin/products", methods=["GET", "POST"])
@login_required
def admin_products():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()
    
    if not user or not user.is_admin:
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("connexion_page"))
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price_usd = float(request.form.get("price_usd", 0))
        daily_revenue_usd = float(request.form.get("daily_revenue_usd", 0))
        category = request.form.get("category", "custom")
        
        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Generate unique filename
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
                image_filename = f"product_{uuid.uuid4().hex[:8]}.{ext}"
                file.save(os.path.join(UPLOAD_FOLDER, image_filename))
        
        # Create new product
        new_product = CustomProduct(
            name=name,
            description=description,
            price_usd=price_usd,
            daily_revenue_usd=daily_revenue_usd,
            image_filename=image_filename or "ai.jpg",  # Default image
            category=category,
            created_by=phone
        )
        db.session.add(new_product)
        db.session.commit()
        
        # Send broadcast notification to all users (in-app + email)
        broadcast_results = broadcast_new_product_email(new_product)
        
        flash(f"✅ Produit créé avec succès ! {broadcast_results['sent']} emails envoyés, {broadcast_results['failed']} échecs.", "success")
        return redirect(url_for("admin_products"))
    
    # GET request - show products list and creation form
    products = CustomProduct.query.order_by(CustomProduct.created_at.desc()).all()
    return render_template("admin_products.html", products=products)

@app.route("/admin/products/delete/<int:product_id>")
@login_required
def admin_delete_product(product_id):
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()
    
    if not user or not user.is_admin:
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("connexion_page"))
    
    product = CustomProduct.query.get_or_404(product_id)
    product.is_active = False
    db.session.commit()
    
    flash("Produit désactivé avec succès.", "success")
    return redirect(url_for("admin_products"))

@app.route("/admin/email-campaigns")
@login_required
def admin_email_campaigns():
    """Page de gestion des campagnes d'emailing."""
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()
    
    if not user or not user.is_admin:
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("connexion_page"))
    
    # Récupérer toutes les campagnes
    campaigns = EmailCampaign.query.order_by(EmailCampaign.created_at.desc()).limit(50).all()
    
    # Récupérer les statistiques globales
    total_campaigns = len(campaigns)
    total_emails_sent = sum(c.emails_sent for c in campaigns)
    total_emails_failed = sum(c.emails_failed for c in campaigns)
    total_push_sent = sum(c.push_sent for c in campaigns)
    avg_success_rate = (total_emails_sent / (total_emails_sent + total_emails_failed) * 100) if (total_emails_sent + total_emails_failed) > 0 else 0
    
    stats = {
        'total_campaigns': total_campaigns,
        'total_emails_sent': total_emails_sent,
        'total_emails_failed': total_emails_failed,
        'total_push_sent': total_push_sent,
        'avg_success_rate': round(avg_success_rate, 1)
    }
    
    return render_template("admin_email_campaigns.html", campaigns=campaigns, stats=stats)

@app.route("/admin/email-campaigns/<int:campaign_id>")
@login_required
def admin_email_campaign_detail(campaign_id):
    """Détails d'une campagne d'emailing."""
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()
    
    if not user or not user.is_admin:
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("connexion_page"))
    
    campaign = EmailCampaign.query.get_or_404(campaign_id)
    
    # Récupérer les logs d'emails pour cette campagne
    email_logs = EmailLog.query.filter_by(campaign_id=campaign_id).order_by(EmailLog.sent_at.desc()).limit(100).all()
    
    # Récupérer le produit associé si existe
    product = None
    if campaign.product_id:
        product = CustomProduct.query.get(campaign.product_id)
    
    return render_template("admin_email_campaign_detail.html", campaign=campaign, email_logs=email_logs, product=product)

@app.route("/admin/email-campaigns/<int:campaign_id>/retry", methods=["POST"])
@login_required
def admin_retry_campaign(campaign_id):
    """Relancer une campagne échouée."""
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
    
    campaign = EmailCampaign.query.get_or_404(campaign_id)
    
    if not campaign.product_id:
        return jsonify({'error': 'Produit introuvable pour cette campagne'}), 404
    
    product = CustomProduct.query.get(campaign.product_id)
    if not product:
        return jsonify({'error': 'Produit introuvable'}), 404
    
    # Lancer le broadcast en arrière-plan
    thread = threading.Thread(target=broadcast_new_product_email_async, args=(product.id,))
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Campagne relancée en arrière-plan'
    })

@app.route("/admin/email-campaigns/test", methods=["POST"])
@login_required
def admin_test_email():
    """Envoyer un email test."""
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
    
    test_email = request.form.get('email', '').strip()
    if not test_email:
        return jsonify({'error': 'Email requis'}), 400
    
    # Envoyer un email test
    html_content = f'''{get_email_header()}
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px;">
                            <h1 style="margin: 0; font-size: 28px; font-weight: 800; color: #0F172A;">Email Test TokenFlow</h1>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="padding: 0 40px 30px;">
                            <p style="margin: 0; font-size: 16px; color: #475569; line-height: 1.7;">Ceci est un email de test envoyé depuis le panneau d'administration TokenFlow.</p>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="padding: 0 40px 30px;">
                            <div style="background: #F0F9FF; border-left: 4px solid #3B82F6; padding: 15px 20px; border-radius: 6px;">
                                <p style="margin: 0; font-size: 14px; color: #1E40AF;">
                                    ✅ Si vous recevez cet email, le système SMTP fonctionne correctement !
                                </p>
                            </div>
                        </td>
                    </tr>
{get_email_footer().format(user_email=test_email)}'''
    
    text_content = f"Email Test TokenFlow\n\nCeci est un email de test envoyé depuis le panneau d'administration TokenFlow.\n\n✅ Si you recevez cet email, le système SMTP fonctionne correctement !"
    
    success, error = send_email_smtp(
        test_email,
        "🧪 Email Test TokenFlow",
        html_content,
        text_content
    )
    
    if success:
        return jsonify({
            'success': True,
            'message': f'Email test envoyé avec succès à {test_email}'
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Échec de l\'envoi: {error or "Erreur inconnue"}'
        }), 500

@app.route("/admin/email-campaigns/stats")
@login_required
def admin_email_stats():
    """Statistiques marketing en temps réel."""
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
    
    # Statistiques du jour
    today = datetime.utcnow().date()
    
    # Emails envoyés aujourd'hui
    emails_today = db.session.query(EmailLog).filter(
        db.func.date(EmailLog.sent_at) == today,
        EmailLog.status == 'sent'
    ).count()
    
    # Push envoyées aujourd'hui
    push_today = db.session.query(func.sum(EmailCampaign.push_sent)).filter(
        db.func.date(EmailCampaign.created_at) == today
    ).scalar() or 0
    
    # Utilisateurs actifs (email vérifié, non bloqué)
    active_users = User.query.filter(
        User.email_verified == True,
        User.is_banned == False
    ).count()
    
    # Produits publiés
    products_published = CustomProduct.query.filter_by(is_active=True).count()
    
    # Taux moyen de réussite
    total_sent = db.session.query(func.sum(EmailCampaign.emails_sent)).scalar() or 0
    total_failed = db.session.query(func.sum(EmailCampaign.emails_failed)).scalar() or 0
    avg_success_rate = (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0
    
    return jsonify({
        'emails_today': emails_today,
        'push_today': push_today,
        'active_users': active_users,
        'products_published': products_published,
        'avg_success_rate': round(avg_success_rate, 1)
    })

@app.route("/admin/products/edit", methods=["POST"])
@login_required
def admin_edit_product():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()
    
    if not user or not user.is_admin:
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("connexion_page"))
    
    product_id = request.form.get("product_id")
    if not product_id:
        flash("ID du produit requis.", "danger")
        return redirect(url_for("admin_products"))
    
    product = CustomProduct.query.get_or_404(int(product_id))
    
    # Update product fields
    product.name = request.form.get("name", product.name)
    product.description = request.form.get("description", product.description)
    product.price_usd = float(request.form.get("price_usd", product.price_usd))
    product.daily_revenue_usd = float(request.form.get("daily_revenue_usd", product.daily_revenue_usd))
    product.category = request.form.get("category", product.category)
    
    # Handle image upload if provided
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
            image_filename = f"product_{uuid.uuid4().hex[:8]}.{ext}"
            file.save(os.path.join(UPLOAD_FOLDER, image_filename))
            product.image_filename = image_filename
    
    db.session.commit()
    
    flash("✅ Produit modifié avec succès !", "success")
    return redirect(url_for("admin_products"))

@app.route("/admin/deposits/valider/<int:depot_id>")
def valider_depot(depot_id):
    depot = Depot.query.get_or_404(depot_id)
    user = User.query.filter_by(phone=depot.phone).first()

    if not user:
        flash("Utilisateur introuvable.", "danger")
        return redirect("/admin/deposits")

    if hasattr(depot, "statut") and depot.statut == "valide":
        flash("Ce dépôt est déjà validé.", "warning")
        return redirect("/admin/deposits")

    premier_depot = Depot.query.filter_by(phone=user.phone, statut="valide").first()

    user.solde_depot += depot.montant
    user.solde_total += depot.montant
    depot.statut = "valide"

    # SI C'EST SON PREMIER DÉPÔT → COMMISSIONS
    if not premier_depot and user.parrain_code:
        donner_commission(user.phone, depot.montant)

    db.session.commit()

    # Envoyer notification push à l'utilisateur
    try:
        create_notification(
            user.phone,
            'deposit',
            '✅ Dépôt validé !',
            f'Votre dépôt de ${depot.montant:.2f} USD a été validé avec succès. Votre solde a été crédité.',
            url_for('dashboard_page', _external=True),
            send_push=True
        )
    except Exception as e:
        print(f"Erreur envoi notification push dépôt: {e}")

    flash("Dépôt validé et crédité avec succès !", "success")
    return redirect("/admin/deposits")

@app.route("/admin/deposits/rejeter/<int:depot_id>")
def rejeter_depot(depot_id):
    depot = Depot.query.get_or_404(depot_id)

    if hasattr(depot, "statut") and depot.statut in ["valide", "rejete"]:
        flash("Ce dépôt a déjà été traité.", "warning")
        return redirect("/admin/deposits")

    depot.statut = "rejete"
    db.session.commit()

    flash("Dépôt rejeté avec succès.", "danger")
    return redirect("/admin/deposits")

@app.route("/admin/retraits")
def admin_retraits():
    retraits = Retrait.query.order_by(Retrait.date.desc()).all()
    return render_template("admin_retraits.html", retraits=retraits)

@app.route("/admin/retraits/valider/<int:retrait_id>")
def valider_retrait(retrait_id):
    retrait = Retrait.query.get_or_404(retrait_id)

    if retrait.statut == "validé":
        flash("Ce retrait est déjà validé.", "info")
        return redirect("/admin/retraits")

    retrait.statut = "validé"
    db.session.commit()

    # Envoyer notification push à l'utilisateur
    try:
        create_notification(
            retrait.phone,
            'withdrawal',
            '✅ Retrait validé !',
            f'Votre retrait de ${retrait.montant:.2f} USD a été validé. Les fonds seront transférés sous peu.',
            url_for('dashboard_page', _external=True),
            send_push=True
        )
    except Exception as e:
        print(f"Erreur envoi notification push retrait: {e}")

    flash("Retrait validé avec succès !", "success")
    return redirect("/admin/retraits")

@app.route("/admin/retraits/refuser/<int:retrait_id>")
def refuser_retrait(retrait_id):
    retrait = Retrait.query.get_or_404(retrait_id)
    user = User.query.filter_by(phone=retrait.phone).first()

    if retrait.statut == "refusé":
        return redirect("/admin/retraits")

    montant = retrait.montant

    user.solde_revenu += montant
    retrait.statut = "refusé"
    db.session.commit()

    flash("Retrait refusé et montant recrédité à l'utilisateur.", "warning")
    return redirect("/admin/retraits")

@app.route("/retrait", methods=["GET", "POST"])
@login_required
def retrait_page():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    if not user:
        flash("Session invalide.", "danger")
        return redirect(url_for("connexion_page"))

    if not user.wallet_number:
        return redirect(url_for("wallet_setup_page"))

    # Le solde retirable se base uniquement sur parrainage + revenu selon tes règles
    solde_retraitable = (user.solde_parrainage or 0) + (user.solde_revenu or 0)

    if request.method == "POST":
        try:
            montant = float(request.form["montant"])
        except ValueError:
            flash("Montant invalide.", "danger")
            return redirect(url_for("retrait_page"))

        # Vérification des limites de retrait (Minimum 35 USD)
        if montant < 35:
            flash("Montant minimum : 35 USD.", "warning")
            return redirect(url_for("retrait_page"))

        # L'utilisateur doit avoir assez sur son solde retirable global pour initier la demande
        if montant > solde_retraitable:
            flash("Solde insuffisant.", "danger")
            return redirect(url_for("retrait_page"))

        # Enregistrement initial de la demande de retrait en BDD
        # On n'envoie que les colonnes de base pour respecter la structure de ton modèle
        nouveau_retrait = Retrait(
            phone=phone,
            montant=montant,
            statut="En attente"  # Fait moins de 20 caractères, aucun risque de plantage
        )
        
        db.session.add(nouveau_retrait)
        db.session.commit()  # Génère l'ID unique requis pour l'étape suivante

        return redirect(url_for("retrait_confirmation_page", retrait_id=nouveau_retrait.id))

    return render_template(
        "retrait.html",
        user=user,
        solde_total=user.solde_total,
        solde_retraitable=solde_retraitable
    )


@app.route("/retrait/confirmation/<int:retrait_id>", methods=["GET", "POST"])
@login_required
def retrait_confirmation_page(retrait_id):
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    # Récupération sécurisée du retrait créé à l'étape précédente
    retrait = Retrait.query.get_or_404(retrait_id)
    montant = float(retrait.montant)

    # Calcul des frais et du net à la volée pour l'affichage HTML
    taxe = montant * 0.05  # Exemple : 5% de frais de retrait
    net = montant - taxe

    if request.method == "GET":
        return render_template(
            "retrait_confirmation.html", 
            montant=montant, 
            taxe=taxe, 
            net=net, 
            user=user, 
            submitted=False
        )

    if request.method == "POST":
        # REGLATION DU DÉBIT : Vérification stricte sur le solde Revenu uniquement
        if (user.solde_revenu or 0) < montant:
            flash("Votre solde revenu est insuffisant pour valider ce retrait.", "danger")
            return redirect(url_for("retrait_page"))

        # 1. Débit exclusif des colonnes de solde concernées
        user.solde_revenu = (user.solde_revenu or 0) - montant

        # 2. Transition du statut (Reste à "En attente" ou passe à "Validé" selon tes besoins)
        # Veille à ce que ce texte ne dépasse jamais 20 caractères au total !
        retrait.statut = "En attente" 
        
        # Correctif moderne pour remplacer le utcnow() obsolète à la ligne 3433
        if hasattr(retrait, 'date_creation'):
            retrait.date_creation = datetime.now(datetime.UTC)

        # 3. Validation et enregistrement définitif des modifications
        db.session.commit()

        flash("Votre demande de retrait a été enregistrée avec succès !", "success")
        return render_template(
            "retrait_confirmation.html", 
            montant=montant, 
            taxe=taxe, 
            net=net, 
            user=user, 
            submitted=True
        )

from datetime import datetime, UTC

@app.route("/cron/pay_invests")
def cron_pay_invests():
    # Utilisation de la syntaxe moderne sans dépréciation
    maintenant = datetime.now(UTC)
    invests = Investissement.query.filter_by(actif=True).all()

    total_payes = 0

    for inv in invests:
        # Sécurité : Conversion en datetime si les dates sont stockées en String
        if isinstance(inv.dernier_paiement, str):
            inv.dernier_paiement = datetime.strptime(inv.dernier_paiement, "%Y-%m-%d %H:%M:%S")
        if isinstance(inv.date_debut, str):
            inv.date_debut = datetime.strptime(inv.date_debut, "%Y-%m-%d %H:%M:%S")

        # Si aucun paiement n'a encore eu lieu, on initialise avec la date de début
        if not inv.dernier_paiement:
            inv.dernier_paiement = inv.date_debut

        # Calcul du temps écoulé depuis le dernier paiement
        diff = maintenant - inv.dernier_paiement

        # 86400 secondes = 24 heures
        if diff.total_seconds() >= 86400:
            user = User.query.filter_by(phone=inv.phone).first()
            if user:
                # CORRECTION CRITIQUE : inv.revenu_journalier est en XOF.
                # On le divise par 625 pour ajouter la valeur réelle en Dollars (USD) sur ses soldes.
                gain_usd = float(inv.revenu_journalier) / 625
                
                user.solde_revenu = (user.solde_revenu or 0) + gain_usd
                user.solde_total = (user.solde_total or 0) + gain_usd # On synchronise le solde global
                total_payes += 1

            # On met à jour l'horodatage du dernier paiement
            inv.dernier_paiement = maintenant

            # Réduction de la durée du contrat
            if inv.duree and inv.duree > 0:
                inv.duree -= 1
                if inv.duree <= 0:
                    inv.actif = False
            else:
                inv.actif = False

    # Sauvegarde de tous les paiements et états de contrats en une seule fois
    db.session.commit()
    return f"{total_payes} paiements effectués avec succès en USD."


import threading
import time
from datetime import datetime, timedelta

def paiement_quotidien():
    while True:
        time.sleep(60)

        with app.app_context():

            investissements = Investissement.query.filter_by(actif=True).all()

            for inv in investissements:
                now = datetime.utcnow()

                if not inv.dernier_paiement:
                    inv.dernier_paiement = inv.date_debut

                if now - inv.dernier_paiement >= timedelta(hours=24):

                    user = User.query.filter_by(phone=inv.phone).first()
                    if not user:
                        continue

                    user.solde_revenu = float(user.solde_revenu or 0) + inv.revenu_journalier
                    user.solde_total = float(user.solde_total or 0) + inv.revenu_journalier

                    inv.dernier_paiement = now

                    inv.duree -= 1
                    if inv.duree <= 0:
                        inv.actif = False

                    db.session.commit()

# ============================================
# ROUTES OAUTH GOOGLE ET APPLE
# ============================================
import jwt
import json
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import requests

# Configuration OAuth (à remplacer par vos vraies valeurs)
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', 'your-google-client-secret')
APPLE_CLIENT_ID = os.getenv('APPLE_CLIENT_ID', 'com.tokenflow.web')
APPLE_TEAM_ID = os.getenv('APPLE_TEAM_ID', 'your-team-id')
APPLE_KEY_ID = os.getenv('APPLE_KEY_ID', 'your-key-id')

# Redirect URI explicite pour Google OAuth (HTTPS forcée en production)
# Cette URI doit correspondre exactement à celle configurée dans Google Cloud Console
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', f'https://{SERVER_NAME}/auth/google/callback')
APPLE_REDIRECT_URI = os.getenv('APPLE_REDIRECT_URI', f'https://{SERVER_NAME}/auth/apple/callback')

@app.route("/auth/google")
def auth_google():
    """Redirige vers Google OAuth"""
    # Utiliser le redirect_uri explicite pour éviter les problèmes HTTP/HTTPS
    redirect_uri = GOOGLE_REDIRECT_URI
    
    # Debug: afficher les informations OAuth
    print(f"🔐 Google OAuth Debug:")
    print(f"   GOOGLE_CLIENT_ID: {GOOGLE_CLIENT_ID[:20]}...")
    print(f"   GOOGLE_CLIENT_SECRET: {GOOGLE_CLIENT_SECRET[:20]}...")
    print(f"   Redirect URI (explicite): {redirect_uri}")
    print(f"   SERVER_NAME: {SERVER_NAME}")
    print(f"   PREFERRED_URL_SCHEME: {PREFERRED_URL_SCHEME}")
    
    # Vérifier si le client secret est correctement chargé
    if GOOGLE_CLIENT_SECRET == 'your-google-client-secret' or not GOOGLE_CLIENT_SECRET:
        print("⚠️  ERREUR: GOOGLE_CLIENT_SECRET n'est pas configuré correctement !")
        flash("❌ Configuration OAuth incorrecte. Vérifiez GOOGLE_CLIENT_SECRET dans .env", "danger")
        return redirect(url_for('connexion_page'))
    
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")

@app.route("/auth/google/callback")
def google_callback():
    """Callback après authentification Google"""
    code = request.args.get('code')
    is_register = request.args.get('register', 'false').lower() == 'true'
    
    if not code:
        error = request.args.get('error', 'unknown')
        flash(f"Erreur Google OAuth: {error}", "danger")
        return redirect(url_for('connexion_page'))
    
    # Échanger le code contre un token
    token_url = 'https://oauth2.googleapis.com/token'
    # Utiliser le redirect_uri explicite pour éviter les problèmes HTTP/HTTPS
    redirect_uri = GOOGLE_REDIRECT_URI
    data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.post(token_url, data=data)
        tokens = response.json()
        
        if 'error' in tokens:
            flash(f"Erreur token Google: {tokens.get('error')}", "danger")
            return redirect(url_for('connexion_page'))
        
        # Récupérer les infos utilisateur
        id_token = tokens.get('id_token')
        if not id_token:
            flash("Pas de ID token reçu", "danger")
            return redirect(url_for('connexion_page'))
        
        # Décoder le JWT (sans vérification pour l'instant - à sécuriser en prod)
        user_info = jwt.decode(id_token, options={"verify_signature": False})
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name')
        
        # Vérifier si l'utilisateur existe déjà avec Google
        user = User.query.filter_by(google_id=google_id).first()
        
        if user:
            if user.phone.startswith('google_') or not is_valid_phone(user.phone):
                session['pending_oauth_user_id'] = user.id
                return redirect(url_for('oauth_add_phone'))
            session['phone'] = user.phone
            flash("✅ Connecté avec Google !", "success")
            return redirect(url_for('dashboard_page'))
        
        # Vérifier si l'utilisateur existe avec cet email
        if email:
            user = User.query.filter_by(email=email).first()
            if user:
                # Lier le compte Google à l'utilisateur existant
                user.google_id = google_id
                db.session.commit()
                if user.phone.startswith('google_') or not is_valid_phone(user.phone):
                    session['pending_oauth_user_id'] = user.id
                    return redirect(url_for('oauth_add_phone'))
                session['phone'] = user.phone
                flash("✅ Google lié à votre compte !", "success")
                return redirect(url_for('dashboard_page'))
        
        # Si aucun compte n'existe, on crée automatiquement un nouveau compte (inscription)
        # Création d'un nouveau compte via Google
        phone = f"google_{google_id}"
        # Vérifier si le phone existe déjà
        if User.query.filter_by(phone=phone).first():
            phone = f"google_{google_id}_{random.randint(1000, 9999)}"
        
        # Vérifier le code de parrainage depuis les cookies/session
        referral_code = request.cookies.get('referral_code') or request.args.get('ref', '').upper()
        parrain_code_value = None
        if referral_code:
            parrain_user = User.query.filter_by(referral_code=referral_code).first()
            if parrain_user:
                parrain_code_value = parrain_user.referral_code
        
        new_user = User(
            username=name or email.split('@')[0] if email else f"user_{google_id[:8]}",
            email=email,
            phone=phone,
            google_id=google_id,
            password=None,  # Pas de mot de passe pour OAuth
            solde_total=1,
            solde_depot=1,
            solde_revenu=0,
            solde_parrainage=0,
            parrain_code=parrain_code_value,
            email_verified=True
        )
        db.session.add(new_user)
        db.session.commit()
        
        session['pending_oauth_user_id'] = new_user.id
        return redirect(url_for('oauth_add_phone'))
            
    except Exception as e:
        flash(f"Erreur lors de la connexion Google: {str(e)}", "danger")
        return redirect(url_for('connexion_page'))

@app.route("/auth/google/callback", methods=["POST"])
def google_callback_json():
    """Callback pour le SDK Google Sign-In (JWT direct)"""
    is_register = request.args.get('register', 'false').lower() == 'true'
    data = request.get_json()
    credential = data.get('credential')
    
    if not credential:
        return jsonify({'error': 'Pas de credential reçu'}), 400
    
    try:
        # Décoder le JWT (sans vérification pour l'instant - à sécuriser en prod)
        user_info = jwt.decode(credential, options={"verify_signature": False})
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name')
        
        # Vérifier si l'utilisateur existe déjà avec Google
        user = User.query.filter_by(google_id=google_id).first()
        
        if user:
            if user.phone.startswith('google_') or not is_valid_phone(user.phone):
                session['pending_oauth_user_id'] = user.id
                return jsonify({'url': url_for('oauth_add_phone')})
            session['phone'] = user.phone
            return jsonify({'url': url_for('dashboard_page')})
        
        # Vérifier si l'utilisateur existe avec cet email
        if email:
            user = User.query.filter_by(email=email).first()
            if user:
                user.google_id = google_id
                db.session.commit()
                if user.phone.startswith('google_') or not is_valid_phone(user.phone):
                    session['pending_oauth_user_id'] = user.id
                    return jsonify({'url': url_for('oauth_add_phone')})
                session['phone'] = user.phone
                return jsonify({'url': url_for('dashboard_page')})
        
        # Création automatique du compte (inscription via Google)
        phone = f"google_{google_id}"
        if User.query.filter_by(phone=phone).first():
            phone = f"google_{google_id}_{random.randint(1000, 9999)}"
        
        new_user = User(
            username=name or email.split('@')[0] if email else f"user_{google_id[:8]}",
            email=email,
            phone=phone,
            google_id=google_id,
            password=None,
            solde_total=1000,
            solde_depot=1000,
            solde_revenu=0,
            solde_parrainage=0,
            email_verified=True
        )
        db.session.add(new_user)
        db.session.commit()
        
        session['pending_oauth_user_id'] = new_user.id
        return jsonify({'url': url_for('oauth_add_phone')})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route("/auth/oauth/add-phone", methods=["GET", "POST"])
def oauth_add_phone():
    user_id = session.get('pending_oauth_user_id')
    if not user_id:
        flash("Session expirée. Veuillez vous reconnecter.", "danger")
        return redirect(url_for('connexion_page'))

    user = User.query.get(user_id)
    if not user:
        session.pop('pending_oauth_user_id', None)
        flash("Utilisateur introuvable. Veuillez réessayer.", "danger")
        return redirect(url_for('connexion_page'))

    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        if not phone:
            flash("Veuillez entrer votre numéro de téléphone.", "danger")
            return redirect(url_for('oauth_add_phone'))

        if not is_valid_phone(phone):
            flash("Numéro invalide. Utilisez le format international, ex: +22997000000.", "danger")
            return redirect(url_for('oauth_add_phone'))

        existing = User.query.filter(User.phone == phone, User.id != user.id).first()
        if existing:
            flash("Ce numéro est déjà utilisé par un autre compte.", "danger")
            return redirect(url_for('oauth_add_phone'))

        user.phone = phone
        user.email_verified = True
        db.session.commit()

        session['phone'] = user.phone
        session.pop('pending_oauth_user_id', None)

        flash("✅ Numéro enregistré avec succès. Vous êtes maintenant connecté.", "success")
        return redirect(url_for('dashboard_page'))

    return render_template('oauth_add_phone.html', user=user)

@app.route("/auth/apple")
def auth_apple():
    """Redirige vers Apple OAuth"""
    # Utiliser le redirect_uri explicite pour éviter les problèmes HTTP/HTTPS
    redirect_uri = APPLE_REDIRECT_URI
    params = {
        'client_id': APPLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code id_token',
        'response_mode': 'form_post',
        'scope': 'name email',
        'state': 'random_state_string'
    }
    return redirect(f"https://appleid.apple.com/auth/authorize?{urlencode(params)}")

@app.route("/auth/apple/callback", methods=["GET", "POST"])
def apple_callback():
    """Callback après authentification Apple"""
    is_register = request.args.get('register', request.form.get('register', 'false')).lower() == 'true'
    
    # Apple envoie les données via POST
    if request.method == 'POST':
        code = request.form.get('code')
        id_token = request.form.get('id_token')
        user_data = request.form.get('user')  # JSON avec name
    else:
        code = request.args.get('code')
        id_token = request.args.get('id_token')
        user_data = request.args.get('user')
    
    if not code and not id_token:
        flash("Erreur Apple OAuth: pas de code ou id_token", "danger")
        return redirect(url_for('connexion_page'))
    
    try:
        if id_token:
            # Décoder le JWT Apple
            user_info = jwt.decode(id_token, options={"verify_signature": False})
        else:
            # Échanger le code contre un token
            token_url = 'https://appleid.apple.com/auth/token'
            # Utiliser le redirect_uri explicite pour éviter les problèmes HTTP/HTTPS
            redirect_uri = APPLE_REDIRECT_URI
            data = {
                'code': code,
                'client_id': APPLE_CLIENT_ID,
                'client_secret': generate_apple_client_secret(),
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            response = requests.post(token_url, data=data)
            tokens = response.json()
            id_token = tokens.get('id_token')
            if id_token:
                user_info = jwt.decode(id_token, options={"verify_signature": False})
            else:
                flash("Erreur token Apple", "danger")
                return redirect(url_for('connexion_page'))
        
        apple_id = user_info.get('sub')
        email = user_info.get('email')
        
        # Vérifier si l'utilisateur existe déjà avec Apple
        user = User.query.filter_by(apple_id=apple_id).first()
        
        if user:
            session['phone'] = user.phone
            flash("✅ Connecté with Apple !", "success")
            return redirect(url_for('dashboard_page'))
        
        # Vérifier si l'utilisateur existe avec cet email
        if email:
            user = User.query.filter_by(email=email).first()
            if user:
                user.apple_id = apple_id
                db.session.commit()
                session['phone'] = user.phone
                flash("✅ Apple lié à votre compte !", "success")
                return redirect(url_for('dashboard_page'))
        
        if is_register:
            phone = f"apple_{apple_id}"
            if User.query.filter_by(phone=phone).first():
                phone = f"apple_{apple_id}_{random.randint(1000, 9999)}"
            
            name = "Utilisateur Apple"
            if user_data:
                try:
                    name_json = json.loads(user_data)
                    name = f"{name_json.get('name', {}).get('firstName', '')} {name_json.get('name', {}).get('lastName', '')}".strip()
                except:
                    pass
            
            new_user = User(
                username=name or email.split('@')[0] if email else f"user_{apple_id[:8]}",
                email=email,
                phone=phone,
                apple_id=apple_id,
                password=None,
                solde_total=0,
                solde_depot=0,
                solde_revenu=0,
                solde_parrainage=0
            )
            db.session.add(new_user)
            db.session.commit()
            
            session['phone'] = new_user.phone
            flash("🎉 Compte créé avec Apple !", "success")
            return redirect(url_for('dashboard_page'))
        else:
            flash("⚠️ Aucun compte trouvé. Veuillez vous inscrire.", "warning")
            return redirect(url_for('inscription_page'))
            
    except Exception as e:
        flash(f"Erreur Apple: {str(e)}", "danger")
        return redirect(url_for('connexion_page'))

def generate_apple_client_secret():
    """Génère un client_secret pour Apple (nécessite une clé privée)"""
    # Cette fonction nécessite la clé privée Apple
    # Pour l'instant, retourne une valeur placeholder
    return "apple_client_secret_placeholder"

# ============================================
# API NOTIFICATIONS - Real-time updates
# ============================================
@app.route('/api/notifications')
@login_required
def api_get_notifications():
    """Récupère les notifications de l'utilisateur connecté."""
    try:
        user_phone = session.get('phone')
        if not user_phone:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Get unread notifications, ordered by most recent first
        notifications = Notification.query.filter_by(
            user_phone=user_phone,
            is_read=False
        ).order_by(Notification.created_at.desc()).limit(20).all()
        
        # Map notification types to display types
        type_map = {
            'deposit': 'success',
            'withdrawal': 'info',
            'investment': 'success',
            'profit': 'success',
            'referral': 'success',
            'system': 'info',
            'warning': 'warning',
            'error': 'error'
        }
        
        result = []
        for n in notifications:
            result.append({
                'id': n.id,
                'type': type_map.get(n.type, 'info'),
                'title': n.title,
                'message': n.message,
                'created_at': n.created_at.isoformat() if n.created_at else datetime.utcnow().isoformat(),
                'read': n.is_read,
                'action_url': n.action_url
            })
        
        return jsonify({
            'success': True,
            'notifications': result,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def api_mark_notification_read(notification_id):
    """Marque une notification comme lue."""
    try:
        user_phone = session.get('phone')
        if not user_phone:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404
        
        # Only allow users to mark their own notifications
        if notification.user_phone != user_phone:
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# AI REGISTRATION FLOW
# ============================================

# Store pending registrations in memory (could use Redis for production)
pending_registrations = {}

@app.route('/api/ai-register', methods=['POST'])
def api_ai_register():
    """AI-powered registration flow endpoint"""
    import json
    data = request.get_json()
    action = data.get('action')
    
    if action == 'check_phone':
        phone = data.get('phone', '').strip()
        if not phone:
            return jsonify({'exists': False, 'error': 'Phone required'})
        
        # Check if phone already exists
        existing = User.query.filter_by(phone=phone).first()
        return jsonify({'exists': existing is not None})
    
    elif action == 'check_email':
        email = data.get('email', '').strip().lower()
        if not email:
            return jsonify({'exists': False, 'error': 'Email required'})
        
        # Check if email already exists
        existing = User.query.filter_by(email=email).first()
        return jsonify({'exists': existing is not None})
    
    elif action == 'start_registration':
        # Store registration data temporarily
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        pays = data.get('pays', '')
        referral_code = data.get('referral_code', '').strip().upper()
        
        # Generate OTP
        otp = generate_otp()
        
        # Store in pending registrations
        session_id = f"{phone}_{int(datetime.utcnow().timestamp())}"
        pending_registrations[session_id] = {
            'phone': phone,
            'email': email,
            'username': username,
            'password': password,
            'pays': pays,
            'referral_code': referral_code,
            'otp': otp,
            'expires': datetime.utcnow() + timedelta(minutes=10)
        }
        
        # Send OTP email
        success, error = send_otp_email(email, otp, "inscription")
        if not success:
            print(f"OTP email error: {error}")
            return jsonify({
                'success': False,
                'error': f"Impossible d'envoyer le code OTP : {error or 'Erreur inconnue'}"
            })
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'OTP sent to your email'
        })
    
    elif action == 'verify_otp':
        session_id = data.get('session_id')
        otp_input = data.get('otp', '').strip()
        
        if session_id not in pending_registrations:
            return jsonify({'success': False, 'error': 'Session expired'})
        
        reg_data = pending_registrations[session_id]
        
        # Check OTP
        if otp_input != reg_data['otp']:
            return jsonify({'success': False, 'error': 'Invalid OTP'})
        
        # Check expiration
        if datetime.utcnow() > reg_data['expires']:
            del pending_registrations[session_id]
            return jsonify({'success': False, 'error': 'Session expired'})
        
        # Check referral code
        parrain_code_value = None
        if reg_data.get('referral_code'):
            parrain_user = User.query.filter_by(referral_code=reg_data['referral_code']).first()
            if parrain_user:
                parrain_code_value = parrain_user.referral_code
        
        # Create user
        new_user = User(
            username=reg_data['username'],
            email=reg_data['email'],
            phone=reg_data['phone'],
            password=reg_data['password'],
            wallet_country=reg_data.get('pays', ''),
            solde_total=0,
            solde_depot=0,
            solde_revenu=0,
            solde_parrainage=0,
            parrain_code=parrain_code_value,
            otp_verified=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate verification token
        token = generate_verification_token()
        new_user.email_verification_token = token
        new_user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        
        # Send verification email
        try:
            send_verification_email(reg_data['email'], token)
        except:
            pass
        
        # Clean up pending registration
        del pending_registrations[session_id]
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'redirect': url_for('connexion_page')
        })
    
    return jsonify({'error': 'Invalid action'}), 400

@app.route('/api/ai-chat', methods=['POST'])
def api_ai_chat():
    """AI chat endpoint with registration flow support"""
    data = request.get_json()
    message = data.get('message', '').lower().strip()
    lang = data.get('lang', 'fr')
    
    # AI responses with registration flow detection
    responses = {
        'fr': {
            'create_account': [
                'Je veux créer un compte',
                'créer un compte',
                'inscription',
                "s'inscrire",
                'ouvrir un compte',
                'creer un compte',
                'je veux m inscrire',
                'je voudrais créer un compte'
            ],
            'account_created': '🎉 Excellent ! Je vais vous guider pour créer votre compte TokenFlow. Commençons par les informations de base.\n\n📱 Quel est votre numéro de téléphone ? (avec indicatif pays, ex: +33612345678)',
            'ask_email': '✅ Numéro enregistré !\n\n📧 Quelle est votre adresse email ?',
            'ask_username': '✅ Email enregistré !\n\n👤 Quel nom d\'utilisateur souhaitez-vous ? (sans espaces)',
            'ask_password': '✅ Nom d\'utilisateur : {username}\n\n🔐 Choisissez un mot de passe (min 6 caractères)',
            'ask_country': '✅ Mot de passe enregistré !\n\n🌍 Dans quel pays résidez-vous ?',
            'ask_referral': '✅ Pays enregistré !\n\n🤝 Avez-vous un code de parrainage ? (laissez vide si non)',
            'sending_otp': '📧 Un code OTP a été envoyé à {email}. Veuillez le saisir pour vérifier votre compte.',
            'registration_complete': '🎉 Félicitations ! Votre compte TokenFlow a été créé avec succès !\n\nVous allez recevoir un email de vérification. Cliquez sur le lien pour activer votre compte.\n\n👉 <a href="/connexion" style="color: #6366F1; font-weight: 700;">Connectez-vous maintenant</a>',
            'error_exists': '❌ Ce {field} existe déjà. Veuillez en choisir un autre.',
            'error_invalid': '❌ Format invalide. Veuillez entrer un {field} valide.',
            'help': 'Je suis l\'assistant IA TokenFlow ! 🤖\n\nJe peux vous aider à :\n• Créer un compte (tapez "créer un compte")\n• Répondre à vos questions sur la plateforme\n• Vous guider dans vos premiers pas\n\nComment puis-je vous aider ?'
        },
        'en': {
            'create_account': [
                'create account',
                'sign up',
                'register',
                'i want to create',
                'open an account'
            ],
            'account_created': '🎉 Great! I\'ll guide you through creating your TokenFlow account. Let\'s start with basic info.\n\n📱 What is your phone number? (with country code, ex: +1234567890)',
            'ask_email': '✅ Phone saved!\n\n📧 What is your email address?',
            'ask_username': '✅ Email saved!\n\n👤 What username would you like? (no spaces)',
            'ask_password': '✅ Username: {username}\n\n🔐 Choose a password (min 6 characters)',
            'ask_country': '✅ Password saved!\n\n🌍 Which country do you live in?',
            'ask_referral': '✅ Country saved!\n\n🤝 Do you have a referral code? (leave empty if not)',
            'sending_otp': '📧 An OTP code has been sent to {email}. Please enter it to verify your account.',
            'registration_complete': '🎉 Congratulations! Your TokenFlow account has been created successfully!\n\nYou\'ll receive a verification email. Click the link to activate your account.\n\n👉 <a href="/connexion" style="color: #6366F1; font-weight: 700;">Login now</a>',
            'error_exists': '❌ This {field} already exists. Please choose another.',
            'error_invalid': '❌ Invalid format. Please enter a valid {field}.',
            'help': 'I\'m the TokenFlow AI assistant! 🤖\n\nI can help you:\n• Create an account (type "create account")\n• Answer questions about the platform\n• Guide you through your first steps\n\nHow can I help you?'
        }
    }
    
    # Get responses for current language
    lang_responses = responses.get(lang, responses['fr'])
    
    # Check if user wants to create account
    for phrase in lang_responses['create_account']:
        if phrase in message:
            return jsonify({
                'response': lang_responses['account_created'],
                'step': 'ask_phone',
                'show_form': True
            })
    
    return jsonify({'response': 'Je suis l\'assistant IA TokenFlow. Tapez "créer un compte" pour commencer l\'inscription ! 😊'})

@app.route('/api/check-first-deposit')
@login_required
def api_check_first_deposit():
    """Vérifie si l'utilisateur a effectué son premier dépôt."""
    try:
        user_phone = session.get('phone')
        if not user_phone:
            return jsonify({'has_first_deposit': False, 'error': 'Not authenticated'}), 401
        
        # Check if user has any validated deposit
        first_deposit = Depot.query.filter_by(
            phone=user_phone,
            statut='valide'
        ).first()
        
        return jsonify({
            'has_first_deposit': first_deposit is not None
        })
    except Exception as e:
        return jsonify({
            'has_first_deposit': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def api_mark_all_notifications_read():
    """Marque toutes les notifications comme lues."""
    try:
        user_phone = session.get('phone')
        if not user_phone:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        Notification.query.filter_by(
            user_phone=user_phone,
            is_read=False
        ).update({'is_read': True})
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# PUSH NOTIFICATION SYSTEM (Web Push)
# ============================================
import hmac
import hashlib
import json as json_module
import base64
import os

# VAPID Keys Configuration
_VAPID_PRIVATE_KEY = None
_VAPID_PUBLIC_KEY = None

VAPID_CLAIMS = {
    'sub': 'mailto:support@flowtoken.uk'
}

def _generate_vapid_keys():
    """Génère une nouvelle paire de clés VAPID en utilisant py_vapid."""
    try:
        from py_vapid import Vapid02
        import ecdsa
        
        # Generate new VAPID keys using Vapid02
        vapid = Vapid02()
        
        # Generate the keys
        vapid.generate_keys()
        
        # Get private key as base64url (32 bytes)
        # The private key is the raw secret key
        private_bytes = vapid.private_key.to_string()
        private_key = base64.urlsafe_b64encode(private_bytes).rstrip(b'=').decode('ascii')
        
        # Get public key in UNCOMPRESSED format (65 bytes WITH 0x04 prefix)
        # Vapid02 provides public_key as PEM, so we need the raw format
        public_bytes = vapid.public_key.to_string()
        # Add 0x04 prefix for uncompressed format
        public_key_raw = b'\x04' + public_bytes
        
        # Encode as base64url without padding
        public_key = base64.urlsafe_b64encode(public_key_raw).rstrip(b'=').decode('ascii')
        
        print(f"🔑 Clés VAPID générées avec succès")
        print(f"   Private key length: {len(private_key)} chars")
        print(f"   Public key length: {len(public_key)} chars")
        
        return private_key, public_key
    except ImportError:
        print("❌ py_vapid n'est pas installé. Installez-le avec: pip install py-vapid")
        return None, None
    except Exception as e:
        print(f"❌ Erreur génération clés VAPID: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def get_vapid_keys():
    """Récupère les clés VAPID depuis les variables d'environnement ou en génère de nouvelles."""
    global _VAPID_PRIVATE_KEY, _VAPID_PUBLIC_KEY
    
    if _VAPID_PRIVATE_KEY and _VAPID_PUBLIC_KEY:
        return _VAPID_PRIVATE_KEY, _VAPID_PUBLIC_KEY
    
    # Try to get from environment
    env_private = os.getenv('VAPID_PRIVATE_KEY', '').strip()
    env_public = os.getenv('VAPID_PUBLIC_KEY', '').strip()
    
    if env_private and env_public:
        _VAPID_PRIVATE_KEY = env_private
        _VAPID_PUBLIC_KEY = env_public
        print(f"✅ Clés VAPID chargées depuis .env (public key length: {len(env_public)})")
        return _VAPID_PRIVATE_KEY, _VAPID_PUBLIC_KEY
    
    # Generate new keys
    print("🔄 Génération de nouvelles clés VAPID...")
    _VAPID_PRIVATE_KEY, _VAPID_PUBLIC_KEY = _generate_vapid_keys()
    
    if _VAPID_PRIVATE_KEY and _VAPID_PUBLIC_KEY:
        print("⚠️  Nouvelles clés VAPID générées. Ajoutez-les à votre .env:")
        print(f"   VAPID_PRIVATE_KEY={_VAPID_PRIVATE_KEY}")
        print(f"   VAPID_PUBLIC_KEY={_VAPID_PUBLIC_KEY}")
        print(f"   (public key length: {len(_VAPID_PUBLIC_KEY)})")
    else:
        print("❌ Erreur génération clés VAPID")
    
    return _VAPID_PRIVATE_KEY, _VAPID_PUBLIC_KEY

def send_push_notification_to_subscription(subscription, title, body, url=None, icon='/static/images/logo.svg', badge='/static/images/badge.png', require_interaction=False):
    """Envoie une notification push à un abonnement spécifique.
    
    Gère automatiquement le nettoyage des abonnements invalides:
    - 404: Endpoint introuvable
    - 410: Endpoint expiré/supprimé
    - Autres erreurs de connexion
    """
    try:
        from py_vapid import Vapid
        from pywebpush import webpush
        from pywebpush import WebPushException
        
        private_key, public_key = get_vapid_keys()
        
        # Create Vapid instance
        vapid = Vapid()
        vapid.private_raw = base64.urlsafe_b64decode(private_key + '==')
        vapid.public_raw = base64.urlsafe_b64decode(public_key + '==')
        
        # Payload optimisé pour batterie mobile (léger)
        payload = json_module.dumps({
            'title': title,
            'body': body,
            'url': url or '/dashboard',
            'icon': icon,
            'badge': badge,
            'requireInteraction': require_interaction,
            'timestamp': datetime.utcnow().isoformat(),
            'ttl': 86400  # Indique au client la durée de vie
        }, separators=(',', ':'))  # Réduit taille JSON
        
        response = webpush(
            subscription_info={
                'endpoint': subscription.endpoint,
                'keys': {
                    'p256dh': subscription.p256dh,
                    'auth': subscription.auth
                }
            },
            data=payload,
            vapid_private_key=private_key,
            vapid_claims=VAPID_CLAIMS,
            ttl=86400  # 24 hours - évite réveils inutiles
        )
        
        status_code = response.status_code
        
        # Nettoyer les abonnements invalides
        if status_code in [404, 410, 400]:
            print(f"[TokenFlow Push] 🗑️ Subscription invalide ({status_code}), désactivation...")
            subscription.is_active = False
            subscription.last_used = datetime.utcnow()
            db.session.commit()
            return False
        
        # Mettre à jour last_used pour les succès
        subscription.last_used = datetime.utcnow()
        db.session.commit()
        
        return status_code < 400
        
    except WebPushException as e:
        print(f"[TokenFlow Push] ❌ WebPushException: {e}")
        # Nettoyer si erreur fatale
        if e.response and e.response.status_code in [404, 410, 400]:
            subscription.is_active = False
            db.session.commit()
        return False
        
    except Exception as e:
        print(f"[TokenFlow Push] ❌ Erreur envoi push notification: {e}")
        # Nettoyer si endpoint expiré
        if '410' in str(e) or '404' in str(e) or 'Gone' in str(e):
            subscription.is_active = False
            db.session.commit()
        return False

def send_push_notification_to_user(user_phone, title, body, url=None, require_interaction=False):
    """Envoie une notification push à TOUS les appareils d'un utilisateur (multi-device).
    
    Supporte:
    - PC (Chrome, Firefox, Edge, Safari)
    - Android (Chrome, Samsung Internet)
    - iOS/iPadOS (Safari PWA)
    - Tablettes
    
    Logs production:
    - Nombre d'appareils cibles
    - Type de chaque appareil
    - Navigateur et OS
    - Statut d'envoi par appareil
    """
    subscriptions = PushSubscription.query.filter_by(
        user_phone=user_phone,
        is_active=True
    ).all()
    
    if not subscriptions:
        print(f"[TokenFlow Push] ❌ Aucun abonnement actif trouvé pour {user_phone}")
        return False
    
    print(f"[TokenFlow Push] 📱 Envoi notification à {user_phone} sur {len(subscriptions)} appareil(s):")
    
    success_count = 0
    failed_count = 0
    
    for i, sub in enumerate(subscriptions):
        device_info = f"Appareil {i+1}: {sub.browser} ({sub.device_type})"
        
        try:
            result = send_push_notification_to_subscription(
                sub, 
                title, 
                body, 
                url, 
                require_interaction=require_interaction
            )
            
            if result:
                success_count += 1
                print(f"[TokenFlow Push] ✅ {device_info} - Notification envoyée")
            else:
                failed_count += 1
                print(f"[TokenFlow Push] ❌ {device_info} - Échec envoi")
                
        except Exception as e:
            failed_count += 1
            print(f"[TokenFlow Push] ❌ {device_info} - Erreur: {e}")
    
    total = len(subscriptions)
    print(f"[TokenFlow Push] 📊 Résumé: {success_count}/{total} appareils atteints, {failed_count} échecs")
    
    return success_count > 0

def broadcast_push_notification(title, body, url=None, require_interaction=False):
    """Envoie une notification push à TOUS les utilisateurs (pour annonces globales)."""
    # Récupérer tous les abonnements actifs
    subscriptions = PushSubscription.query.filter_by(is_active=True).all()
    
    success_count = 0
    for sub in subscriptions:
        if send_push_notification_to_subscription(sub, title, body, url, require_interaction=require_interaction):
            success_count += 1
    
    return success_count

@app.route('/api/push/vapid-keys')
def api_get_vapid_keys():
    """Retourne la clé publique VAPID pour le navigateur.
    
    NOTE: Cette route doit être publique (pas de @login_required)
    car elle est appelée avant l'abonnement push.
    """
    # Récupérer directement depuis les variables d'environnement
    public_key = os.environ.get('VAPID_PUBLIC_KEY', '').strip()
    
    # Logs backend
    print("=" * 60)
    print("🔑 API /api/push/vapid-keys called")
    print(f"   VAPID_PUBLIC_KEY from env: {public_key[:20] if public_key else 'NONE'}...")
    print(f"   Longueur: {len(public_key)} caractères")
    
    if not public_key:
        print("   ⚠️  VAPID_PUBLIC_KEY not set in environment!")
        # Générer une nouvelle clé si manquante
        _, public_key = get_vapid_keys()
        if public_key:
            print(f"   🔄 Generated new key: {public_key[:20]}... ({len(public_key)} chars)")
    
    print("=" * 60)
    
    if not public_key:
        return jsonify({'error': 'VAPID public key not configured'}), 500
    
    return jsonify({'publicKey': public_key})

@app.route('/api/push/subscribe', methods=['POST'])
@login_required
def api_subscribe_push():
    """Enregistre un nouvel abonnement push pour l'utilisateur connecté."""
    try:
        user_phone = session.get('phone')
        if not user_phone:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        endpoint = data.get('endpoint')
        p256dh = data.get('p256dh')
        auth = data.get('auth')
        browser = data.get('browser', 'Unknown')
        device_type = data.get('device_type', 'desktop')
        
        if not all([endpoint, p256dh, auth]):
            return jsonify({'success': False, 'error': 'Missing subscription data'}), 400
        
        # Vérifier si l'abonnement existe déjà
        existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if existing:
            existing.is_active = True
            existing.last_used = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Subscription updated'})
        
        # Créer un nouvel abonnement
        subscription = PushSubscription(
            user_phone=user_phone,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            browser=browser,
            device_type=device_type,
            is_active=True
        )
        db.session.add(subscription)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Subscription created'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/push/unsubscribe', methods=['POST'])
@login_required
def api_unsubscribe_push():
    """Désactive tous les abonnements push de l'utilisateur."""
    try:
        user_phone = session.get('phone')
        if not user_phone:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        PushSubscription.query.filter_by(user_phone=user_phone).update({'is_active': False})
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Unsubscribed from push notifications'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/push/test', methods=['POST'])
@login_required
def api_test_push():
    """Envoie une notification push de test à l'utilisateur."""
    try:
        user_phone = session.get('phone')
        if not user_phone:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        title = data.get('title', 'Test TokenFlow')
        body = data.get('body', 'Ceci est une notification de test')
        
        print("=" * 60)
        print(f"🔔 Envoi notification push test à {user_phone}")
        print(f"   Title: {title}")
        print(f"   Body: {body}")
        
        # Vérifier les abonnements
        subscriptions = PushSubscription.query.filter_by(
            user_phone=user_phone,
            is_active=True
        ).all()
        
        print(f"   Abonnements trouvés: {len(subscriptions)}")
        
        if not subscriptions:
            print("   ❌ Aucun abonnement actif trouvé")
            return jsonify({'success': False, 'error': 'Aucun abonnement push actif'}), 400
        
        for i, sub in enumerate(subscriptions):
            print(f"   Abonnement {i+1}:")
            print(f"     Endpoint: {sub.endpoint[:50]}...")
            print(f"     p256dh: {sub.p256dh[:20]}...")
            print(f"     auth: {sub.auth[:20]}...")
        
        success = send_push_notification_to_user(
            user_phone,
            title,
            body,
            url='/dashboard',
            require_interaction=True
        )
        
        print(f"{'✅' if success else '❌'} Notification push test {'envoyée' if success else 'échouée'}")
        print("=" * 60)
        return jsonify({'success': success})
    except Exception as e:
        print(f"❌ Erreur envoi notification test: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/push-test')
@login_required
def push_test_page():
    """Page de test des notifications push."""
    return render_template('push_test.html')

# ============================================
# AGRICULTURE PDF DOWNLOAD API
# ============================================

# Configuration des PDFs disponibles par niveau
AGRICULTURE_PDFS = {
    # Niveau 2 (requis: pack_level >= 2)
    'elevage_avicole': {
        'name': 'Guide_Complet_Elevage_Avicole.pdf',
        'display_name': 'Guide Complet d\'Élevage Avicole',
        'required_level': 2
    },
    'nutrition_animale': {
        'name': 'Manuel_Nutrition_Animale.pdf',
        'display_name': 'Manuel de Nutrition Animale',
        'required_level': 2
    },
    # Niveau 3 (requis: pack_level >= 3)
    'irrigation': {
        'name': 'Irrigation_Intelligente.pdf',
        'display_name': 'Irrigation Intelligente et Gestion de l\'Eau',
        'required_level': 3
    },
    'culture-intensive': {
        'name': 'Techniques_Culture_Intensive.pdf',
        'display_name': 'Techniques de Culture Intensive',
        'required_level': 3
    },
    # Niveau 4 (requis: pack_level >= 4)
    'business-plan': {
        'name': 'Business_Plan_Agricole.pdf',
        'display_name': 'Business Plan Agricole Complet',
        'required_level': 4
    },
    'marketing': {
        'name': 'Strategies_Commercialisation.pdf',
        'display_name': 'Stratégies de Commercialisation',
        'required_level': 4
    },
    # Niveau 5+ (requis: pack_level >= 5)
    'elevage-bovin': {
        'name': 'Guide_Expert_Elevage_Bovin.pdf',
        'display_name': 'Guide Expert - Élevage Bovin Intensif',
        'required_level': 5
    },
    'exportation': {
        'name': 'Exportation_Marches_Internationaux.pdf',
        'display_name': 'Exportation & Marchés Internationaux',
        'required_level': 5
    },
    'collection-complete': {
        'name': 'Collection_Complete_Agriculture.zip',
        'display_name': 'Collection Complète - Tous les Guides',
        'required_level': 5
    }
}

@app.route('/api/agriculture/download/<pdf_id>')
@login_required
def download_agriculture_pdf(pdf_id):
    """
    Téléchargement de PDF avec contrôle d'accès basé sur le pack_level.
    
    Règles d'accès:
    - Niveau 1: Pas d'accès
    - Pack 2: Accès niveau 2
    - Pack 3: Accès niveau 3
    - Pack 4: Accès niveau 4
    - Pack 5+: Accès à tous les PDFs
    """
    try:
        user_phone = get_logged_in_user_phone()
        if not user_phone:
            return jsonify({'error': 'Non authentifié'}), 401
        
        user = User.query.filter_by(phone=user_phone).first()
        if not user:
            return jsonify({'error': 'Utilisateur introuvable'}), 404
        
        # Vérifier si le PDF existe
        if pdf_id not in AGRICULTURE_PDFS:
            return jsonify({'error': 'PDF introuvable'}), 404
        
        pdf_info = AGRICULTURE_PDFS[pdf_id]
        required_level = pdf_info['required_level']
        user_level = user.pack_level or 1
        
        # Vérifier le niveau d'accès
        if user_level < required_level:
            return jsonify({
                'error': 'Accès refusé',
                'message': f'Vous devez avoir le Pack {required_level} ou supérieur pour accéder à ce PDF.',
                'user_level': user_level,
                'required_level': required_level,
                'upgrade_url': url_for('produits_rapide_page', _external=True)
            }), 403
        
        # Log the download
        print(f"[PDF Download] {user_phone} a téléchargé: {pdf_info['display_name']}")
        
        # Retourner le chemin du fichier pour téléchargement
        # Les PDFs doivent être placés dans static/agriculture/
        pdf_path = url_for('static', filename=f'agriculture/{pdf_info["name"]}')
        
        return jsonify({
            'success': True,
            'download_url': pdf_path,
            'filename': pdf_info['name'],
            'display_name': pdf_info['display_name']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/pack-level')
@login_required
def get_user_pack_level():
    """Retourne le niveau de pack actuel de l'utilisateur."""
    try:
        user_phone = get_logged_in_user_phone()
        if not user_phone:
            return jsonify({'error': 'Non authentifié'}), 401
        
        user = User.query.filter_by(phone=user_phone).first()
        if not user:
            return jsonify({'error': 'Utilisateur introuvable'}), 404
        
        return jsonify({
            'success': True,
            'pack_level': user.pack_level or 1,
            'access_levels': {
                'level_2': (user.pack_level or 1) >= 2,
                'level_3': (user.pack_level or 1) >= 3,
                'level_4': (user.pack_level or 1) >= 4,
                'level_5': (user.pack_level or 1) >= 5
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# ADMIN: Set user pack level
# ============================================

@app.route('/admin/user/<int:user_id>/set-pack-level', methods=['POST'])
@login_required
def admin_set_pack_level(user_id):
    """
    Permet à l'admin de définir le niveau de pack d'un utilisateur.
    Niveaux: 1 (base), 2, 3, 4, 5 (premium - accès illimité)
    """
    if not admin_required(lambda: None)():
        return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
    
    try:
        new_level = int(request.form.get('pack_level', 1))
        if new_level < 1 or new_level > 5:
            return jsonify({'error': 'Niveau invalide (doit être entre 1 et 5)'}), 400
        
        user = User.query.get_or_404(user_id)
        old_level = user.pack_level or 1
        user.pack_level = new_level
        db.session.commit()
        
        # Envoyer notification à l'utilisateur
        try:
            create_notification(
                user.phone,
                'pack_upgrade',
                f'🎉 Pack mis à niveau!',
                f'Votre pack est passé au niveau {new_level}. Vous avez maintenant accès à plus de ressources de formation.',
                url_for('formation_agri_page', _external=True)
            )
        except:
            pass
        
        return jsonify({
            'success': True,
            'message': f'Pack level mis à jour: {old_level} → {new_level}',
            'user_phone': user.phone,
            'old_level': old_level,
            'new_level': new_level
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    bg_thread = threading.Thread(target=paiement_quotidien, daemon=True)
    bg_thread.start()
    print("🚀 Serveur TokenFlow démarré sur http://127.0.0.1:5000")
    print("⚙️  Système de paiement automatique activé.")
    print("📝 Pour activer Google/Apple OAuth, configurez les variables d'environnement:")
    print("   - GOOGLE_CLIENT_ID")
    print("   - GOOGLE_CLIENT_SECRET")
    print("   - APPLE_CLIENT_ID")
    print("   - APPLE_TEAM_ID")
    print("   - APPLE_KEY_ID")
    app.run(debug=True, host="0.0.0.0")
