#!/usr/bin/env python3
"""
LLMDB Bitemporal Demonstration

This example demonstrates LLMDB's bitemporal capabilities by simulating
a real-world scenario: tracking employee salary changes over time with
corrections and audit trails.

Features demonstrated:
- Valid time vs Transaction time
- Historical queries (AS OF VALID)
- Audit trails and corrections
- Time-travel queries
- Complete version history
"""

import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from llmdb import KV
from llmdb.temporal_key import Key
from llmdb.kv._codec import JSONValue


def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_currency(amount: float) -> str:
    """Format currency for display"""
    return f"${amount:,.2f}"


class EmployeeTracker:
    """Demonstrates bitemporal employee data tracking"""
    
    def __init__(self, db_path: str):
        self.db = KV(db_path)
        
    def add_employee_record(self, employee_id: str, data: Dict[str, Any], 
                          valid_from: datetime) -> None:
        """Add an employee record with specific valid time"""
        key = Key(
            partition=0,
            user_key=f"employee:{employee_id}",
            valid_from=int(valid_from.timestamp() * 1_000_000)  # microseconds
        )
        self.db.put(key, JSONValue(payload=data))
        
    def get_current_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get current employee record"""
        key = Key(partition=0, user_key=f"employee:{employee_id}")
        result = self.db.get(key)
        return result.payload if result else None
        
    def get_employee_history(self, employee_id: str) -> List[tuple]:
        """Get all versions of an employee record"""
        versions = []
        prefix = f"employee:{employee_id}".encode()
        
        for key, value in self.db.items():
            if key.user_key.startswith(prefix):
                valid_time = datetime.fromtimestamp(key.valid_from / 1_000_000)
                versions.append((valid_time, key.tx_id, value.payload))
                
        return sorted(versions, key=lambda x: x[0])  # Sort by valid time
        
    def print_employee_summary(self, employee_id: str):
        """Print a summary of an employee's record history"""
        print(f"\n{'='*60}")
        print(f"EMPLOYEE RECORD HISTORY: {employee_id}")
        print(f"{'='*60}")
        
        history = self.get_employee_history(employee_id)
        if not history:
            print("No records found.")
            return
            
        print(f"{'Valid From':<20} {'Tx ID':<8} {'Salary':<12} {'Department':<15} {'Status'}")
        print("-" * 80)
        
        for valid_time, tx_id, data in history:
            salary = format_currency(data.get('salary', 0))
            department = data.get('department', 'Unknown')[:14]
            status = data.get('status', 'Unknown')
            
            print(f"{format_datetime(valid_time):<20} {tx_id:<8} {salary:<12} {department:<15} {status}")


