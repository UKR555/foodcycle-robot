"""
InsightsAgent: Analyzes donation data to provide impact metrics and visualizations.
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path to access shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class InsightsAgent:
    def __init__(self, db_path='database/foodcycle.sqlite'):
        """Initialize the insights agent with database connection."""
        self.db_path = db_path
        self.connect_db()
        
        # Constants for impact calculation
        self.impact_factors = {
            'meals_per_kg': 2.5,  # Estimated number of meals per kg of food
            'co2_per_kg': 2.5,    # Estimated kg of CO2 saved per kg of food
            'water_per_kg': 1000   # Estimated liters of water saved per kg of food
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
    
    def calculate_overall_impact(self):
        """Calculate the overall impact of all successful donations."""
        try:
            # Get all completed donations
            self.cursor.execute(
                "SELECT * FROM donations WHERE status = 'completed'"
            )
            donations = [dict(row) for row in self.cursor.fetchall()]
            
            # Extract quantities and normalize
            total_kg = 0
            for donation in donations:
                quantity = donation['quantity'].lower()
                
                # Basic parsing of quantity strings
                if 'kg' in quantity:
                    try:
                        kg = float(quantity.split('kg')[0].strip())
                        total_kg += kg
                    except ValueError:
                        pass
                elif 'g' in quantity and 'kg' not in quantity:
                    try:
                        g = float(quantity.split('g')[0].strip())
                        total_kg += g / 1000
                    except ValueError:
                        pass
                elif 'lb' in quantity or 'pound' in quantity:
                    try:
                        if 'lb' in quantity:
                            lb = float(quantity.split('lb')[0].strip())
                        else:
                            lb = float(quantity.split('pound')[0].strip())
                        total_kg += lb * 0.453592  # Convert lb to kg
                    except ValueError:
                        pass
                elif 'item' in quantity or 'piece' in quantity or 'pcs' in quantity:
                    try:
                        if 'item' in quantity:
                            items = float(quantity.split('item')[0].strip())
                        elif 'piece' in quantity:
                            items = float(quantity.split('piece')[0].strip())
                        else:
                            items = float(quantity.split('pcs')[0].strip())
                        total_kg += items * 0.2  # Assume average item weight is 200g
                    except ValueError:
                        pass
                else:
                    # Try to extract just the number
                    try:
                        parts = quantity.split()
                        if parts and parts[0].replace('.', '', 1).isdigit():
                            num = float(parts[0])
                            if len(parts) > 1:
                                unit = parts[1].lower()
                                if unit in ['box', 'boxes', 'package', 'packages', 'pack', 'packs']:
                                    total_kg += num * 0.5  # Assume average package is 500g
                                else:
                                    total_kg += num * 0.3  # Generic assumption for unspecified units
                            else:
                                total_kg += num * 0.3  # Just a number, assume kg
                    except (ValueError, IndexError):
                        # If we can't parse it, make a conservative estimate
                        total_kg += 0.2
            
            # Calculate impact metrics
            impact = {
                "total_donations": len(donations),
                "estimated_total_kg": round(total_kg, 2),
                "estimated_meals_provided": round(total_kg * self.impact_factors['meals_per_kg']),
                "estimated_co2_saved": round(total_kg * self.impact_factors['co2_per_kg'], 2),
                "estimated_water_saved": round(total_kg * self.impact_factors['water_per_kg']),
                "unique_donors": len(set(d['donor_id'] for d in donations)),
                "unique_recipients": self.count_unique_recipients()
            }
            
            return impact
        except sqlite3.Error as e:
            print(f"Error calculating overall impact: {e}")
            return {}
    
    def count_unique_recipients(self):
        """Count the number of unique recipients who received donations."""
        try:
            self.cursor.execute(
                """
                SELECT COUNT(DISTINCT recipient_id) as count 
                FROM requests 
                WHERE status = 'accepted'
                """
            )
            result = self.cursor.fetchone()
            return result['count'] if result else 0
        except sqlite3.Error as e:
            print(f"Error counting unique recipients: {e}")
            return 0
    
    def generate_time_series_data(self, period='monthly'):
        """Generate time series data for donations over time."""
        try:
            if period == 'monthly':
                date_format = '%Y-%m'
                sql_format = "strftime('%Y-%m', created_at)"
            elif period == 'weekly':
                date_format = '%Y-%W'
                sql_format = "strftime('%Y-%W', created_at)"
            elif period == 'daily':
                date_format = '%Y-%m-%d'
                sql_format = "date(created_at)"
            else:
                date_format = '%Y-%m'
                sql_format = "strftime('%Y-%m', created_at)"
            
            # Get donation counts by period
            self.cursor.execute(
                f"""
                SELECT 
                    {sql_format} as period,
                    COUNT(*) as donation_count
                FROM donations
                GROUP BY period
                ORDER BY period
                """
            )
            donation_counts = [dict(row) for row in self.cursor.fetchall()]
            
            # Get request counts by period
            self.cursor.execute(
                f"""
                SELECT 
                    {sql_format} as period,
                    COUNT(*) as request_count
                FROM requests
                GROUP BY period
                ORDER BY period
                """
            )
            request_counts = [dict(row) for row in self.cursor.fetchall()]
            
            # Combine data for visualization
            time_series_data = {
                "period_type": period,
                "donations": donation_counts,
                "requests": request_counts
            }
            
            return time_series_data
        except sqlite3.Error as e:
            print(f"Error generating time series data: {e}")
            return {}
    
    def analyze_food_waste_prevention(self):
        """Analyze how much food waste was prevented through the platform."""
        try:
            # Get donations that would have expired soon when they were completed
            threshold_days = 5  # Consider food "saved" if it was completed within 5 days of expiry
            
            self.cursor.execute(
                """
                SELECT 
                    COUNT(*) as count,
                    julianday(expiry_date) - julianday(created_at) as shelf_life_days
                FROM donations
                WHERE 
                    status = 'completed' 
                    AND expiry_date IS NOT NULL
                    AND julianday(expiry_date) - julianday(created_at) <= ?
                """,
                (threshold_days,)
            )
            nearly_expired = self.cursor.fetchone()
            
            # Get donations completed by expiry date proximity
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
                WHERE 
                    status = 'completed' 
                    AND expiry_date IS NOT NULL
                GROUP BY shelf_life
                ORDER BY count DESC
                """
            )
            shelf_life_distribution = [dict(row) for row in self.cursor.fetchall()]
            
            # Estimate food saved from waste
            # Assume donations completed with short shelf life would have been wasted
            short_shelf_life_count = sum(item['count'] for item in shelf_life_distribution 
                                        if item['shelf_life'] in ['very_short', 'short'])
            
            # Estimate kg saved (similar to overall impact calculation)
            saved_kg = 0
            self.cursor.execute(
                """
                SELECT quantity 
                FROM donations 
                WHERE status = 'completed' 
                AND expiry_date IS NOT NULL
                AND julianday(expiry_date) - julianday(created_at) <= 7
                """
            )
            short_quantities = [row['quantity'] for row in self.cursor.fetchall()]
            
            # Basic parsing of quantity strings (simplified version)
            for quantity in short_quantities:
                quantity = quantity.lower()
                if 'kg' in quantity:
                    try:
                        kg = float(quantity.split('kg')[0].strip())
                        saved_kg += kg
                    except ValueError:
                        saved_kg += 0.5  # Default assumption
                else:
                    saved_kg += 0.5  # Default assumption
            
            waste_prevention = {
                "donations_saved_from_waste": short_shelf_life_count,
                "percentage_of_total": round((short_shelf_life_count / max(1, self.count_completed_donations())) * 100),
                "estimated_kg_saved": round(saved_kg, 2),
                "environmental_impact": {
                    "co2_prevented": round(saved_kg * self.impact_factors['co2_per_kg'], 2),
                    "water_saved": round(saved_kg * self.impact_factors['water_per_kg'])
                },
                "shelf_life_distribution": shelf_life_distribution
            }
            
            return waste_prevention
        except sqlite3.Error as e:
            print(f"Error analyzing food waste prevention: {e}")
            return {}
    
    def count_completed_donations(self):
        """Count the total number of completed donations."""
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM donations WHERE status = 'completed'")
            result = self.cursor.fetchone()
            return result['count'] if result else 0
        except sqlite3.Error as e:
            print(f"Error counting completed donations: {e}")
            return 0
    
    def generate_geographic_insights(self):
        """Generate insights based on geographic distribution of donations."""
        try:
            # Get donation counts by location
            self.cursor.execute(
                """
                SELECT 
                    location,
                    COUNT(*) as donation_count
                FROM donations
                WHERE location IS NOT NULL AND location != ''
                GROUP BY location
                ORDER BY donation_count DESC
                """
            )
            location_data = [dict(row) for row in self.cursor.fetchall()]
            
            # Calculate donation density per location
            total_donations = sum(item['donation_count'] for item in location_data)
            
            for item in location_data:
                item['percentage'] = round((item['donation_count'] / total_donations) * 100, 1)
            
            return {
                "location_distribution": location_data,
                "total_locations": len(location_data),
                "most_active_location": location_data[0]['location'] if location_data else "Unknown"
            }
        except sqlite3.Error as e:
            print(f"Error generating geographic insights: {e}")
            return {}
    
    def generate_user_engagement_metrics(self):
        """Generate metrics on user engagement with the platform."""
        try:
            # Donor engagement
            self.cursor.execute(
                """
                SELECT 
                    donor_id,
                    COUNT(*) as donation_count
                FROM donations
                GROUP BY donor_id
                ORDER BY donation_count DESC
                """
            )
            donor_activity = [dict(row) for row in self.cursor.fetchall()]
            
            # Calculate donor engagement metrics
            donor_count = len(donor_activity)
            total_donations = sum(d['donation_count'] for d in donor_activity)
            avg_donations_per_donor = round(total_donations / max(1, donor_count), 2)
            
            # Recurring donors (more than 1 donation)
            recurring_donors = sum(1 for d in donor_activity if d['donation_count'] > 1)
            recurring_donor_rate = round((recurring_donors / max(1, donor_count)) * 100, 1)
            
            # Top donors
            top_donors = donor_activity[:5] if donor_activity else []
            
            # Recipient engagement
            self.cursor.execute(
                """
                SELECT 
                    recipient_id,
                    COUNT(*) as request_count
                FROM requests
                GROUP BY recipient_id
                ORDER BY request_count DESC
                """
            )
            recipient_activity = [dict(row) for row in self.cursor.fetchall()]
            
            # Calculate recipient engagement metrics
            recipient_count = len(recipient_activity)
            total_requests = sum(r['request_count'] for r in recipient_activity)
            avg_requests_per_recipient = round(total_requests / max(1, recipient_count), 2)
            
            # Recurring recipients (more than 1 request)
            recurring_recipients = sum(1 for r in recipient_activity if r['request_count'] > 1)
            recurring_recipient_rate = round((recurring_recipients / max(1, recipient_count)) * 100, 1)
            
            # Chat activity
            self.cursor.execute("SELECT COUNT(*) as count FROM messages")
            message_count = self.cursor.fetchone()['count']
            
            engagement_metrics = {
                "donor_metrics": {
                    "total_donors": donor_count,
                    "avg_donations_per_donor": avg_donations_per_donor,
                    "recurring_donor_rate": recurring_donor_rate,
                    "top_donors": top_donors
                },
                "recipient_metrics": {
                    "total_recipients": recipient_count,
                    "avg_requests_per_recipient": avg_requests_per_recipient,
                    "recurring_recipient_rate": recurring_recipient_rate
                },
                "communication_metrics": {
                    "total_messages": message_count,
                    "avg_messages_per_donation": round(message_count / max(1, total_donations), 2)
                }
            }
            
            return engagement_metrics
        except sqlite3.Error as e:
            print(f"Error generating user engagement metrics: {e}")
            return {}
    
    def generate_comprehensive_report(self):
        """Generate a comprehensive impact and insights report."""
        overall_impact = self.calculate_overall_impact()
        time_series = self.generate_time_series_data('monthly')
        waste_prevention = self.analyze_food_waste_prevention()
        geographic = self.generate_geographic_insights()
        engagement = self.generate_user_engagement_metrics()
        
        report = {
            "report_date": datetime.now().strftime('%Y-%m-%d'),
            "overall_impact": overall_impact,
            "user_engagement": engagement,
            "food_waste_prevention": waste_prevention,
            "geographic_insights": geographic,
            "time_series_data": time_series
        }
        
        return report

# Example usage
if __name__ == "__main__":
    agent = InsightsAgent()
    
    # Generate comprehensive report
    report = agent.generate_comprehensive_report()
    print(json.dumps(report, indent=2))
    
    agent.close_connection() 