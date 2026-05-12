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

load_dotenv()

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

    premier_depot = db.Column(db.Boolean, default=False)

    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)

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

class ReferralLeaderboard(db.Model):
    """Classement des parrains"""
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(30), nullable=False, unique=True)
    total_referrals = db.Column(db.Integer, default=0)
    active_referrals = db.Column(db.Integer, default=0)
    total_commissions = db.Column(db.Float, default=0.0)
    rank = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

def create_notification(user_phone, notif_type, title, message, action_url=None):
    """Crée une notification pour un utilisateur."""
    notification = Notification(
        user_phone=user_phone,
        type=notif_type,
        title=title,
        message=message,
        action_url=action_url
    )
    db.session.add(notification)
    db.session.commit()
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

        new_user = User(
            username=username,
            email=email,
            phone=phone,
            password=password,
            wallet_country=pays,
            solde_total=1000,
            solde_depot=1000,
            solde_revenu=0,
            solde_parrainage=0,
            parrain_code=parrain_code_value
        )

        db.session.add(new_user)
        db.session.commit()

        flash("🎉 Inscription réussie ! Connectez-vous maintenant.", "success")
        return redirect(url_for("connexion_page"))

    return render_template("inscription.html", code_ref=code_ref)

@app.route("/connexion", methods=["GET", "POST"])
def connexion_page():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()

        if not phone or not password:
            flash({"title": "Erreur", "message": "Veuillez remplir tous les champs."}, "danger")
            return redirect(url_for("connexion_page"))

        user = User.query.filter_by(phone=phone).first()

        if not user:
            flash({"title": "Erreur", "message": "Numéro introuvable."}, "danger")
            return redirect(url_for("connexion_page"))

        if user.password != password:
            flash({"title": "Erreur", "message": "Mot de passe incorrect."}, "danger")
            return redirect(url_for("connexion_page"))

        session["phone"] = user.phone

        flash({"title": "Connexion réussie", "message": "Bienvenue sur TokenFlow !"}, "success")
        return redirect(url_for("dashboard_page"))

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

@app.route("/admin")
@login_required
def admin_dashboard():
    stats = {
        "users": User.query.count(),
        "depots": Depot.query.count(),
        "retraits": Retrait.query.count(),
        "investissements": Investissement.query.count(),
        "staking": Staking.query.count(),
        "commissions": Commission.query.count(),
        "solde_total": db.session.query(db.func.sum(User.solde_total)).scalar() or 0
    }
    return render_template("admin/dashboard.html", stats=stats)

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

@app.route("/deposit", methods=["POST"])
@login_required
def create_deposit():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 400

    try:
        montant = int(request.form.get("montant", 0))
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

    if operator == "Stripe":
        if montant < 6000:
            return jsonify({"error": "Montant minimum 10 USD (6 000 XOF) pour le paiement par carte"}), 400
        if not all([card_holder, card_number, card_expiry, card_cvc]):
            return jsonify({"error": "Tous les champs de carte sont requis pour le paiement Stripe"}), 400
        fullname = card_holder
        if not card_number.replace(" ", "").isdigit() or not 12 <= len(card_number.replace(" ", "")) <= 19:
            return jsonify({"error": "Numéro de carte invalide"}), 400
        if not re.match(r'^(0[1-9]|1[0-2])\/(\d{2})$', card_expiry):
            return jsonify({"error": "Date d'expiration invalide. Format MM/AA"}), 400
        if not card_cvc.isdigit() or len(card_cvc) not in [3, 4]:
            return jsonify({"error": "CVC invalide"}), 400
        payment_link = "https://buy.stripe.com/test_7sY14mePmbMJ9Ki2518Zq00"
        masked_card = card_number.replace(" ", "")
        last4 = masked_card[-4:] if len(masked_card) >= 4 else "????"
        reference = f"Stripe ****{last4}"
        
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
        if montant < 3000:
            return jsonify({"error": "Montant minimum 3000 FCFA pour Mobile Money"}), 400
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

# Taux de change (1 USD = ...)
USD_TO_XOF = 625
USD_TO_EUR = 0.92

