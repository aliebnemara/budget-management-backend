# Audit Tracking - Quick Reference Guide

## 🎯 Overview

Brand and Branch tables now automatically track:
- ✅ Who created each record (`added_by`)
- ✅ When it was created (`added_at`)
- ✅ Who last edited it (`edited_by`)
- ✅ When it was last edited (`edited_at`)
- ✅ Who soft-deleted it (`deleted_by`)
- ✅ When it was soft-deleted (`deleted_at`)

---

## 📋 Quick Field Reference

| Field | Purpose | Auto-populated? | When Updated |
|-------|---------|-----------------|--------------|
| `added_at` | Creation timestamp | ✅ Yes (DB) | On INSERT |
| `added_by` | Creator user ID | ⚙️ API | On INSERT |
| `edited_at` | Last edit timestamp | ✅ Yes (DB) | On UPDATE |
| `edited_by` | Last editor user ID | ⚙️ API | On UPDATE |
| `deleted_at` | Soft delete timestamp | ⚙️ API | On soft delete |
| `deleted_by` | Deleter user ID | ⚙️ API | On soft delete |

---

## 💡 Usage Examples

### Creating Records

```python
# Brand creation
new_brand = Brand(
    id=brand_id,
    name="Brand Name",
    added_by=current_user.get("id")  # ← Add this line
)
```

```python
# Branch creation
new_branch = Branch(
    id=branch_id,
    name="Branch Name",
    brand_id=brand_id,
    added_by=current_user.get("id")  # ← Add this line
)
```

### Updating Records

```python
# Update any record
brand.name = "New Name"
brand.edited_by = current_user.get("id")  # ← Add these lines
brand.edited_at = datetime.now()          # ← Add these lines
```

### Soft Deleting Records

```python
# Soft delete
brand.is_deleted = True
brand.deleted_at = datetime.now()          # ← Add these lines
brand.deleted_by = current_user.get("id")  # ← Add these lines
```

### Restoring Soft-Deleted Records

```python
# Restore
brand.is_deleted = False
brand.deleted_at = None                    # ← Clear deletion tracking
brand.deleted_by = None                    # ← Clear deletion tracking
brand.edited_by = current_user.get("id")   # ← Track restoration
brand.edited_at = datetime.now()           # ← Track restoration
```

---

## 🔍 Common Queries

### Get all records created by a user

```python
brands = dbs.query(Brand).filter(Brand.added_by == user_id).all()
```

### Get all soft-deleted records

```python
deleted = dbs.query(Brand).filter(
    Brand.is_deleted == True,
    Brand.deleted_at.isnot(None)
).all()
```

### Get recently modified records (last 7 days)

```python
from datetime import datetime, timedelta

week_ago = datetime.now() - timedelta(days=7)
recent = dbs.query(Brand).filter(Brand.edited_at >= week_ago).all()
```

### Get audit trail for specific record

```python
brand = dbs.query(Brand).filter(Brand.id == brand_id).first()

print(f"Created: {brand.added_at} by User {brand.added_by}")
print(f"Edited: {brand.edited_at} by User {brand.edited_by}")

if brand.is_deleted:
    print(f"Deleted: {brand.deleted_at} by User {brand.deleted_by}")
```

---

## ⚠️ Important Notes

### Required Import

```python
from datetime import datetime  # ← Add to top of file
```

### Current User Access

All endpoints should use `current_user: dict = Depends(get_current_user)`:

```python
@brandsRouter.post("/")
def create_brand(
    brand_data: BrandCreate, 
    current_user: dict = Depends(get_current_user)  # ← Required
):
    user_id = current_user.get("id")  # ← Extract user ID
```

### Database Auto-Population

The following fields are **automatically** populated by the database:
- `added_at` (on INSERT)
- `edited_at` (on UPDATE)

You **do not** need to manually set these unless you want to override the default behavior.

---

## 🧪 Testing Your Changes

### Run the test suite

```bash
cd /home/user/backend/Backend
python tests/test_audit_tracking.py
```

### Verify in database

```sql
-- Check brand audit fields
SELECT 
    id, name, added_at, added_by, edited_at, edited_by, 
    deleted_at, deleted_by, is_deleted
FROM brand 
WHERE id = YOUR_BRAND_ID;

-- Check branch audit fields
SELECT 
    id, name, added_at, added_by, edited_at, edited_by, 
    deleted_at, deleted_by, is_deleted
FROM branch 
WHERE id = YOUR_BRANCH_ID;
```

---

## 📊 Checklist for New Endpoints

When creating new API endpoints that modify Brand or Branch:

- [ ] Import `datetime` module
- [ ] Add `current_user: dict = Depends(get_current_user)` parameter
- [ ] On CREATE: Set `added_by = current_user.get("id")`
- [ ] On UPDATE: Set `edited_by` and `edited_at`
- [ ] On SOFT DELETE: Set `deleted_by` and `deleted_at`
- [ ] On RESTORE: Clear `deleted_by` and `deleted_at`, set `edited_by` and `edited_at`

---

## 🚀 Quick Start

1. **Migration completed**: ✅ Database schema updated
2. **Models updated**: ✅ SQLAlchemy models include audit fields
3. **API routes updated**: ✅ All CRUD operations track audit info
4. **Tests passing**: ✅ Comprehensive test suite validated
5. **Server restarted**: ✅ Backend running with new models

**You're ready to use audit tracking!**

---

## 📞 Need Help?

- **Full Documentation**: See `AUDIT_TRACKING_DOCUMENTATION.md`
- **Migration Script**: `migrations/add_audit_fields.py`
- **Test Suite**: `tests/test_audit_tracking.py`
- **Database Models**: `src/db/dbtables.py`
- **API Routes**: `src/api/routes/brands.py`

---

**Last Updated**: November 19, 2025  
**Status**: ✅ Production Ready
