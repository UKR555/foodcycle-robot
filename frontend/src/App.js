import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [donations, setDonations] = useState([]);
  const [view, setView] = useState('donations'); // 'donations', 'chat', 'profile'
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  
  // Simulating user login - in a real app, this would connect to your backend
  const handleLogin = (type) => {
    // For demo purposes, creating a mock user
    const mockUser = {
      id: type === 'donor' ? 1 : 2,
      name: type === 'donor' ? 'John Donor' : 'Sarah Recipient',
      email: type === 'donor' ? 'john@example.com' : 'sarah@example.com',
      user_type: type
    };
    
    setUser(mockUser);
    setIsLoggedIn(true);
    
    // Fetch donations based on user type
    fetchDonations();
  };
  
  // Fetch donations from the API
  const fetchDonations = async () => {
    try {
      // In a real app, you would connect to your backend API
      // For demo, using mock data
      const mockDonations = [
        {
          id: 1,
          donor_id: 1,
          donor_name: 'John Donor',
          food_name: 'Fresh Vegetables',
          quantity: '5 kg',
          expiry_date: '2023-12-31',
          description: 'Assorted fresh vegetables from local farm',
          location: 'Downtown Community Center',
          status: 'available',
          created_at: '2023-12-15T10:30:00Z'
        },
        {
          id: 2,
          donor_id: 3,
          donor_name: 'Mary Giver',
          food_name: 'Canned Goods',
          quantity: '12 cans',
          expiry_date: '2024-06-30',
          description: 'Assorted canned vegetables and beans',
          location: 'North Food Bank',
          status: 'available',
          created_at: '2023-12-14T14:45:00Z'
        }
      ];
      
      setDonations(mockDonations);
    } catch (error) {
      console.error('Error fetching donations:', error);
    }
  };
  
  // Chat with a donor or recipient
  const handleStartChat = (recipientId, recipientName) => {
    setSelectedRecipient({
      id: recipientId,
      name: recipientName
    });
    setView('chat');
  };
  
  // Create a new donation (donor only)
  const handleCreateDonation = () => {
    // In a real app, this would open a form and submit to the backend
    alert('Create donation form would open here');
  };
  
  // Simulate a request for a donation (recipient only)
  const handleRequestDonation = (donationId) => {
    // In a real app, this would submit a request to the backend
    alert(`Request sent for donation #${donationId}`);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>FoodCycle</h1>
        {isLoggedIn && (
          <nav>
            <button onClick={() => setView('donations')}>Donations</button>
            <button onClick={() => setView('profile')}>Profile</button>
          </nav>
        )}
      </header>
      
      <main className="app-content">
        {!isLoggedIn ? (
          <div className="login-container">
            <h2>Welcome to FoodCycle</h2>
            <p>Connect food donors with those in need, reducing waste and fighting hunger.</p>
            <div className="login-buttons">
              <button onClick={() => handleLogin('donor')}>Log in as Donor</button>
              <button onClick={() => handleLogin('recipient')}>Log in as Recipient</button>
            </div>
          </div>
        ) : (
          <>
            {view === 'donations' && (
              <div className="donations-container">
                <div className="donations-header">
                  <h2>Available Donations</h2>
                  {user.user_type === 'donor' && (
                    <button 
                      className="primary-button"
                      onClick={handleCreateDonation}
                    >
                      Create Donation
                    </button>
                  )}
                </div>
                
                <div className="donations-list">
                  {donations.map(donation => (
                    <div key={donation.id} className="donation-card">
                      <h3>{donation.food_name}</h3>
                      <p><strong>Quantity:</strong> {donation.quantity}</p>
                      <p><strong>Expires:</strong> {donation.expiry_date}</p>
                      <p><strong>Location:</strong> {donation.location}</p>
                      <p>{donation.description}</p>
                      <div className="donation-actions">
                        {user.user_type === 'recipient' && (
                          <>
                            <button 
                              onClick={() => handleRequestDonation(donation.id)}
                              className="primary-button"
                            >
                              Request
                            </button>
                            <button 
                              onClick={() => handleStartChat(donation.donor_id, donation.donor_name)}
                            >
                              Chat with Donor
                            </button>
                          </>
                        )}
                        {user.user_type === 'donor' && donation.donor_id === user.id && (
                          <span className="status">Your donation</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {view === 'chat' && selectedRecipient && (
              <div className="chat-view">
                <button 
                  className="back-button"
                  onClick={() => {
                    setView('donations');
                    setSelectedRecipient(null);
                  }}
                >
                  Back to Donations
                </button>
                <ChatInterface 
                  userId={user.id}
                  recipientId={selectedRecipient.id}
                  userName={user.name}
                  recipientName={selectedRecipient.name}
                />
              </div>
            )}
            
            {view === 'profile' && (
              <div className="profile-container">
                <h2>Your Profile</h2>
                <div className="profile-info">
                  <p><strong>Name:</strong> {user.name}</p>
                  <p><strong>Email:</strong> {user.email}</p>
                  <p><strong>Account Type:</strong> {user.user_type === 'donor' ? 'Food Donor' : 'Recipient'}</p>
                </div>
                <button 
                  className="logout-button"
                  onClick={() => {
                    setIsLoggedIn(false);
                    setUser(null);
                  }}
                >
                  Logout
                </button>
              </div>
            )}
          </>
        )}
      </main>
      
      <footer className="app-footer">
        <p>&copy; 2023 FoodCycle. Connecting food donors with recipients to reduce waste and fight hunger.</p>
      </footer>
    </div>
  );
}

export default App; 