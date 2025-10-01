#!/usr/bin/env python3
"""
Script to fix all @biro_required decorators and request.user.profile references
"""

import re

def fix_api_file():
    with open('api.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace @biro_required with auth=biro_auth in decorator
    # Pattern: @biro_router.method("/path", response=Schema)\n@biro_required
    pattern1 = r'(@biro_router\.[^,]+, response=[^)]+)\)\s*\n@biro_required'
    replacement1 = r'\1, auth=biro_auth)'
    content = re.sub(pattern1, replacement1, content)
    
    # Replace remaining standalone @biro_required
    content = content.replace('@biro_required\n', '')
    
    # Replace request.user.profile with request.auth.profile
    content = content.replace('request.user.profile', 'request.auth.profile')
    
    with open('api.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed all @biro_required decorators and request.user.profile references")

if __name__ == '__main__':
    fix_api_file()