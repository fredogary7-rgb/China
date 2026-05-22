#!/usr/bin/env python3
"""Génère les clés VAPID pour les notifications push Web Push API."""

from py_vapid import Vapid
import base64

def generate_vapid_keys():
    """Génère une paire de clés VAPID pour Web Push."""
    vapid = Vapid()
    
    # Private key (32 bytes) -> base64url
    private_key = base64.urlsafe_b64encode(vapid.private_raw).rstrip(b'=').decode('ascii')
    
    # Public key (65 bytes with 0x04 prefix) -> base64url
    public_key_raw = vapid.public_raw
    if len(public_key_raw) == 64:
        public_key_raw = b'\x04' + public_key_raw
    elif len(public_key_raw) == 65 and public_key_raw[0] != 0x04:
        public_key_raw = b'\x04' + public_key_raw[1:]
    
    public_key = base64.urlsafe_b64encode(public_key_raw).rstrip(b'=').decode('ascii')
    
    return private_key, public_key

if __name__ == '__main__':
    private_key, public_key = generate_vapid_keys()
    
    print("=" * 60)
    print("🔑 Clés VAPID générées avec succès !")
    print("=" * 60)
    print(f"VAPID_PRIVATE_KEY={private_key}")
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print("=" * 60)
    print("\n📝 Ajoutez ces lignes à votre fichier .env :")
    print(f"   VAPID_PRIVATE_KEY={private_key}")
    print(f"   VAPID_PUBLIC_KEY={public_key}")
    print("\n⚠️  IMPORTANT: Gardez VAPID_PRIVATE_KEY secret !")
    print("=" * 60)