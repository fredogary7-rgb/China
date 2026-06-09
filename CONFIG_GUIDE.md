# 🔧 Guide de Configuration TokenFlow

## 🚨 Erreurs détectées

### 1. 🔑 Erreur VAPID Keys
**Erreur:** `'Vapid02' object has no attribute 'private_raw'`
- ✅ **CORRIGÉ** - La fonction `_generate_vapid_keys()` utilise maintenant la bonne API

### 2. 📧 Erreur Authentification SMTP Gmail  
**Erreur:** `Username and Password not accepted (BadCredentials)`
- **Cause:** Le mot de passe d'application Gmail est incorrect ou non configuré
- **Solution:** Voir section **Configuration Gmail** ci-dessous

### 3. 🔐 OAuth Google/Apple manquant
**Erreur:** Variables d'environnement non configurées
- **Solution:** Voir section **Configuration OAuth** ci-dessous

---

## 📧 Configuration Gmail SMTP

Pour envoyer des emails via Gmail, vous DEVEZ utiliser un **mot de passe d'application**, pas votre mot de passe normal.

### Étapes :

1. **Activer l'authentification en deux étapes:**
   - Accédez à: https://myaccount.google.com/security
   - Cliquez sur "Authentification à deux facteurs"
   - Suivez les instructions

