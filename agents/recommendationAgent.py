"""
RecommendationAgent: Provides intelligent recommendations for food donations and matchmaking.
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path to access shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RecommendationAgent:
    def __init__(self, db_path='database/foodcycle.sqlite'):
        """Initialize the recommendation agent with database connection."""
        self.db_path = db_path
        self.connect_db()
        
        # Define food categories for classification
        self.food_categories = {
            'vegetables': ['vegetable', 'veg', 'greens', 'lettuce', 'spinach', 'carrot', 'tomato'],
            'fruits': ['fruit', 'apple', 'banana', 'orange', 'berry', 'berries'],
            'dairy': ['dairy', 'milk', 'cheese', 'yogurt', 'butter', 'cream'],
            'bakery': ['bread', 'bakery', 'cake', 'pastry', 'roll', 'bun'],
            'canned': ['canned', 'can', 'preserved', 'jar', 'tin'],
            'grains': ['rice', 'pasta', 'grain', 'cereal', 'oat', 'wheat'],
            'meat': ['meat', 'beef', 'chicken', 'pork', 'fish', 'seafood', 'poultry'],
            'ready': ['prepared', 'meal', 'cooked', 'ready', 'leftover']
        }
    
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
    
    def categorize_food(self, food_name):
        """Categorize food based on keywords in the name."""
        food_name = food_name.lower()
        
        for category, keywords in self.food_categories.items():
            for keyword in keywords:
                if keyword in food_name:
                    return category
        
        return 'other'
    
    def analyze_donation_trends(self):
        """Analyze trends in donations over time."""
        try:
            # Overall donation trends
            self.cursor.execute(
                """
                SELECT 
                    date(created_at) as donation_date,
                    COUNT(*) as donation_count
                FROM donations
                GROUP BY donation_date
                ORDER BY donation_date DESC
                LIMIT 30
                """
            )
            daily_counts = [dict(row) for row in self.cursor.fetchall()]
            
            # Food type trends
            self.cursor.execute("SELECT food_name FROM donations")
            food_names = [row['food_name'] for row in self.cursor.fetchall()]
            
            food_categories = {}
            for food in food_names:
                category = self.categorize_food(food)
                food_categories[category] = food_categories.get(category, 0) + 1
            
            # Sort by frequency
            food_categories = dict(sorted(food_categories.items(), key=lambda x: x[1], reverse=True))
            
            # Expiration patterns
            self.cursor.execute(
                """
                SELECT
                    CASE
                        WHEN julianday(expiry_date) - julianday(created_at) <= 3 THEN 'very_short'
                        WHEN julianday(expiry_date) - julianday(created_at) <= 7 THEN 'short'
                        WHEN julianday(expiry_date) - julianday(created_at) <= 14 THEN 'medium'
                        ELSE 'long'
                    END as shelf_life,
                    COUNT(*) as count
                FROM donations
                WHERE expiry_date IS NOT NULL
                GROUP BY shelf_life
                ORDER BY count DESC
                """
            )
            shelf_life = [dict(row) for row in self.cursor.fetchall()]
            
            return {
                "daily_trends": daily_counts,
                "food_categories": food_categories,
                "shelf_life": shelf_life
            }
        except sqlite3.Error as e:
            print(f"Error analyzing donation trends: {e}")
            return {}
    
    def identify_community_needs(self):
        """Identify current community needs based on requests and available food."""
        try:
            # Most requested food types
            self.cursor.execute(
                """
                SELECT d.food_name, COUNT(*) as request_count
                FROM requests r
                JOIN donations d ON r.donation_id = d.id
                GROUP BY d.food_name
                ORDER BY request_count DESC
                LIMIT 10
                """
            )
            most_requested = [dict(row) for row in self.cursor.fetchall()]
            
            # Most requested but unavailable categories
            self.cursor.execute(
                """
                SELECT food_name FROM donations 
                WHERE status = 'completed' 
                AND id IN (
                    SELECT donation_id FROM requests GROUP BY donation_id
                    HAVING COUNT(*) > 1
                )
                ORDER BY created_at DESC
                LIMIT 20
                """
            )
            high_demand_foods = [row['food_name'] for row in self.cursor.fetchall()]
            
            high_demand_categories = {}
            for food in high_demand_foods:
                category = self.categorize_food(food)
                high_demand_categories[category] = high_demand_categories.get(category, 0) + 1
            
            # Sort by frequency
            high_demand_categories = dict(sorted(high_demand_categories.items(), key=lambda x: x[1], reverse=True))
            
            # Currently available categories
            self.cursor.execute("SELECT food_name FROM donations WHERE status = 'available'")
            available_foods = [row['food_name'] for row in self.cursor.fetchall()]
            
            available_categories = {}
            for food in available_foods:
                category = self.categorize_food(food)
                available_categories[category] = available_categories.get(category, 0) + 1
            
            # Calculate supply-demand gap
            all_categories = set(high_demand_categories.keys()) | set(available_categories.keys())
            supply_demand_gap = {}
            
            for category in all_categories:
                demand = high_demand_categories.get(category, 0)
                supply = available_categories.get(category, 0)
                
                if demand > 0:
                    # Calculate as percentage: (demand - supply) / demand * 100
                    gap = (demand - min(demand, supply)) / demand * 100
                    supply_demand_gap[category] = round(gap)
            
            # Sort by gap size (descending)
            supply_demand_gap = dict(sorted(supply_demand_gap.items(), key=lambda x: x[1], reverse=True))
            
            return {
                "most_requested": most_requested,
                "high_demand_categories": high_demand_categories,
                "available_categories": available_categories,
                "supply_demand_gap": supply_demand_gap
            }
        except sqlite3.Error as e:
            print(f"Error identifying community needs: {e}")
            return {}
    
    def generate_donor_recommendations(self, donor_id=None):
        """Generate personalized recommendations for donors."""
        community_needs = self.identify_community_needs()
        trends = self.analyze_donation_trends()
        
        recommendations = []
        
        # Add recommendations based on community needs
        if community_needs.get('supply_demand_gap'):
            for category, gap in list(community_needs['supply_demand_gap'].items())[:3]:
                if gap > 50:  # High gap indicates need
                    recommendations.append({
                        "type": "need",
                        "category": category,
                        "message": f"The community has a high need for {category}. Consider donating these items."
                    })
        
        # Add recommendations based on trends
        if trends.get('shelf_life'):
            shelf_life_dict = {sl['shelf_life']: sl['count'] for sl in trends['shelf_life']}
            if shelf_life_dict.get('very_short', 0) > shelf_life_dict.get('medium', 0):
                recommendations.append({
                    "type": "shelf_life",
                    "message": "Many donations have very short shelf life. Consider donating items that last longer."
                })
        
        # Add recommendations based on specific donor history if donor_id is provided
        if donor_id:
            try:
                self.cursor.execute(
                    "SELECT food_name FROM donations WHERE donor_id = ? ORDER BY created_at DESC LIMIT 10",
                    (donor_id,)
                )
                donor_foods = [row['food_name'] for row in self.cursor.fetchall()]
                
                donor_categories = {}
                for food in donor_foods:
                    category = self.categorize_food(food)
                    donor_categories[category] = donor_categories.get(category, 0) + 1
                
                # Sort by frequency
                donor_categories = dict(sorted(donor_categories.items(), key=lambda x: x[1], reverse=True))
                
                # Recommend diversification if donor mostly donates one category
                if donor_categories and list(donor_categories.values())[0] > 0.6 * sum(donor_categories.values()):
                    most_donated = list(donor_categories.keys())[0]
                    needed_categories = [c for c, g in community_needs.get('supply_demand_gap', {}).items() 
                                        if g > 30 and c != most_donated]
                    
                    if needed_categories:
                        recommendations.append({
                            "type": "diversify",
                            "message": f"You frequently donate {most_donated}. Consider diversifying with {needed_categories[0]} which is in high demand."
                        })
            except sqlite3.Error as e:
                print(f"Error analyzing donor history: {e}")
        
        # Add general recommendations if we don't have many specific ones
        if len(recommendations) < 3:
            general_recs = [
                {
                    "type": "general",
                    "message": "Non-perishable items like canned goods and grains are always valuable donations."
                },
                {
                    "type": "general",
                    "message": "Consider donating fresh produce that has at least 5-7 days before expiration."
                },
                {
                    "type": "general",
                    "message": "Excess food from events can be donated if properly stored and transported."
                }
            ]
            
            recommendations.extend(general_recs[:3 - len(recommendations)])
        
        return {
            "recommendations": recommendations,
            "community_needs": community_needs.get('supply_demand_gap', {}),
            "trends": {
                "food_categories": trends.get('food_categories', {}),
                "daily_trends": trends.get('daily_trends', [])
            }
        }
    
    def generate_recipient_recommendations(self, recipient_id):
        """Generate personalized recommendations for recipients."""
        try:
            # Get recipient's request history
            self.cursor.execute(
                """
                SELECT d.food_name, d.expiry_date, r.status
                FROM requests r
                JOIN donations d ON r.donation_id = d.id
                WHERE r.recipient_id = ?
                ORDER BY r.created_at DESC
                """,
                (recipient_id,)
            )
            request_history = [dict(row) for row in self.cursor.fetchall()]
            
            # Calculate preferred categories
            preferences = {}
            for request in request_history:
                if request['status'] != 'rejected':
                    category = self.categorize_food(request['food_name'])
                    preferences[category] = preferences.get(category, 0) + 1
            
            # Available donations
            self.cursor.execute(
                """
                SELECT *
                FROM donations
                WHERE status = 'available'
                ORDER BY 
                    CASE 
                        WHEN expiry_date IS NULL THEN '9999-12-31'
                        ELSE expiry_date 
                    END ASC
                LIMIT 30
                """
            )
            available = [dict(row) for row in self.cursor.fetchall()]
            
            # Score and rank available donations
            scored_donations = []
            for donation in available:
                score = 0
                category = self.categorize_food(donation['food_name'])
                
                # Base score on preferences
                if category in preferences:
                    score += preferences[category] * 10
                
                # Consider expiration (prioritize items with reasonable shelf life)
                if donation['expiry_date']:
                    try:
                        expiry = datetime.strptime(donation['expiry_date'], '%Y-%m-%d')
                        days_left = (expiry - datetime.now()).days
                        
                        if 3 <= days_left <= 10:
                            score += 20
                        elif days_left > 10:
                            score += 10
                    except (ValueError, TypeError):
                        pass
                
                scored_donations.append((donation, score))
            
            # Sort by score
            scored_donations.sort(key=lambda x: x[1], reverse=True)
            
            # Generate recommendations
            recommendations = []
            
            # Top recommended donations
            top_donations = [d[0] for d in scored_donations[:5]]
            if top_donations:
                recommendations.append({
                    "type": "recommended_donations",
                    "donations": top_donations
                })
            
            # Preferred but unavailable categories
            available_categories = {self.categorize_food(d['food_name']) for d in available}
            missing_preferences = [p for p in preferences if p not in available_categories]
            
            if missing_preferences:
                recommendations.append({
                    "type": "unavailable_preference",
                    "message": f"Your preferred food categories ({', '.join(missing_preferences)}) are currently unavailable. Consider alternative options or check back later."
                })
            
            # Expiring soon
            expiring_soon = [d for d in available if d['expiry_date'] and 
                             datetime.strptime(d['expiry_date'], '%Y-%m-%d') - datetime.now() <= timedelta(days=3)]
            
            if expiring_soon:
                recommendations.append({
                    "type": "expiring_soon",
                    "message": f"There are {len(expiring_soon)} donations expiring soon. Consider requesting these to prevent food waste.",
                    "donations": expiring_soon[:3]
                })
            
            return {
                "recipient_id": recipient_id,
                "preferences": preferences,
                "recommendations": recommendations
            }
        except sqlite3.Error as e:
            print(f"Error generating recipient recommendations: {e}")
            return {
                "recipient_id": recipient_id,
                "error": str(e)
            }

# Example usage
if __name__ == "__main__":
    agent = RecommendationAgent()
    
    # Generate donor recommendations
    donor_recs = agent.generate_donor_recommendations()
    print("Donor Recommendations:")
    print(json.dumps(donor_recs, indent=2))
    
    # Generate recipient recommendations
    recipient_id = 2  # Example recipient ID
    recipient_recs = agent.generate_recipient_recommendations(recipient_id)
    print("\nRecipient Recommendations:")
    print(json.dumps(recipient_recs, indent=2))
    
    # Analyze donation trends
    trends = agent.analyze_donation_trends()
    print("\nDonation Trends:")
    print(json.dumps(trends, indent=2))
    
    agent.close_connection() 