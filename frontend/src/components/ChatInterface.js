import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import './ChatInterface.css';

const ChatInterface = ({ userId, recipientId, userName, recipientName }) => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [socket, setSocket] = useState(null);
  const messagesEndRef = useRef(null);

  // Generate a unique room ID from the user IDs (smaller one first)
  const roomId = userId < recipientId 
    ? `${userId}-${recipientId}` 
    : `${recipientId}-${userId}`;

  // Initialize socket connection
  useEffect(() => {
    // Connect to the server
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);

    // Join chat room
    newSocket.emit('join_room', roomId);

    // Clean up on component unmount
    return () => {
      newSocket.disconnect();
    };
  }, [roomId]);

  // Listen for incoming messages
  useEffect(() => {
    if (!socket) return;

    socket.on('receive_message', (data) => {
      setMessages((prevMessages) => [...prevMessages, data]);
    });

    // Clean up the event listener
    return () => {
      socket.off('receive_message');
    };
  }, [socket]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle message submission
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (message.trim() === '') return;
    
    const messageData = {
      sender_id: userId,
      sender_name: userName,
      recipient_id: recipientId,
      recipient_name: recipientName,
      message: message,
      roomId: roomId,
      time: new Date().toLocaleTimeString()
    };
    
    // Send message to server
    socket.emit('send_message', messageData);
    
    // Add message to local state
    setMessages((prevMessages) => [...prevMessages, messageData]);
    
    // Clear input field
    setMessage('');
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h3>Chat with {recipientName}</h3>
      </div>
      
      <div className="messages-container">
        {messages.map((msg, index) => (
          <div 
            key={index} 
            className={`message ${msg.sender_id === userId ? 'sent' : 'received'}`}
          >
            <div className="message-content">
              <p>{msg.message}</p>
              <span className="timestamp">{msg.time}</span>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <form className="message-form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Type a message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
};

export default ChatInterface; 