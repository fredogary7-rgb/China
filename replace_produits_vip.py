#!/usr/bin/env python3
"""Script pour remplacer PRODUITS_VIP dans app.py avec les nouveaux packs TokenFlow."""

import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Nouveau bloc PRODUITS_VIP
new_block = '''PRODUITS_VIP = [
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
]'''

# Remplacer le bloc PRODUITS_VIP avec regex (du début PRODUITS_VIP jusqu'au ] fermant)
pattern = r'PRODUITS_VIP = \[.*?\]'
new_content = re.sub(pattern, new_block, content, flags=re.DOTALL)

if new_content == content:
    print("ERREUR: Le remplacement n'a pas fonctionné!")
else:
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: PRODUITS_VIP remplacé avec succès!")

# Vérification
with open('app.py', 'r', encoding='utf-8') as f:
    verify = f.read()

if 'Pack 1' in verify and 'Pack 10' in verify and 'r40' in verify:
    print("VERIFICATION OK: Nouveaux packs présents dans app.py")
else:
    print("VERIFICATION FAILED!")
