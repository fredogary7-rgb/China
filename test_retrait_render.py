from app import app

with app.test_request_context():
    from flask import render_template
    html = render_template('retrait.html', user=None, solde_total=0, solde_retraitable=0)
    print('Rendered length:', len(html))
    print('First 1000 chars:')
    print(html[:1000])
    print('\n---\n')
    print('Last 1000 chars:')
    print(html[-1000:])