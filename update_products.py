"""Script pour mettre à jour les produits avec le nouveau tableau de rendement progressif."""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Database connection
DB_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require')

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

# Créer la table custom_product si elle n'existe pas
cursor.execute("""
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
""")

# Supprimer les anciens produits
cursor.execute("DELETE FROM custom_product")

# Nouveaux produits basés sur le tableau fourni
nouveaux_produits = [
    # Paquet 1 - Immobilier
    {
        "name": "Pack Découverte",
        "description": "Idéal pour commencer - 40% de rendement mensuel",
        "price_usd": 25.0,
        "daily_revenue_usd": 0.33,
        "category": "realestate",
        "image_filename": "pack1.jpg"
    },
    # Paquet 2 - Immobilier
    {
        "name": "Pack Essentiel",
        "description": "Premier niveau de croissance - 40% de rendement mensuel",
        "price_usd": 70.0,
        "daily_revenue_usd": 0.93,
        "category": "realestate",
        "image_filename": "pack2.jpg"
    },
    # Paquet 3 - Materials
    {
        "name": "Pack Croissance",
        "description": "Accélérez vos gains - 40% de rendement mensuel",
        "price_usd": 160.0,
        "daily_revenue_usd": 2.13,
        "category": "materials",
        "image_filename": "pack3.jpg"
    },
    # Paquet 4 - Materials
    {
        "name": "Pack Expansion",
        "description": "Développez votre portefeuille - 40% de rendement mensuel",
        "price_usd": 340.0,
        "daily_revenue_usd": 4.53,
        "category": "materials",
        "image_filename": "pack4.jpg"
    },
    # Paquet 5 - Metaux Précieux
    {
        "name": "Pack Avancé",
        "description": "Niveau supérieur - 40% de rendement mensuel",
        "price_usd": 700.0,
        "daily_revenue_usd": 9.33,
        "category": "gold",
        "image_filename": "pack5.jpg"
    },
    # Paquet 6 - Metaux Précieux - Rendement 45%
    {
        "name": "Pack Premium",
        "description": "Rendement boosté - 45% de rendement mensuel",
        "price_usd": 1000.0,
        "daily_revenue_usd": 15.0,
        "category": "gold",
        "image_filename": "pack6.jpg"
    },
    # Paquet 7 - AI Trading
    {
        "name": "Pack Élite",
        "description": "Rendement premium - 45% de rendement mensuel",
        "price_usd": 1420.0,
        "daily_revenue_usd": 21.3,
        "category": "ai",
        "image_filename": "pack7.jpg"
    },
    # Paquet 8 - AI Trading - Rendement 51%
    {
        "name": "Pack Platinum",
        "description": "Rendement exceptionnel - 51% de rendement mensuel",
        "price_usd": 2860.0,
        "daily_revenue_usd": 48.62,
        "category": "ai",
        "image_filename": "pack8.jpg"
    },
    # Paquet 9 - VIP
    {
        "name": "Pack Diamond",
        "description": "Rendement diamant - 51% de rendement mensuel",
        "price_usd": 5740.0,
        "daily_revenue_usd": 97.58,
        "category": "vip",
        "image_filename": "pack9.jpg"
    },
    # Paquet 10 - VIP - Le plus élevé
    {
        "name": "Pack Ultimate",
        "description": "Le summum du rendement - 51% de rendement mensuel",
        "price_usd": 11500.0,
        "daily_revenue_usd": 195.5,
        "category": "vip",
        "image_filename": "pack10.jpg"
    }
]

# Insérer les nouveaux produits
for produit in nouveaux_produits:
    cursor.execute("""
        INSERT INTO custom_product 
        (name, description, price_usd, daily_revenue_usd, image_filename, category, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
    """, (
        produit["name"],
        produit["description"],
        produit["price_usd"],
        produit["daily_revenue_usd"],
        produit["image_filename"],
        produit["category"]
    ))

conn.commit()

# Vérifier l'insertion
cursor.execute("SELECT COUNT(*) FROM custom_product")
count = cursor.fetchone()[0]
print(f"✅ {count} produits ont été ajoutés avec succès !")

# Afficher un résumé
cursor.execute("SELECT name, price_usd, daily_revenue_usd FROM custom_product ORDER BY price_usd")
products = cursor.fetchall()
print("\n📊 Résumé des produits :")
print(f"{'Nom':<25} {'Prix (USD)':>12} {'Revenu/jour (USD)':>18}")
print("-" * 60)
for p in products:
    print(f"{p[0]:<25} ${p[1]:>10,.2f} ${p[2]:>16,.2f}")

cursor.close()
conn.close()

print("\n🎉 Mise à jour des produits terminée avec succès !")
print("Les nouveaux produits sont maintenant disponibles sur la plateforme.")