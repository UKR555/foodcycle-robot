"""
RecipientAgent: Handles interactions with food recipients and matches them with appropriate donations.
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path to access shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RecipientAgent:
    def __init__(self, db_path='database/foodcycle.sqlite'):
        """Initialize the recipient agent with database connection."""
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
    
    def get_available_donations(self, limit=20):
        """Get a list of available donations ordered by expiry date."""
        try:
            self.cursor.execute(
                """
                SELECT d.*, u.name as donor_name
                FROM donations d
                JOIN users u ON d.donor_id = u.id
                WHERE d.status = 'available'
                ORDER BY 
                    CASE 
                        WHEN d.expiry_date IS NULL THEN '9999-12-31'
                        ELSE d.expiry_date 
                    END ASC,
                    d.created_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            donations = [dict(row) for row in self.cursor.fetchall()]
            print(f"Retrieved {len(donations)} available donations")
            return donations
        except sqlite3.Error as e:
            print(f"Error retrieving available donations: {e}")
            return []
    
    def get_recipient_history(self, recipient_id):
        """Get a recipient's request history."""
        try:
            self.cursor.execute(
                """
                SELECT r.*, d.food_name, d.quantity, d.expiry_date, u.name as donor_name
                FROM requests r
                JOIN donations d ON r.donation_id = d.id
                JOIN users u ON d.donor_id = u.id
                WHERE r.recipient_id = ?
                ORDER BY r.created_at DESC
                """,
                (recipient_id,)
            )
            requests = [dict(row) for row in self.cursor.fetchall()]
            print(f"Retrieved {len(requests)} requests for recipient {recipient_id}")
            return requests
        except sqlite3.Error as e:
            print(f"Error retrieving recipient history: {e}")
            return []
    
    def calculate_recipient_preferences(self, recipient_id):
        """Calculate food preferences based on recipient's request history."""
        requests = self.get_recipient_history(recipient_id)
        
        if not requests:
            return {
                "preferences": {},
                "message": "No preference data available."
            }
        
        # Extract food types from request history
        food_types = {}
        for request in requests:
            if request['status'] != 'rejected':  # Only consider accepted or pending requests
                food_name = request['food_name'].lower()
                
                # Categorize food
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
        
        # Calculate preferences as percentages
        total_requests = sum(food_types.values())
        preferences = {k: round((v / total_requests) * 100) for k, v in food_types.items()}
        
        return {
            "preferences": preferences,
            "total_requests": total_requests,
            "most_requested": max(preferences.items(), key=lambda x: x[1])[0] if preferences else None
        }
    
    def match_donation_to_recipient(self, recipient_id):
        """Match the most suitable donations to a recipient based on preferences."""
        preferences = self.calculate_recipient_preferences(recipient_id)
        available_donations = self.get_available_donations()
        
        if not available_donations:
            return {
                "matches": [],
                "message": "No available donations at this time."
            }
        
        # If we have no preference data, just return available donations
        if not preferences.get('preferences'):
            return {
                "matches": available_donations[:5],
                "message": "Showing available donations (no preference data available)."
            }
        
        # Calculate match score for each donation
        scored_donations = []
        for donation in available_donations:
            score = 0
            food_name = donation['food_name'].lower()
            
            # Categorize the donation
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
            
            # Score based on preference match
            if category in preferences['preferences']:
                score += preferences['preferences'][category]
            
            # Score based on expiry (prioritize items expiring soon)
            if donation['expiry_date']:
                try:
                    expiry_date = datetime.strptime(donation['expiry_date'], '%Y-%m-%d')
                    days_until_expiry = (expiry_date - datetime.now()).days
                    
                    # Higher score for items expiring soon, but not too soon
                    if 2 <= days_until_expiry <= 7:
                        score += 20
                    elif days_until_expiry > 7:
                        score += 10
                except ValueError:
                    # Handle date parsing errors
                    pass
            
            scored_donations.append((donation, score))
        
        # Sort by score (descending)
        scored_donations.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 5 matches
        matches = [d[0] for d in scored_donations[:5]]
        
        return {
            "matches": matches,
            "recipient_preferences": preferences,
            "message": f"Found {len(matches)} donations matching your preferences."
        }
    
    def create_request(self, recipient_id, donation_id):
        """Create a new request for a donation."""
        try:
            # Check if donation is available
            self.cursor.execute(
                "SELECT status FROM donations WHERE id = ?",
                (donation_id,)
            )
            result = self.cursor.fetchone()
            
            if not result:
                return {
                    "status": "error",
                    "message": "Donation not found."
                }
            
            if result['status'] != 'available':
                return {
                    "status": "error",
                    "message": f"Donation is not available (current status: {result['status']})."
                }
            
            # Create the request
            self.cursor.execute(
                "INSERT INTO requests (recipient_id, donation_id) VALUES (?, ?)",
                (recipient_id, donation_id)
            )
            
            # Update donation status to 'reserved'
            self.cursor.execute(
                "UPDATE donations SET status = 'reserved' WHERE id = ?",
                (donation_id,)
            )
            
            self.conn.commit()
            
            return {
                "status": "success",
                "message": "Request created successfully.",
                "request_id": self.cursor.lastrowid
            }
        except sqlite3.Error as e:
            print(f"Error creating request: {e}")
            return {
                "status": "error",
                "message": f"Failed to create request: {str(e)}"
            }

# Example usage
if __name__ == "__main__":
    agent = RecipientAgent()
    
    # Example: Match donations to a recipient
    recipient_id = 2  # Example recipient ID
    matches = agent.match_donation_to_recipient(recipient_id)
    print(json.dumps(matches, indent=2))
    
    # Example: Calculate recipient preferences
    preferences = agent.calculate_recipient_preferences(recipient_id)
    print(json.dumps(preferences, indent=2))
    
    # Example: Create a request (uncomment to test)
    # donation_id = 1  # Example donation ID
    # result = agent.create_request(recipient_id, donation_id)
    # print(json.dumps(result, indent=2))
    
    agent.close_connection() 