from app import app
import re

with app.test_request_context():
    from flask import render_template
    html = render_template('retrait.html', user=None, solde_total=0, solde_retraitable=0)
    
    # Find body content
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
    if body_match:
        body_content = body_match.group(1)
        print('Body length:', len(body_content))
        print('\nFirst 1000 chars of body:')
        print(body_content[:1000])
        print('\n---\n')
        print('Middle 1000 chars of body:')
        mid = len(body_content) // 2
        print(body_content[mid:mid+1000])
    else:
        print('No body found!')