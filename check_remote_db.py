import psycopg2

DB_URL = "postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require"

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Get custom_product columns
cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'custom_product' ORDER BY ordinal_position")
cols = cursor.fetchall()
print("\ncustom_product columns:")
for col in cols:
    print(f"  {col[0]}: {col[1]}")

# Get custom_product data
cursor.execute("SELECT id, name, category FROM custom_product")
products = cursor.fetchall()
print("\nProducts:")
for p in products:
    print(f"  ID: {p[0]}, Name: {p[1]}, Category: {p[2]}")

conn.close()