# FoodCycle Bot

A system that connects food donors with recipients to reduce food waste and fight hunger.

## Project Structure

- **backend/**: Node.js server and API endpoints
- **frontend/**: React-based web interface
- **agents/**: Python-based intelligent agents for processing and recommendations
- **database/**: SQLite database for storing application data

## Features

- Real-time chat interface for donors and recipients
- Intelligent matching of food donations with recipients
- Insights on food waste reduction and impact
- Recommendation system for optimal distribution

## Getting Started

1. Install dependencies:
   ```
   npm install
   pip install -r requirements.txt
   ```

2. Start the backend server:
   ```
   npm run server
   ```

3. Start the frontend application:
   ```
   npm run client
   ```

4. Run the agents:
   ```
   python agents/donorAgent.py
   ```

## Technologies

- Node.js and Express for the backend
- React for the frontend
- Python for intelligent agents
- SQLite for database
- Socket.io for real-time communication
