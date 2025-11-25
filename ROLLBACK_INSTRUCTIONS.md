# 🔄 Rollback Instructions - Smart Ramadan System Integration

## If Integration Has Issues

If you encounter any problems with the Smart Ramadan System integration, you can quickly rollback to the previous working state.

### Option 1: Restore from Backup Files (Fastest)

```bash
cd /home/user/backend/Backend

# Restore the budget routes file
cp backups/budget_routes_before_smart.py src/api/routes/budget.py

# Restore the budget service file (if modified)
cp backups/budget_service_before_smart.py src/services/budget.py

# Remove the new smart_ramadan service file
rm src/services/smart_ramadan.py

# Restart backend
cd /home/user/backend/Backend
pkill -f "python3 -m uvicorn"
sleep 2
nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
```

### Option 2: Git Rollback (Alternative)

```bash
cd /home/user/backend

# View git log to confirm backup
git log --oneline

# Rollback to backup branch
git checkout backup-before-smart-integration

# Restart backend
cd /home/user/backend/Backend
pkill -f "python3 -m uvicorn"
sleep 2
nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
```

### Option 3: Manual File Comparison

```bash
# Compare current vs backup to see changes
cd /home/user/backend/Backend
diff src/api/routes/budget.py backups/budget_routes_before_smart.py

# If you see the differences you want to remove, use Option 1
```

## Verification After Rollback

1. **Check Backend Status:**
```bash
curl http://localhost:8000/api/brands-list
```

2. **Test Islamic Calendar Endpoint:**
```bash
# Should return data without errors
curl -X POST http://localhost:8000/api/islamic-calendar-effects \
  -H "Content-Type: application/json" \
  -d '{"branch_ids": [1], "compare_year": 2025}'
```

3. **Check Frontend:**
Open the frontend application and test the Islamic Calendar Effects page.

## What Was Changed

### Files Modified:
1. **NEW FILE**: `src/services/smart_ramadan.py` - Smart Ramadan System class
2. **MODIFIED**: `src/api/routes/budget.py` - Replaced hardcoded month logic with dynamic system

### Key Changes in budget.py:
- **Line 13**: Added `from src.services.smart_ramadan import SmartRamadanSystem`
- **Lines ~494-603**: Replaced hardcoded February, March, April logic with SmartRamadanSystem
- **Lines ~604-646**: Replaced hardcoded daily estimation with dynamic reference period selection

### Backup Locations:
- `/home/user/backend/Backend/backups/budget_routes_before_smart.py`
- `/home/user/backend/Backend/backups/budget_service_before_smart.py`
- Git branch: `backup-before-smart-integration`

## Contact

If you need help with rollback or encounter any issues:
1. Check backend logs: `tail -f /home/user/backend/Backend/backend.log`
2. Check for errors in the log output
3. Use the backup files to restore working state

---

**Date Created**: November 25, 2024  
**Integration Version**: Smart Ramadan System v1.0  
**Backup Status**: ✅ Complete
