# 📧 Documentation Emails TokenFlow

## 🎯 Vue d'ensemble

Tous les emails TokenFlow utilisent des templates HTML professionnels et responsifs avec :
- ✅ Design fintech moderne (bleu/indigo + blanc)
- ✅ Logo TokenFlow personnalisé
- ✅ Responsive mobile (max-width: 600px)
- ✅ Éléments de sécurité
- ✅ Footer copyright

## 📋 Templates disponibles

### 1. ✉️ Email OTP (Inscription, Connexion, Réinitialisation)

**Fonction:** `send_otp_email(user_email, otp_code, purpose)`

**Paramètres:**
- `user_email`: Email du destinataire
- `otp_code`: Code OTP à 6 chiffres
- `purpose`: "inscription" | "connexion" | "reset_password"

**Features:**
- Code OTP mis en évidence avec gradient bleu
- Boîte de code avec espacement des chiffres
- Avertissement d'expiration (10 minutes)
- Notice de sécurité "Ne partagez jamais"

**Utilisation:**
```python
send_otp_email("user@example.com", "123456", "inscription")
send_otp_email("user@example.com", "654321", "connexion")
send_otp_email("user@example.com", "789456", "reset_password")
```

---

### 2. 👋 Email Bienvenue

**Fonction:** `send_welcome_email(username, user_email)`

**Paramètres:**
- `username`: Nom d'utilisateur
- `user_email`: Email du destinataire

**Features:**
- Greeting personnalisé
- 4 cartes de features (Investissements, Parrainage, Analyses, Sécurité)
- Bouton CTA vers le tableau de bord
- Bonus bienvenue pour les 200 premiers utilisateurs

**Utilisation:**
```python
send_welcome_email("Jean Dupont", "jean@example.com")
```

---

### 3. 💳 Email Confirmation Dépôt

**Fonction:** `send_deposit_confirmation_email(phone, amount, currency, reference, user_email)`

**Paramètres:**
- `phone`: Numéro du compte
- `amount`: Montant déposé
- `currency`: Devise (USD, EUR, XOF)
- `reference`: Numéro de référence de transaction
- `user_email`: Email du destinataire

**Features:**
- Icône de succès vert
- Montant en gros caractères
- Tableau de détails (numéro, montant, référence, date)
- Bouton "Voir mon Solde"

**Utilisation:**
```python
send_deposit_confirmation_email("+22997000000", 1000.50, "USD", "DEP20240606123", "user@example.com")
```

---

### 4. 🔄 Email Confirmation Retrait

**Fonction:** `send_withdrawal_confirmation_email(phone, amount, currency, reference, user_email)`

**Paramètres:**
- `phone`: Numéro de destination
- `amount`: Montant retiré
- `currency`: Devise
- `reference`: Numéro de référence
- `user_email`: Email du destinataire

**Features:**
- Icône d'horloge (statut en attente)
- Montant avec badge "Traitement en cours (1-2 jours)"
- Tableau de détails
- Notice d'information

**Utilisation:**
```python
send_withdrawal_confirmation_email("+22997000000", 500.00, "USD", "WIT20240606456", "user@example.com")
```

---

### 5. ✨ Email Notification Produit

**Fonction:** `send_product_notification_email(user_email, product_name, description, daily_roi, min_amount)`

**Paramètres:**
- `user_email`: Email du destinataire
- `product_name`: Nom du produit
- `description`: Description du produit
- `daily_roi`: Rendement quotidien en %
- `min_amount`: Investissement minimum

**Features:**
- Icône d'annonce (étoile)
- Carte de produit avec gradient rose
- Tableau des caractéristiques (ROI, Min)
- Bouton CTA "Découvrir et Investir"

**Utilisation:**
```python
send_product_notification_email(
    "user@example.com",
    "Crypto Starter",
    "Investissement dans les cryptomonnaies majeures (BTC, ETH)",
    1.50,
    6000
)
```

---

### 6. ✔️ Email Vérification Email

**Fonction:** `send_verification_email(user_email, token)`

**Paramètres:**
- `user_email`: Email du destinataire
- `token`: Token de vérification

**Features:**
- Lien de vérification valide 24h
- Bouton CTA avec lien
- Option copier le lien
- Notice d'expiration