PRODUITS_VIP = [
    # Crypto Trading (prix en USD) - ROI: 0.8% à 1.2% par jour
    {"id": 1, "nom": "Bitcoin Trader Pro", "prix_usd": 50, "revenu_journalier_usd": 0.50, "image": "crypto.jpg"},
    {"id": 2, "nom": "Crypto Portfolio Elite", "prix_usd": 100, "revenu_journalier_usd": 1.00, "image": "crypto.jpg"},
    {"id": 3, "nom": "BTC Mining Fund", "prix_usd": 200, "revenu_journalier_usd": 2.20, "image": "crypto.jpg"},
    
    # Forex Trading (prix en USD) - ROI: 0.6% à 1% par jour
    {"id": 4, "nom": "Forex Master Fund", "prix_usd": 60, "revenu_journalier_usd": 0.48, "image": "forex.jpg"},
    {"id": 5, "nom": "Currency Trader Pro", "prix_usd": 150, "revenu_journalier_usd": 1.35, "image": "forex.jpg"},
    
    # Gold Investment (prix en USD) - ROI: 0.4% à 0.7% par jour (sûr)
    {"id": 6, "nom": "Gold Reserve Fund", "prix_usd": 200, "revenu_journalier_usd": 1.20, "image": "gold.jpg"},
    {"id": 7, "nom": "Gold Bullion Premium", "prix_usd": 400, "revenu_journalier_usd": 2.80, "image": "gold.jpg"},
    
    # AI Trading (prix en USD) - ROI: 0.9% à 1.1% par jour
    {"id": 8, "nom": "AI Starter Bot", "prix_usd": 10, "revenu_journalier_usd": 0.10, "image": "ai.jpg"},
    {"id": 9, "nom": "AI Trading Bot Alpha", "prix_usd": 80, "revenu_journalier_usd": 0.72, "image": "ai.jpg"},
    {"id": 13, "nom": "AI Basic Trader", "prix_usd": 25, "revenu_journalier_usd": 0.24, "image": "ai.jpg"},
    {"id": 14, "nom": "AI Pro Assistant", "prix_usd": 50, "revenu_journalier_usd": 0.48, "image": "ai.jpg"},
    {"id": 15, "nom": "AutoTrader Quantum", "prix_usd": 300, "revenu_journalier_usd": 3.30, "image": "ai.jpg"},
    {"id": 16, "nom": "AI Elite System", "prix_usd": 500, "revenu_journalier_usd": 5.75, "image": "ai.jpg"},
    
    # VIP Premium (prix en USD) - ROI: 1% à 1.5% par jour (le plus élevé)
    {"id": 10, "nom": "VIP Diamond Club", "prix_usd": 400, "revenu_journalier_usd": 4.80, "image": "vip.jpg"},
    {"id": 11, "nom": "VIP Platinum Elite", "prix_usd": 800, "revenu_journalier_usd": 10.40, "image": "vip.jpg"},
    {"id": 12, "nom": "VIP Exclusive Fund", "prix_usd": 2000, "revenu_journalier_usd": 28.00, "image": "vip.jpg"},
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

    return render_template(
        "produits_rapide.html",
        user=user,
        produits=PRODUITS_VIP
    )

@app.route("/produits_rapide/confirmer/<int:vip_id>", methods=["GET", "POST"])
@login_required
def confirmer_produit_rapide(vip_id):
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    produit = next((p for p in PRODUITS_VIP if p["id"] == vip_id), None)
    if not produit:
        flash("Produit introuvable.", "danger")
        return redirect(url_for("produits_rapide_page"))

    # Conversion USD vers XOF (1 USD = 625 XOF)
    montant_usd = produit["prix_usd"]
    montant = int(montant_usd * USD_TO_XOF)  # Prix en XOF
    revenu_journalier_usd = produit["revenu_journalier_usd"]
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

    if float(user.solde_total or 0) < montant:
        flash("Solde insuffisant.", "danger")
        return redirect(url_for("produits_rapide_page"))

    user.solde_total -= montant
    credit_user_revenu(user, 1000)

    inv = Investissement(
        phone=phone,
        montant=montant,
        revenu_journalier=revenu_journalier,
        duree=120,
        actif=True
    )
    db.session.add(inv)
    db.session.commit()

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

    montant = produit["prix"]

    if user.solde_total < montant:
        flash("Solde insuffisant.", "danger")
        return redirect(url_for("produits_rapide_page"))

    inv = Investissement(
        phone=phone,
        montant=montant,
        revenu_journalier=produit["revenu_journalier"],
        duree=120,
        actif=True
    )
    db.session.add(inv)

    user.solde_total -= montant
    db.session.commit()

    return render_template("achat_rapide_loader.html", produit=produit)

from datetime import datetime

@app.route("/achats")
@login_required
def achats_page():
    phone = get_logged_in_user_phone()

    investissements = []
    now = datetime.now()

    for inv in Investissement.query.filter_by(phone=phone).order_by(Investissement.date_debut.desc()).all():
        jours_passes = (now - inv.date_debut).days
        progression = min(int((jours_passes / inv.duree) * 100), 100)
        jours_restants = max(inv.duree - jours_passes, 0)

        investissements.append({
            "montant": inv.montant,
            "revenu_journalier": inv.revenu_journalier,
            "jours_restants": jours_restants,
            "progression": progression,
            "actif": inv.actif
        })

    return render_template(
        "achats.html",
        investissements=investissements
    )

@app.route("/finance")
@login_required
def finance_page():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    if not user:
        flash("Session expirée.", "danger")
        return redirect(url_for("connexion_page"))

    revenus_totaux = (user.solde_revenu or 0) + (user.solde_parrainage or 0)
    fortune_totale = (user.solde_depot or 0) + revenus_totaux

    retraits = Retrait.query.filter_by(phone=phone)\
        .order_by(Retrait.date.desc()).limit(10).all()

    depots = Depot.query.filter_by(phone=phone)\
        .order_by(Depot.date.desc()).limit(10).all()

    actifs_raw = Investissement.query.filter_by(phone=phone, actif=True).all()

    actifs = []
    for a in actifs_raw:
        date_fin = a.date_debut + timedelta(days=a.duree)
        actifs.append({
            "montant": a.montant,
            "revenu_journalier": a.revenu_journalier,
            "duree": a.duree,
            "date_debut": a.date_debut,
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

    depots = Depot.query.filter_by(phone=phone).order_by(Depot.date.desc()).all()
    retraits = Retrait.query.filter_by(phone=phone).order_by(Retrait.date.desc()).all()

    commissions = Commission.query.filter_by(
        parrain_phone=phone
    ).order_by(Commission.date.desc()).all()

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
def admin_deposits():
    depots = Depot.query.order_by(Depot.date.desc()).all()
    return render_template("admin_deposits.html", depots=depots)

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

    # Solde retirable = parrainage + revenu SEULEMENT (pas le depot)
    solde_retraitable = (user.solde_parrainage or 0) + (user.solde_revenu or 0)

    if request.method == "POST":
        try:
            montant = float(request.form["montant"])
        except:
            flash("Montant invalide.", "danger")
            return redirect(url_for("retrait_page"))

        # Minimum 15 USD = environ 9 375 XOF
        if montant < 9375:
            flash("Montant minimum : 15 USD (9 375 XOF).", "warning")
            return redirect(url_for("retrait_page"))

        if montant > solde_retraitable:
            flash("Solde insuffisant.", "danger")
            return redirect(url_for("retrait_page"))

        return redirect(url_for("retrait_confirmation_page", montant=montant))

    return render_template(
        "retrait.html",
        user=user,
        solde_total=user.solde_total,
        solde_retraitable=solde_retraitable
    )

@app.route("/retrait/confirmation/<int:montant>", methods=["GET", "POST"])
@login_required
def retrait_confirmation_page(montant):
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    if not user:
        flash("Session expirée.", "danger")
        return redirect(url_for("connexion_page"))

    solde_retraitable = (user.solde_parrainage or 0) + (user.solde_revenu or 0)
    if montant > solde_retraitable:
        flash("Solde insuffisant.", "danger")
        return redirect(url_for("retrait_page"))

    taxe = int(montant * 0.15)
    net = montant - taxe

    if request.method == "POST":
        retrait = Retrait(phone=phone, montant=montant, statut="en_attente")
        db.session.add(retrait)

        reste = montant
        if user.solde_parrainage >= reste:
            user.solde_parrainage -= reste
            reste = 0
        else:
            reste -= user.solde_parrainage
            user.solde_parrainage = 0

        if reste > 0:
            user.solde_revenu -= reste

        db.session.commit()
        return render_template("retrait_confirmation.html", montant=montant, taxe=taxe, net=net, user=user, submitted=True)

    return render_template("retrait_confirmation.html", montant=montant, taxe=taxe, net=net, user=user, submitted=False)

@app.route("/cron/pay_invests")
def cron_pay_invests():
    maintenant = datetime.utcnow()
    invests = Investissement.query.filter_by(actif=True).all()

    total_payes = 0

    for inv in invests:
        if not inv.dernier_paiement:
            inv.dernier_paiement = inv.date_debut

        diff = maintenant - inv.dernier_paiement

        if diff.total_seconds() >= 86400:

            user = User.query.filter_by(phone=inv.phone).first()
            if user:
                user.solde_revenu += inv.revenu_journalier
                total_payes += 1

            inv.dernier_paiement = maintenant

            inv.duree -= 1
            if inv.duree <= 0:
                inv.actif = False

    db.session.commit()
    return f"{total_payes} paiements effectués."

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
            # Connexion existante
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
            solde_total=1000,
            solde_depot=1000,
            solde_revenu=0,
            solde_parrainage=0,
            parrain_code=parrain_code_value
        )
        db.session.add(new_user)
        db.session.commit()
        
        session['phone'] = new_user.phone
        flash("🎉 Compte créé avec Google ! Bienvenue sur TokenFlow.", "success")
        return redirect(url_for('dashboard_page'))
            
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
            session['phone'] = user.phone
            return jsonify({'url': url_for('dashboard_page')})
        
        # Vérifier si l'utilisateur existe avec cet email
        if email:
            user = User.query.filter_by(email=email).first()
            if user:
                user.google_id = google_id
                db.session.commit()
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
            solde_parrainage=0
        )
        db.session.add(new_user)
        db.session.commit()
        
        session['phone'] = new_user.phone
        return jsonify({'url': url_for('dashboard_page')})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 400

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
                solde_total=1000,
                solde_depot=1000,
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
