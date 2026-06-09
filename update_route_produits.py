#!/usr/bin/env python3
"""Script pour mettre à jour la route produits_rapide_page."""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_route = '''@app.route("/produits_rapide")
@login_required
def produits_rapide_page():
    phone = get_logged_in_user_phone()
    user = User.query.filter_by(phone=phone).first()

    # Get active custom products from database (ONLY custom products, no default PRODUITS_VIP)
    custom_products_db = CustomProduct.query.filter_by(is_active=True).order_by(CustomProduct.created_at.desc()).all()
    
    # Convert custom products to same format as before
    custom_products = []
    for p in custom_products_db:
        custom_products.append({
            "id": p.id,  # Direct ID from database
            "nom": p.name,
            "prix_usd": p.price_usd,
            "revenu_journalier_usd": p.daily_revenue_usd,
            "image": p.image_filename or "ai.jpg",
            "is_custom": True,
            "category": p.category or "stable",
            "description": p.description or ""
        })

    return render_template(
        "produits_rapide.html",
        user=user,
        produits=custom_products
    )'''

new_route = '''@app.route("/produits_rapide")
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

    return render_template(
        "produits_rapide.html",
        user=user,
        produits=produits
    )'''

if old_route in content:
    new_content = content.replace(old_route, new_route)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: Route produits_rapide_page mise à jour!")
else:
    print("ERREUR: Ancien bloc de route non trouvé!")
    # Essayons une correspondance partielle pour diagnostiquer
    if 'def produits_rapide_page():' in content:
        print("La fonction existe bien dans le fichier.")
    else:
        print("La fonction n'existe pas!")