**Utilisation:**
```python
send_verification_email("user@example.com", "token_abc123xyz...")
```

---

## 🎨 Design Elements

### Couleurs TokenFlow
```css
Primaire: #4F46E5 (Indigo)
Primaire Dark: #7C3AED (Violet)
Gradient: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)
Fond: #F1F5F9 (Gris clair)
Succès: #10B981 (Vert)
Avertissement: #F59E0B (Ambre)
```

### Typographie
```css
Titre: 28px, font-weight 800
Sous-titre: 24px, font-weight 800
Corps: 16px, font-weight 400
Petit texte: 12-14px
```

### Responsive Breakpoints
```css
Max-width: 600px (Mobile + Desktop)
Padding: 40px (Desktop) / 20px (Mobile)
Border-radius: 12-16px
```

---

## 🔒 Sécurité

### Éléments de sécurité dans les emails:

1. **Avertissements:**
   - "Ne partagez jamais ce code"
   - "Cet email a été envoyé à ... via une connexion sécurisée"
   - "Si vous ne l'avez pas demandé, ignorez ce message"

2. **Icônes de sécurité:**
   - 🔐 Cadenas (sécurité)
   - ✓ Checkmark (succès)
   - ⏱️ Horloge (expiration)

3. **Footer de sécurité:**
   - Copyright © 2024 TokenFlow
   - "Plateforme fintech sécurisée"
   - Notice de connexion sécurisée

---

## 🧪 Tests

Tous les templates ont été testés pour:
- ✅ Génération correcte de codes OTP
- ✅ Expiration correcte des codes
- ✅ Présence de tous les éléments requis
- ✅ Design responsive mobile
- ✅ Éléments de sécurité
- ✅ Branding TokenFlow cohérent

**Résultat:** ✓ TOUS LES TESTS RÉUSSIS

---

## 📝 Intégration dans les routes

### Inscription
```python
@app.route("/inscription", methods=["GET", "POST"])
def inscription_page():
    # ...
    send_otp_email(email, otp, "inscription")  # ✓ Déjà intégré
```

### Connexion
```python
@app.route("/connexion", methods=["GET", "POST"])
def connexion_page():
    # ...
    send_otp_email(user.email, otp, "connexion")  # ✓ Déjà intégré
```

### Vérification OTP (Inscription)
```python
@app.route("/verify-otp/<action>", methods=["GET", "POST"])
def verify_otp_page(action):
    if action == "inscription":
        # ...
        send_verification_email(email, token)  # ✓ Déjà intégré
        send_welcome_email(username, email)  # ✓ Déjà intégré
```

### Réinitialisation Mot de Passe
```python
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password_page():
    # ...
    send_otp_email(email, otp, "reset_password")  # ✓ Déjà intégré
```

---

## 🚀 Prochaines étapes

Pour intégrer les emails de dépôt/retrait, ajouter dans les routes correspondantes:

### Dépôt
```python
send_deposit_confirmation_email(phone, amount, currency, reference, user.email)
```

### Retrait
```python
send_withdrawal_confirmation_email(phone, amount, currency, reference, user.email)
```

### Nouveau produit
```python
# Envoyer à tous les utilisateurs
for user in User.query.all():
    send_product_notification_email(
        user.email, 
        product.name, 
        product.description,
        product.daily_roi,
        product.min_amount
    )
```

---

## 📊 Statistiques

- **Templates créés:** 6
- **Fonctions d'envoi:** 6
- **Couleurs TokenFlow:** 4
- **Icônes utilisées:** 8+
- **Tests réussis:** 6/6
- **Code OTP:** 6 chiffres, expiration 10 minutes
- **Email vérification:** Valide 24 heures

---

## ✅ Checklist

- [x] Design professionnel TokenFlow
- [x] Responsive mobile
- [x] Éléments de sécurité
- [x] Branding cohérent
- [x] 6 templates d'emails
- [x] 6 fonctions d'envoi
- [x] Tests automatisés
- [x] Intégration dans les routes principales
- [x] Documentation complète

**Status:** ✅ PRÊT POUR LA PRODUCTION

---

*Dernière mise à jour: 6 juin 2026*
*Développé par: TokenFlow Team*
