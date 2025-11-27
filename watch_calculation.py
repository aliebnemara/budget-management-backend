#!/usr/bin/env python3
"""
Background watcher for V2 calculation
Checks every 5 seconds and saves status to file
"""

import sqlite3
import time
import json
from datetime import datetime as dt

DB_PATH = "budget.db"
STATUS_FILE = "v2_status.json"

def get_status():
    """Get current V2 status"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM budget_effect_calculations_v2")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM budget_effect_calculations_v2 WHERE effect_type = 'weekend'")
        weekend = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM budget_effect_calculations_v2 WHERE effect_type = 'islamic_calendar'")
        islamic = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT branch_id) FROM budget_effect_calculations_v2")
        branches = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(business_date), MAX(business_date) FROM budget_effect_calculations_v2")
        date_range = cursor.fetchone()
        
        conn.close()
        
        return {
            'timestamp': dt.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total': total,
            'weekend': weekend,
            'islamic': islamic,
            'branches': branches,
            'date_range': date_range,
            'status': 'empty' if total == 0 else ('calculating' if total < 1000 else 'ready')
        }
    except Exception as e:
        return {'error': str(e), 'timestamp': dt.now().strftime('%Y-%m-%d %H:%M:%S')}

# Save initial status
status = get_status()
with open(STATUS_FILE, 'w') as f:
    json.dump(status, f, indent=2)

print(f"Initial status: {status['total']} records")
print(f"Status saved to: {STATUS_FILE}")
