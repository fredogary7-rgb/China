#!/usr/bin/env python3
"""Remove duplicate bottom navigation bars from templates (keep only base.html version)"""

import os

# Templates that may have duplicate bottom nav
templates_to_check = [
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
    'templates/admin_retraits.html',
    'templates/deposit.html'
]

def remove_duplicate_navs():
    """Remove duplicate bottom navigation from templates"""
    updated_count = 0
    
    for template_path in templates_to_check:
        if not os.path.exists(template_path):
            print(f"⚠️  File not found: {template_path}")
            continue
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if template has bottom-nav
        if 'class="bottom-nav"' not in content:
            print(f"✅ No bottom nav in: {template_path}")
            continue
        
        # Remove the bottom-nav block
        # Find the nav block
        start_idx = content.find('<nav class="bottom-nav">')
        if start_idx == -1:
            print(f"✅ No bottom nav in: {template_path}")
            continue
        
        end_idx = content.find('</nav>', start_idx)
        if end_idx == -1:
            print(f"⚠️  Malformed nav in: {template_path}")
            continue
        
        end_idx += len('</nav>')
        
        # Remove the nav block
        new_content = content[:start_idx] + content[end_idx:]
        
        # Clean up extra whitespace
        new_content = new_content.replace('\n\n\n', '\n\n')
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Removed duplicate nav from: {template_path}")
        updated_count += 1
    
    print(f"\n🎉 Removed duplicate navigation from {updated_count} templates!")
    print("The bottom navigation in base.html will now be used for all pages.")

if __name__ == '__main__':
    remove_duplicate_navs()