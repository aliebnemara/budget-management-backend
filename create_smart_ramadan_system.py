#!/usr/bin/env python3
"""
Smart Dynamic Ramadan Detection and Estimation System

This system automatically:
1. Detects which months are affected by Ramadan/Eid in CY and BY
2. Determines the appropriate reference periods for estimation
3. Adapts to any Ramadan shift scenario without hardcoding

Author: AI Assistant
Date: 2024
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd

class SmartRamadanSystem:
    """
    Intelligent system that adapts to any Ramadan configuration
    """
    
    def __init__(self, config: dict):
        """
        Initialize with user-provided Ramadan configuration
        
        Args:
            config: Dictionary containing:
                - compare_year: int (e.g., 2025)
                - ramadan_CY: str (e.g., "2025-03-01")
                - ramadan_BY: str (e.g., "2026-02-18")
                - ramadan_daycount_CY: int (e.g., 30)
                - ramadan_daycount_BY: int (e.g., 30)
        """
        self.compare_year = config['compare_year']
        self.budget_year = config['compare_year'] + 1
        
        # Parse dates
        self.ramadan_start_CY = pd.to_datetime(config['ramadan_CY'])
        self.ramadan_start_BY = pd.to_datetime(config['ramadan_BY'])
        self.ramadan_days_CY = config['ramadan_daycount_CY']
        self.ramadan_days_BY = config['ramadan_daycount_BY']
        
        # Calculate Ramadan and Eid periods
        self.ramadan_end_CY = self.ramadan_start_CY + timedelta(days=self.ramadan_days_CY - 1)
        self.ramadan_end_BY = self.ramadan_start_BY + timedelta(days=self.ramadan_days_BY - 1)
        
        # Eid is 4 days after Ramadan ends
        self.eid_start_CY = self.ramadan_end_CY + timedelta(days=1)
        self.eid_end_CY = self.eid_start_CY + timedelta(days=3)
        self.eid_start_BY = self.ramadan_end_BY + timedelta(days=1)
        self.eid_end_BY = self.eid_start_BY + timedelta(days=3)
        
        print("🌙 Smart Ramadan System Initialized")
        print(f"\n📅 Comparison Year (CY): {self.compare_year}")
        print(f"   Ramadan: {self.ramadan_start_CY.strftime('%B %d')} - {self.ramadan_end_CY.strftime('%B %d, %Y')}")
        print(f"   Eid: {self.eid_start_CY.strftime('%B %d')} - {self.eid_end_CY.strftime('%B %d, %Y')}")
        print(f"\n📅 Budget Year (BY): {self.budget_year}")
        print(f"   Ramadan: {self.ramadan_start_BY.strftime('%B %d')} - {self.ramadan_end_BY.strftime('%B %d, %Y')}")
        print(f"   Eid: {self.eid_start_BY.strftime('%B %d')} - {self.eid_end_BY.strftime('%B %d, %Y')}")
    
    def get_affected_months(self) -> Dict[str, List[int]]:
        """
        Automatically detect which months are affected by Ramadan/Eid in both years
        
        Returns:
            Dictionary with 'CY' and 'BY' keys, each containing list of affected month numbers
        """
        cy_months = set()
        by_months = set()
        
        # Add months that contain any part of Ramadan or Eid in CY
        current = self.ramadan_start_CY
        while current <= self.eid_end_CY:
            cy_months.add(current.month)
            current += timedelta(days=1)
        
        # Add months that contain any part of Ramadan or Eid in BY
        current = self.ramadan_start_BY
        while current <= self.eid_end_BY:
            by_months.add(current.month)
            current += timedelta(days=1)
        
        result = {
            'CY': sorted(list(cy_months)),
            'BY': sorted(list(by_months))
        }
        
        print(f"\n🎯 Affected Months Detected:")
        print(f"   CY {self.compare_year}: {[self._month_name(m) for m in result['CY']]}")
        print(f"   BY {self.budget_year}: {[self._month_name(m) for m in result['BY']]}")
        
        return result
    
    def classify_day(self, date: pd.Timestamp, year_type: str) -> str:
        """
        Classify a specific day as 'ramadan', 'eid', or 'normal'
        
        Args:
            date: Date to classify
            year_type: 'CY' or 'BY'
        
        Returns:
            'ramadan', 'eid', or 'normal'
        """
        if year_type == 'CY':
            if self.ramadan_start_CY <= date <= self.ramadan_end_CY:
                return 'ramadan'
            elif self.eid_start_CY <= date <= self.eid_end_CY:
                return 'eid'
        else:  # BY
            if self.ramadan_start_BY <= date <= self.ramadan_end_BY:
                return 'ramadan'
            elif self.eid_start_BY <= date <= self.eid_end_BY:
                return 'eid'
        
        return 'normal'
    
    def get_month_structure(self, month: int, year_type: str) -> Dict[str, List[int]]:
        """
        Analyze the structure of a specific month - which days are Ramadan/Eid/Normal
        
        Args:
            month: Month number (1-12)
            year_type: 'CY' or 'BY'
        
        Returns:
            Dictionary with keys 'ramadan', 'eid', 'normal', each containing list of day numbers
        """
        year = self.compare_year if year_type == 'CY' else self.budget_year
        
        structure = {
            'ramadan': [],
            'eid': [],
            'normal': []
        }
        
        # Check each day of the month
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        
        for day in range(1, days_in_month + 1):
            date = pd.Timestamp(year=year, month=month, day=day)
            day_type = self.classify_day(date, year_type)
            structure[day_type].append(day)
        
        return structure
    
    def get_reference_period_for_day(self, by_month: int, by_day: int) -> Dict[str, any]:
        """
        SMART ALGORITHM: Determine the best reference period for a BY day
        
        This is the core intelligence that decides:
        - Which CY period to use as reference
        - Whether to use weekday averaging or direct value copy
        
        Args:
            by_month: Budget Year month number
            by_day: Budget Year day number
        
        Returns:
            Dictionary with:
                - method: 'weekday_average' or 'direct_copy'
                - source_period: Description of source period
                - source_month: Month to pull data from
                - source_day_type: 'ramadan', 'eid', or 'normal'
                - eid_day_mapping: If method is 'direct_copy', which CY Eid day to copy
        """
        by_date = pd.Timestamp(year=self.budget_year, month=by_month, day=by_day)
        by_day_type = self.classify_day(by_date, 'BY')
        
        result = {
            'by_date': by_date,
            'by_day_type': by_day_type,
            'method': None,
            'source_period': None,
            'source_months': [],
            'source_day_type': None,
            'eid_day_mapping': None
        }
        
        # RULE 1: Eid days use DIRECT COPY from CY Eid days
        if by_day_type == 'eid':
            # Calculate which Eid day (1st, 2nd, 3rd, 4th)
            eid_day_number = (by_date - self.eid_start_BY).days + 1
            
            # Find corresponding CY Eid day
            cy_eid_date = self.eid_start_CY + timedelta(days=eid_day_number - 1)
            
            result['method'] = 'direct_copy'
            result['source_period'] = f"CY Eid Day {eid_day_number}"
            result['source_months'] = [cy_eid_date.month]
            result['source_day_type'] = 'eid'
            result['eid_day_mapping'] = {
                'eid_day_number': eid_day_number,
                'cy_date': cy_eid_date,
                'cy_month': cy_eid_date.month,
                'cy_day': cy_eid_date.day
            }
        
        # RULE 2: Ramadan days use WEEKDAY AVERAGE from CY Ramadan period
        elif by_day_type == 'ramadan':
            # Find which CY months contain Ramadan
            cy_ramadan_months = []
            current = self.ramadan_start_CY
            while current <= self.ramadan_end_CY:
                if current.month not in cy_ramadan_months:
                    cy_ramadan_months.append(current.month)
                current += timedelta(days=1)
            
            result['method'] = 'weekday_average'
            result['source_period'] = f"CY Ramadan ({self.ramadan_start_CY.strftime('%b %d')} - {self.ramadan_end_CY.strftime('%b %d')})"
            result['source_months'] = cy_ramadan_months
            result['source_day_type'] = 'ramadan'
        
        # RULE 3: Normal days use WEEKDAY AVERAGE from CY normal days in same season
        else:
            # Find a CY month that:
            # 1. Is close to the BY month (same season)
            # 2. Has NO Ramadan or Eid days (pure normal month)
            
            cy_affected_months = self.get_affected_months()['CY']
            
            # Strategy: Look for nearby normal months
            # Start with same month in CY
            candidate_months = []
            
            # If BY month is not affected in CY, use same month
            if by_month not in cy_affected_months:
                candidate_months.append(by_month)
            
            # Otherwise, find nearest normal month
            else:
                # Look backwards and forwards for normal months
                for offset in range(1, 7):
                    for direction in [-1, 1]:
                        test_month = by_month + (offset * direction)
                        if 1 <= test_month <= 12 and test_month not in cy_affected_months:
                            candidate_months.append(test_month)
                            break
                    if candidate_months:
                        break
            
            if not candidate_months:
                # Fallback: Use any month that's not affected (prefer nearby)
                for m in range(1, 13):
                    if m not in cy_affected_months:
                        candidate_months.append(m)
                        break
            
            result['method'] = 'weekday_average'
            result['source_period'] = f"CY {self._month_name(candidate_months[0])} (Normal days)"
            result['source_months'] = candidate_months
            result['source_day_type'] = 'normal'
        
        return result
    
    def generate_estimation_plan(self) -> Dict[int, Dict[int, dict]]:
        """
        Generate a complete estimation plan for all affected BY months
        
        Returns:
            Nested dictionary: {month: {day: reference_info}}
        """
        affected_months = self.get_affected_months()['BY']
        estimation_plan = {}
        
        print(f"\n📋 Generating Estimation Plan for BY {self.budget_year}:")
        print("=" * 80)
        
        for month in affected_months:
            estimation_plan[month] = {}
            month_structure = self.get_month_structure(month, 'BY')
            
            print(f"\n📅 {self._month_name(month)} {self.budget_year}:")
            print(f"   Ramadan days: {len(month_structure['ramadan'])} days")
            print(f"   Eid days: {len(month_structure['eid'])} days")
            print(f"   Normal days: {len(month_structure['normal'])} days")
            
            # Get reference for each day
            import calendar
            days_in_month = calendar.monthrange(self.budget_year, month)[1]
            
            for day in range(1, days_in_month + 1):
                reference = self.get_reference_period_for_day(month, day)
                estimation_plan[month][day] = reference
            
            # Print summary by day type
            self._print_month_summary(month, estimation_plan[month])
        
        return estimation_plan
    
    def _print_month_summary(self, month: int, day_references: Dict[int, dict]):
        """Print a readable summary of the estimation plan for a month"""
        
        # Group days by reference source
        groups = {}
        for day, ref in day_references.items():
            key = (ref['method'], ref['source_period'], ref['by_day_type'])
            if key not in groups:
                groups[key] = []
            groups[key].append(day)
        
        print(f"\n   Estimation Strategy:")
        for (method, source, day_type), days in sorted(groups.items(), key=lambda x: min(x[1])):
            day_ranges = self._format_day_ranges(days)
            emoji = "🌙" if day_type == "ramadan" else "🎉" if day_type == "eid" else "🍽️"
            print(f"   {emoji} Days {day_ranges}: {method.upper()}")
            print(f"      └─ Source: {source}")
    
    def _format_day_ranges(self, days: List[int]) -> str:
        """Format a list of days into readable ranges (e.g., '1-5, 8-10, 15')"""
        if not days:
            return ""
        
        days = sorted(days)
        ranges = []
        start = days[0]
        end = days[0]
        
        for i in range(1, len(days)):
            if days[i] == end + 1:
                end = days[i]
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = days[i]
                end = days[i]
        
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
        
        return ", ".join(ranges)
    
    def _month_name(self, month: int) -> str:
        """Get month name from number"""
        import calendar
        return calendar.month_name[month]


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("🧠 SMART RAMADAN ESTIMATION SYSTEM - DEMONSTRATION")
    print("=" * 80)
    
    # Example 1: 2025-2026 Configuration (Current scenario)
    print("\n\n📌 SCENARIO 1: Ramadan 2025-2026 (Current)")
    print("─" * 80)
    config_2025 = {
        'compare_year': 2025,
        'ramadan_CY': '2025-03-01',
        'ramadan_BY': '2026-02-18',
        'ramadan_daycount_CY': 30,
        'ramadan_daycount_BY': 30
    }
    
    system_2025 = SmartRamadanSystem(config_2025)
    affected = system_2025.get_affected_months()
    plan_2025 = system_2025.generate_estimation_plan()
    
    # Example 2: 2026-2027 Configuration (Next year - Ramadan shifts further back)
    print("\n\n" + "=" * 80)
    print("📌 SCENARIO 2: Ramadan 2026-2027 (Next Year)")
    print("─" * 80)
    print("Note: Ramadan shifts ~11 days earlier, so April won't be affected!")
    
    config_2026 = {
        'compare_year': 2026,
        'ramadan_CY': '2026-02-18',
        'ramadan_BY': '2027-02-07',
        'ramadan_daycount_CY': 30,
        'ramadan_daycount_BY': 30
    }
    
    system_2026 = SmartRamadanSystem(config_2026)
    affected_2026 = system_2026.get_affected_months()
    plan_2026 = system_2026.generate_estimation_plan()
    
    print("\n\n" + "=" * 80)
    print("✅ SYSTEM DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("✓ Automatic detection of affected months")
    print("✓ Dynamic day classification (Ramadan/Eid/Normal)")
    print("✓ Intelligent reference period selection")
    print("✓ Adapts to any Ramadan shift scenario")
    print("✓ No hardcoded month numbers")
    print("=" * 80)
