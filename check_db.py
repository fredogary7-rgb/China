import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(user)')
cols = cursor.fetchall()
print('Columns in user table:')
for c in cols:
    print(f'  {c[1]} ({c[2]})')
cursor.execute('SELECT phone, wallet_number, wallet_operator FROM user LIMIT 5')
rows = cursor.fetchall()
print('\nUser data:')
for r in rows:
    print(f'  Phone: {r[0]}, Wallet: {r[1]}, Operator: {r[2]}')
conn.close()