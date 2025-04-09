# FoodCycle Bot

A web-based application for managing food donations and distribution using delivery robots. The system helps reduce food waste by connecting food donors with recipients via an automated delivery system.

## Features

- Dashboard with key metrics for donations, recipients, and robot fleet
- Interactive map for visualizing donation locations and planning routes
- Robot fleet management system with status monitoring
- Donation management system with filtering and assignment capabilities

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)

### Local Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/foodcycle-bot.git
   cd foodcycle-bot
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:3000`

## Deployment Options

### Option 1: Deploy to Heroku

1. Create a Heroku account if you don't already have one
2. Install the Heroku CLI and login
   ```
   npm install -g heroku
   heroku login
   ```

3. Create a new Heroku app
   ```
   heroku create foodcycle-bot
   ```

4. Push your code to Heroku
   ```
   git push heroku main
   ```

5. Open your deployed application
   ```
   heroku open
   ```

### Option 2: Deploy to Vercel

1. Install Vercel CLI
   ```
   npm install -g vercel
   ```

2. Deploy to Vercel
   ```
   vercel
   ```

3. For production deployment
   ```
   vercel --prod
   ```

### Option 3: Deploy to Netlify

1. Install Netlify CLI
   ```
   npm install -g netlify-cli
   ```

2. Deploy to Netlify
   ```
   netlify deploy
   ```

3. For production deployment
   ```
   netlify deploy --prod
   ```

### Option 4: Deploy to a VPS (DigitalOcean, AWS, etc.)

1. Set up your server with Node.js installed
2. Clone your repository on the server
3. Install dependencies
   ```
   npm install --production
   ```
4. Start the server
   ```
   npm start
   ```
5. Consider using PM2 for process management
   ```
   npm install -g pm2
   pm2 start server.js
   ```

## Customization

- Update the map center coordinates in `foodcycle_integrated.html` to match your local area
- Customize donation types and colors in the `generateFoodIcons` function
- Modify the simulated data in `donationsData` and `robotsData` arrays to match your real-world data

## Technologies Used

- Frontend: HTML, CSS, JavaScript
- Maps: Leaflet.js with OpenStreetMap
- Charts: Chart.js
- Backend: Node.js with Express
- Database: Ready for MongoDB integration

## License

ISC License