def main():
    """Run the bitemporal demonstration"""
    
    # Create temporary database
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "temporal_demo.db")
        tracker = EmployeeTracker(db_path)
        
        print("LLMDB Bitemporal Data Demonstration")
        print("=" * 50)
        print("\nScenario: Employee Salary Tracking with Corrections\n")
        
        # Employee Alice starts working
        start_date = datetime(2022, 1, 1, 9, 0, 0)
        print(f"📅 {format_datetime(start_date)}: Alice hired as Software Engineer")
        tracker.add_employee_record("alice", {
            "name": "Alice Johnson",
            "salary": 75000,
            "department": "Engineering",
            "status": "Active",
            "hire_date": "2022-01-01"
        }, start_date)
        
        # Mid-year performance review and raise
        review_date = datetime(2022, 6, 15, 14, 30, 0)
        print(f"📅 {format_datetime(review_date)}: Alice receives performance raise")
        tracker.add_employee_record("alice", {
            "name": "Alice Johnson",
            "salary": 82000,  # 7k raise
            "department": "Engineering",
            "status": "Active",
            "hire_date": "2022-01-01",
            "last_review": "2022-06-15",
            "performance_rating": "Exceeds Expectations"
        }, review_date)
        
        # Promotion to Senior Engineer
        promotion_date = datetime(2023, 1, 1, 10, 0, 0)
        print(f"📅 {format_datetime(promotion_date)}: Alice promoted to Senior Engineer")
        tracker.add_employee_record("alice", {
            "name": "Alice Johnson",
            "salary": 95000,  # Promotion raise
            "department": "Engineering",
            "status": "Active",
            "title": "Senior Software Engineer",
            "hire_date": "2022-01-01",
            "promotion_date": "2023-01-01",
            "last_review": "2022-06-15",
            "performance_rating": "Exceeds Expectations"
        }, promotion_date)
        
        # Team lead promotion
        lead_date = datetime(2023, 8, 1, 9, 0, 0)
        print(f"📅 {format_datetime(lead_date)}: Alice becomes Team Lead")
        tracker.add_employee_record("alice", {
            "name": "Alice Johnson",
            "salary": 110000,  # Management raise
            "department": "Engineering",
            "status": "Active",
            "title": "Engineering Team Lead",
            "hire_date": "2022-01-01",
            "promotion_date": "2023-08-01",
            "last_review": "2022-06-15",
            "performance_rating": "Exceeds Expectations",
            "reports": 5
        }, lead_date)
        
        # HR discovers a payroll error - Alice's June raise was entered incorrectly
        correction_date = datetime.now()
        print(f"📅 {format_datetime(correction_date)}: HR discovers payroll error in June raise")
        print("   Correcting: Should have been $85,000, not $82,000")
        
        # Correct the historical record
        tracker.add_employee_record("alice", {
            "name": "Alice Johnson",
            "salary": 85000,  # Corrected amount
            "department": "Engineering", 
            "status": "Active",
            "hire_date": "2022-01-01",
            "last_review": "2022-06-15",
            "performance_rating": "Exceeds Expectations",
            "payroll_correction": "2024-07-21"  # Note the correction
        }, review_date)  # Same valid time, but new transaction time
        
        # Show the complete audit trail
        tracker.print_employee_summary("alice")
        
        # Demonstrate temporal queries
        print(f"\n{'='*60}")
        print("TEMPORAL QUERY EXAMPLES")
        print(f"{'='*60}")
        
        # What was Alice's salary in July 2022?
        july_2022 = datetime(2022, 7, 15)
        print(f"\n🕐 Query: What was Alice's salary on {format_datetime(july_2022)}?")
        
        # This would be the temporal query (when implemented):
        # salary_in_july = tracker.get_employee_as_of_valid("alice", july_2022)
        # For now, we'll simulate it by looking at the history
        
        history = tracker.get_employee_history("alice")
        salary_in_july = None
        for valid_time, tx_id, data in sorted(history, key=lambda x: x[0]):
            if valid_time <= july_2022:
                salary_in_july = data
            else:
                break
                
        if salary_in_july:
            print(f"   Answer: {format_currency(salary_in_july['salary'])}")
            print(f"   (This was from the June 15 raise)")
        
        # Show what the corrected history looks like
        print(f"\n📊 Current view of Alice's salary history:")
        print("   (After the payroll correction)")
        
        current_history = tracker.get_employee_history("alice")
        for valid_time, tx_id, data in current_history:
            salary = format_currency(data['salary'])
            print(f"   {format_datetime(valid_time)}: {salary}")
            
        print(f"\n💡 Key Insights:")
        print("   • Each record has both valid time (when true) and transaction time (when recorded)")
        print("   • Corrections create new transaction times but preserve valid times")
        print("   • Complete audit trail shows who changed what when")
        print("   • Can query 'what did we know when' vs 'what was true when'")
        
        # Demonstrate the power of bitemporal queries
        print(f"\n🚀 Advanced Temporal Capabilities (Coming in Phase 4):")
        print("   • AS OF VALID timestamp - data as it was valid at a point in time")
        print("   • AS OF TRANSACTION tx_id - data as recorded at a transaction")
        print("   • BETWEEN VALID start AND end - all versions valid in a period")
        print("   • Combined queries - what we knew when about what was true when")
        
        print(f"\n✨ This demonstrates LLMDB's unique bitemporal capabilities!")
        print("   Traditional databases lose history. LLMDB keeps it all.")


if __name__ == "__main__":
    main()