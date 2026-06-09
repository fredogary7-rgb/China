#!/usr/bin/env python3
"""Script pour mettre à jour la route confirmer_produit_rapide."""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''    # Look for custom product directly by ID (no offset)
    custom_product = CustomProduct.query.get(vip_id)
    if custom_product and custom_product.is_active:
        produit = {
            "id": vip_id,
            "nom": custom_product.name,
            "prix_usd": custom_product.price_usd,
            "revenu_journalier_usd": custom_product.daily_revenue_usd,
            "image": custom_product.image_filename or "ai.jpg",
            "is_custom": True,
            "description": custom_product.description or ""
        }
    else:
        flash("Produit introuvable.", "danger")
        return redirect(url_for("produits_rapide_page"))'''

new = '''    # 1. Chercher d\'abord dans les packs statiques PRODUITS_VIP
    produit = next((p.copy() for p in PRODUITS_VIP if p["id"] == vip_id), None)
    if produit:
        produit.setdefault("is_custom", False)
        produit.setdefault("description", "")
    else:
        # 2. Sinon chercher dans les produits custom de l\'admin
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
            return redirect(url_for("produits_rapide_page"))'''

if old in content:
    new_content = content.replace(old, new)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: Route confirmer_produit_rapide mise à jour!")
else:
    print("ERREUR: Ancien bloc non trouvé!")
