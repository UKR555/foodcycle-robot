"""
DonorAgent: Handles interactions with food donors and processes donation information.
"""

import sqlite3
import json
import time
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path to access shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DonorAgent:
    def __init__(self, db_path='database/foodcycle.sqlite'):
        """Initialize the donor agent with database connection."""
        self.db_path = db_path
        self.connect_db()
    
    def connect_db(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            sys.exit(1)
    
    def close_connection(self):
        """Close the database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()
            print("Database connection closed")
    
    def get_donor_donations(self, donor_id):
        """Retrieve all donations made by a specific donor."""
        try:
            self.cursor.execute(
                "SELECT * FROM donations WHERE donor_id = ? ORDER BY created_at DESC",
                (donor_id,)
            )
            donations = [dict(row) for row in self.cursor.fetchall()]
            print(f"Retrieved {len(donations)} donations for donor {donor_id}")
            return donations
        except sqlite3.Error as e:
            print(f"Error retrieving donations: {e}")
            return []
    
    def analyze_donation_patterns(self, donor_id):
        """Analyze donation patterns for a specific donor."""
        donations = self.get_donor_donations(donor_id)
        
        if not donations:
            return {
                "total_donations": 0,
                "message": "No donation history found."
            }
        
        # Analyze donation frequency
        dates = [datetime.strptime(d['created_at'], '%Y-%m-%dT%H:%M:%SZ') 
                 if 'T' in d['created_at'] else 
                 datetime.strptime(d['created_at'], '%Y-%m-%d %H:%M:%S') 
                 for d in donations]
        
        if len(dates) > 1:
            date_diffs = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
            avg_frequency = sum(date_diffs) / len(date_diffs) if date_diffs else 0
        else:
            avg_frequency = 0
        
        # Analyze food types
        food_types = {}
        for donation in donations:
            food_name = donation['food_name'].lower()
            if 'vegetable' in food_name or 'veg' in food_name:
                category = 'vegetables'
            elif 'fruit' in food_name:
                category = 'fruits'
            elif 'bread' in food_name or 'bakery' in food_name:
                category = 'bakery'
            elif 'canned' in food_name:
                category = 'canned goods'
            elif 'dairy' in food_name or 'milk' in food_name or 'cheese' in food_name:
                category = 'dairy'
            else:
                category = 'other'
            
            food_types[category] = food_types.get(category, 0) + 1
        
        most_common_category = max(food_types.items(), key=lambda x: x[1])[0] if food_types else 'none'
        
        # Calculate impact
        total_donations = len(donations)
        
        return {
            "total_donations": total_donations,
            "donation_frequency": f"Approximately every {round(avg_frequency)} days" if avg_frequency else "First donation",
            "most_common_food": most_common_category,
            "food_distribution": food_types,
            "next_predicted_donation": (dates[0] + timedelta(days=avg_frequency)).strftime('%Y-%m-%d') if avg_frequency else "Unknown"
        }
    
    def generate_suggestions(self, donor_id):
        """Generate donation suggestions based on donor history and community needs."""
        # Get donor's donation patterns
        patterns = self.analyze_donation_patterns(donor_id)
        
        # Check current needs in the system
        try:
            self.cursor.execute("""
                SELECT food_name, COUNT(*) as request_count 
                FROM requests r
                JOIN donations d ON r.donation_id = d.id
                WHERE r.status = 'pending'
                GROUP BY food_name
                ORDER BY request_count DESC
                LIMIT 5
            """)
            needs = [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error retrieving community needs: {e}")
            needs = []
        
        # Check for soon-to-expire foods in the system
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            self.cursor.execute("""
                SELECT COUNT(*) as count
                FROM donations
                WHERE status = 'available'
                AND expiry_date < date('now', '+7 days')
                AND expiry_date >= date('now')
            """)
            expiring_soon = self.cursor.fetchone()['count']
        except sqlite3.Error as e:
            print(f"Error retrieving expiration data: {e}")
            expiring_soon = 0
        
        # Generate personalized suggestions
        suggestions = []
        
        if patterns["total_donations"] == 0:
            suggestions.append({
                "type": "first_time",
                "message": "Welcome to FoodCycle! Consider donating non-perishable items for your first donation."
            })
        else:
            if needs:
                suggestions.append({
                    "type": "community_needs",
                    "message": f"The community currently needs: {', '.join([n['food_name'] for n in needs])}"
                })
            
            if patterns.get('most_common_food', '') != 'none':
                suggestions.append({
                    "type": "diversify",
                    "message": f"You've been donating a lot of {patterns['most_common_food']}. Consider diversifying with other food categories."
                })
            
            if expiring_soon > 0:
                suggestions.append({
                    "type": "expiring",
                    "message": f"There are {expiring_soon} donations expiring soon. Consider donating items with longer shelf life."
                })
            
            if 'next_predicted_donation' in patterns and patterns['next_predicted_donation'] != 'Unknown':
                suggestions.append({
                    "type": "schedule",
                    "message": f"Based on your history, we expect your next donation around {patterns['next_predicted_donation']}. Schedule it in advance!"
                })
        
        return {
            "donor_id": donor_id,
            "patterns": patterns,
            "suggestions": suggestions
        }
    
    def process_new_donation(self, donation_data):
        """Process a new donation and provide feedback."""
        try:
            # Insert the donation into the database
            self.cursor.execute(
                """
                INSERT INTO donations (
                    donor_id, food_name, quantity, expiry_date, description, location
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    donation_data['donor_id'],
                    donation_data['food_name'],
                    donation_data['quantity'],
                    donation_data.get('expiry_date'),
                    donation_data.get('description', ''),
                    donation_data.get('location', '')
                )
            )
            self.conn.commit()
            donation_id = self.cursor.lastrowid
            
            # Generate feedback and recommendations
            feedback = {
                "donation_id": donation_id,
                "status": "success",
                "message": f"Thank you for donating {donation_data['quantity']} of {donation_data['food_name']}!",
                "impact": "Your donation can help feed up to 5 people in need.",
                "recommendations": self.generate_suggestions(donation_data['donor_id'])['suggestions']
            }
            
            return feedback
        except sqlite3.Error as e:
            print(f"Error processing donation: {e}")
            return {
                "status": "error",
                "message": f"Failed to process donation: {str(e)}"
            }

# Example usage
if __name__ == "__main__":
    agent = DonorAgent()
    
    # Example: Get suggestions for donor
    donor_id = 1  # Example donor ID
    suggestions = agent.generate_suggestions(donor_id)
    print(json.dumps(suggestions, indent=2))
    
    # Example: Process a new donation
    example_donation = {
        "donor_id": 1,
        "food_name": "Fresh Apples",
        "quantity": "10 kg",
        "expiry_date": (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
        "description": "Freshly harvested organic apples",
        "location": "Community Center"
    }
    
    # Uncomment to test donation processing
    # result = agent.process_new_donation(example_donation)
    # print(json.dumps(result, indent=2))
    
    agent.close_connection() 