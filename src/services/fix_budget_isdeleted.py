#!/usr/bin/env python3
"""Add is_deleted fields to budget.py response"""

with open('budget.py', 'r') as f:
    content = f.read()

# Replace brand_obj dictionary
old_brand_dict = '''            brand_obj = {
                "brand_id": brand.id,
                "brand_name": brand.name,
                "branches": []
            }'''

new_brand_dict = '''            brand_obj = {
                "brand_id": brand.id,
                "brand_name": brand.name,
                "is_deleted": brand.is_deleted if hasattr(brand, 'is_deleted') else False,
                "branches": []
            }'''

content = content.replace(old_brand_dict, new_brand_dict)

# Replace branch dictionary
old_branch_dict = '''                brand_obj["branches"].append({
                    "branch_id": br.id,
                    "branch_name": br.name,
                    "months": branch_months
                })'''

new_branch_dict = '''                brand_obj["branches"].append({
                    "branch_id": br.id,
                    "branch_name": br.name,
                    "is_deleted": br.is_deleted if hasattr(br, 'is_deleted') else False,
                    "months": branch_months
                })'''

content = content.replace(old_branch_dict, new_branch_dict)

with open('budget.py', 'w') as f:
    f.write(content)

print("✅ Successfully added is_deleted fields to budget.py")
