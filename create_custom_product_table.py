"""Script pour créer la table custom_product dans la base de données."""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Database connection
DB_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require')

# Parse the connection string
conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

# Create the custom_product table
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

conn.commit()
cursor.close()
conn.close()

print("✅ Table custom_product créée avec succès !")