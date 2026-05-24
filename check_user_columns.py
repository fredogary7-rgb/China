from app import db, app, User
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('user')]
    print('User columns:', columns)
    
    # Check if wallet_number and wallet_operator exist
    if 'wallet_number' in columns and 'wallet_operator' in columns:
        print('Wallet columns exist!')
    else:
        print('WARNING: Wallet columns missing!')
    
    # Check for users with wallet configured
    users = User.query.limit(5).all()
    print(f'\nFound {len(users)} users:')
    for u in users:
        print(f'  Phone: {u.phone}, Wallet: {u.wallet_number}, Operator: {u.wallet_operator}')