#!/usr/bin/env python3
"""Add bottom navigation bar to all required templates"""

import os

# Templates that need bottom navigation (excluding login, register, index)
templates_to_update = [
    'templates/retrait.html',
    'templates/produits_rapide.html',
    'templates/confirm_rapide.html',
    'templates/achats.html',
    'templates/team.html',
    'templates/profile.html',
    'templates/ai_chat.html',
    'templates/wallet_setup.html',
    'templates/support_chat.html',
    'templates/support_list.html',
    'templates/contact.html',
    'templates/rules.html',
    'templates/verify_otp.html',
    'templates/forgot_password.html',
    'templates/reset_password.html',
    'templates/admin_deposits.html',
    'templates/admin_retraits.html'
]

bottom_nav_html = '''
<nav class="bottom-nav">
  <a href="/dashboard" class="nav-item">
    <i class="fa-solid fa-house"></i>
    <span>Accueil</span>
  </a>
  <a href="/produits_rapide" class="nav-item">
    <i class="fa-solid fa-rocket"></i>
    <span>Investir</span>
  </a>
  <a href="/team" class="nav-item">
    <i class="fa-solid fa-users"></i>
    <span>Réseau</span>
  </a>
  <a href="/profile" class="nav-item">
    <i class="fa-solid fa-user"></i>
    <span>Profil</span>
  </a>
</nav>
'''

def add_bottom_nav():
    """Add bottom navigation to templates"""
    updated_count = 0
    
    for template_path in templates_to_update:
        if not os.path.exists(template_path):
            print(f"⚠️  File not found: {template_path}")
            continue
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if bottom nav already exists
        if 'class="bottom-nav"' in content:
            print(f"✅ Already has bottom nav: {template_path}")
            continue
        
        # Find the right place to insert (before last {% endblock %})
        # Look for patterns to determine where to insert
        insert_before = None
        
        # If it has {% block extra_js %}...{% endblock %}, insert after that
        if '{% block extra_js %}' in content:
            # Find the end of extra_js block
            extra_js_end = content.find('{% endblock %}', content.find('{% block extra_js %}'))
            if extra_js_end != -1:
                insert_before = extra_js_end + len('{% endblock %}')
        
        # If no extra_js or couldn't find it, insert before last {% endblock %}
        if insert_before is None:
            last_endblock = content.rfind('{% endblock %}')
            if last_endblock != -1:
                insert_before = last_endblock
        
        # If still not found, just append at the end
        if insert_before is None:
            insert_before = len(content)
        
        # Insert the bottom nav
        before = content[:insert_before]
        after = content[insert_before:]
        
        # Make sure there's a newline before the nav
        if before and not before.endswith('\n'):
            before += '\n'
        
        new_content = before + '\n' + bottom_nav_html + '\n' + after
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Added bottom nav: {template_path}")
        updated_count += 1
    
    print(f"\n🎉 Updated {updated_count} templates with bottom navigation!")

if __name__ == '__main__':
    add_bottom_nav()