2. **Générer un mot de passe d'application:**
   - Accédez à: https://myaccount.google.com/apppasswords
   - Sélectionnez: **Mail** et **Windows Computer** (ou votre plateforme)
   - Google génère un mot de passe de **16 caractères**
   - **Copiez ce mot de passe** (c'est important!)

3. **Configurer le `.env`:**
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=votre_email@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx
   EMAIL_FROM=TokenFlow <support@flowtoken.uk>
   ```

   ⚠️ **IMPORTANT:** 
   - Ne pas ajouter de guillemets autour du mot de passe
   - Les 4 espaces dans le mot de passe sont normaux (c'est Google qui l'envoie comme ça)
   - Si ça ne marche pas, essayez sans les espaces: `xxxxxxxxxxxxxxxxxx`

4. **Vérifier la configuration:**
   ```python
   # Depuis la console Python
   from app import send_email_smtp
   success, error = send_email_smtp(
       "votre_email@gmail.com",
       "Test TokenFlow",
       "<h1>Test</h1>",
       "Test email"
   )
   print(f"Success: {success}, Error: {error}")
   ```

### Troubleshooting:

**❌ Erreur: "BadCredentials"**
- Le mot de passe d'application est incorrect
- Solution: Régénérez-le à https://myaccount.google.com/apppasswords
- Supprimez l'ancien mot de passe et créez-en un nouveau

**❌ Erreur: "Account not configured"**
- L'authentification en deux étapes n'est pas activée
- Solution: Activez-la à https://myaccount.google.com/security

**❌ Erreur: "Less secure apps"**
- Cette restriction n'existe plus pour Gmail
- Solution: Utilisez obligatoirement un mot de passe d'application

---

## 🔑 VAPID Keys (Web Push)

Les clés VAPID permettent l'envoi de notifications push web.

### Configuration:

**Option 1: Génération automatique**
```bash
# Les clés sont automatiquement générées lors du premier appel
# et stockées dans les variables d'environnement
```

**Option 2: Utiliser des clés existantes**
```
# Dans .env
VAPID_PRIVATE_KEY=votre_private_key
VAPID_PUBLIC_KEY=votre_public_key
```

### Générer manuellement:

```bash
# Installez py-vapid
pip install py-vapid

# Générez les clés
python -c "
from py_vapid import Vapid02
import base64

vapid = Vapid02()
vapid.generate_keys()

private = base64.urlsafe_b64encode(vapid.private_key.to_string()).rstrip(b'=').decode()
public = base64.urlsafe_b64encode(b'\x04' + vapid.public_key.to_string()).rstrip(b'=').decode()

print(f'VAPID_PRIVATE_KEY={private}')
print(f'VAPID_PUBLIC_KEY={public}')
"
```

---

## 🔐 Configuration OAuth

### Google OAuth 2.0

1. **Créer une application Google:**
   - Allez à: https://console.cloud.google.com/
   - Créez un nouveau projet
   - Allez à "APIs & Services" → "Credentials"
   - Créez des "OAuth 2.0 Client IDs" (type: Web application)

2. **Configurer les URIs de redirection:**
   ```
   Authorized redirect URIs:
   - http://localhost:5000/auth/google/callback
   - https://flowtoken.uk/auth/google/callback
   ```

3. **Récupérer les credentials:**
   - Client ID: `GOOGLE_CLIENT_ID`
   - Client Secret: `GOOGLE_CLIENT_SECRET`

4. **Ajouter au `.env`:**
   ```
   GOOGLE_CLIENT_ID=xxxxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxx
   ```

### Apple OAuth

1. **Créer une application Apple:**
   - Allez à: https://developer.apple.com/account
   - Créez un nouvel App ID
   - Activez "Sign in with Apple"

2. **Créer une clé de service:**
   - Allez à "Keys"
   - Créez une nouvelle clé avec "Sign in with Apple"

3. **Récupérer les informations:**
   - Team ID: `APPLE_TEAM_ID`
   - Client ID: `APPLE_CLIENT_ID`  
   - Key ID: `APPLE_KEY_ID`
   - Private Key: Téléchargez le fichier `.p8`

4. **Ajouter au `.env`:**
   ```
   APPLE_TEAM_ID=xxxxxxxxxx
   APPLE_CLIENT_ID=com.flowtoken.app
   APPLE_KEY_ID=xxxxxxxxxx
   APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...
   ```

---

## ✅ Template `.env` complet

```env
# ========== CONFIGURATION SERVEUR ==========
FLASK_ENV=production
SERVER_NAME=flowtoken.uk
PREFERRED_URL_SCHEME=https
DEBUG=False

# ========== BASE DE DONNÉES ==========
DATABASE_URL=postgresql://user:password@host:port/dbname

# ========== EMAIL (SMTP Gmail) ==========
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_FROM=TokenFlow <support@flowtoken.uk>

# ========== NOTIFICATIONS PUSH ==========
VAPID_PRIVATE_KEY=
VAPID_PUBLIC_KEY=

# ========== OAUTH GOOGLE ==========
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://flowtoken.uk/auth/google/callback

# ========== OAUTH APPLE ==========
APPLE_TEAM_ID=
APPLE_CLIENT_ID=
APPLE_KEY_ID=
APPLE_PRIVATE_KEY=

# ========== PAIEMENTS & APIs ==========
MONEYFUSION_API_KEY=
MONEYFUSION_API_URL=
SOLEAS_API_KEY=
SOLEAS_API_URL=
SOLEAS_WEBHOOK_SECRET=

# ========== SÉCURITÉ ==========
SECRET_KEY=votre_cle_secrete_aleeatoire
JWT_SECRET_KEY=votre_jwt_secret
```

---

## 🧪 Vérification des configurations

### Script de vérification:

```python
#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()

checks = {
    "SMTP_SERVER": os.getenv('SMTP_SERVER'),
    "SMTP_PORT": os.getenv('SMTP_PORT'),
    "SMTP_USER": os.getenv('SMTP_USER'),
    "SMTP_PASSWORD": "***" if os.getenv('SMTP_PASSWORD') else "VIDE",
    "EMAIL_FROM": os.getenv('EMAIL_FROM'),
    "VAPID_PRIVATE_KEY": "OK" if os.getenv('VAPID_PRIVATE_KEY') else "VIDE",
    "VAPID_PUBLIC_KEY": "OK" if os.getenv('VAPID_PUBLIC_KEY') else "VIDE",
    "GOOGLE_CLIENT_ID": "OK" if os.getenv('GOOGLE_CLIENT_ID') else "VIDE",
    "GOOGLE_CLIENT_SECRET": "OK" if os.getenv('GOOGLE_CLIENT_SECRET') else "VIDE",
    "APPLE_TEAM_ID": "OK" if os.getenv('APPLE_TEAM_ID') else "VIDE",
    "APPLE_CLIENT_ID": "OK" if os.getenv('APPLE_CLIENT_ID') else "VIDE",
    "APPLE_KEY_ID": "OK" if os.getenv('APPLE_KEY_ID') else "VIDE",
}

print("\n📋 Vérification des configurations:\n")
for key, value in checks.items():
    status = "✅" if value and value != "VIDE" else "⚠️ "
    print(f"{status} {key}: {value}")
```

### Exécuter la vérification:

```bash
python check_config.py
```

---

## 🚀 Prochaines étapes

1. **✅ Configurer le `.env` avec les valeurs correctes**
2. **✅ Redémarrer l'application Flask**
3. **✅ Tester l'envoi d'emails:**
   ```bash
   curl -X POST http://localhost:5000/test-email -H "Content-Type: application/json" -d '{"email":"test@example.com"}'
   ```
4. **✅ Vérifier les notifications push**
5. **✅ Tester OAuth Google et Apple**

---

## 📞 Support

Si vous rencontrez des problèmes:

1. Vérifiez les logs de l'application: `Traceback complet:`
2. Consultez la section Troubleshooting ci-dessus
3. Vérifiez les variables d'environnement: `echo $SMTP_PASSWORD`
4. Testez les connexions directement en Python

---

**Dernière mise à jour:** 6 juin 2026
**Version:** 1.0
