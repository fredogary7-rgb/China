#!/usr/bin/env python3
"""Add bottom navigation to all required pages"""

import os

# Templates that need bottom navigation (excluding login, register, index, and retrait which is done)
templates_to_update = [
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
    'templates/admin_retraits.html',
    'templates/deposit.html'
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
        
        # Find the right place to insert (after last {% endblock %})
        last_endblock = content.rfind('{% endblock %}')
        if last_endblock == -1:
            print(f"⚠️  No endblock found in: {template_path}")
            continue
        
        insert_pos = last_endblock + len('{% endblock %}')
        
        # Insert the bottom nav
        before = content[:insert_pos]
        after = content[insert_pos:]
        
        # Make sure there's proper spacing
        new_content = before + '\n\n' + bottom_nav_html + '\n' + after
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Added bottom nav: {template_path}")
        updated_count += 1
    
    print(f"\n🎉 Added bottom navigation to {updated_count} templates!")

if __name__ == '__main__':
    add_bottom_nav()