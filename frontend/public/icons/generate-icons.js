const fs = require('fs');
const { createCanvas } = require('canvas');

// Function to create a marker icon
function createMarkerIcon(color, text) {
  const canvas = createCanvas(32, 32);
  const ctx = canvas.getContext('2d');
  
  // Draw marker shape
  ctx.beginPath();
  ctx.moveTo(16, 0);
  ctx.lineTo(32, 32);
  ctx.lineTo(0, 32);
  ctx.closePath();
  
  // Fill with color
  ctx.fillStyle = color;
  ctx.fill();
  
  // Add text
  ctx.fillStyle = 'white';
  ctx.font = 'bold 12px Arial';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 16, 16);
  
  return canvas.toBuffer();
}

// Create icons directory if it doesn't exist
if (!fs.existsSync('./frontend/public/icons')) {
  fs.mkdirSync('./frontend/public/icons', { recursive: true });
}

// Generate icons
const icons = [
  { name: 'donation-marker.png', color: '#4CAF50', text: 'D' },
  { name: 'donation-marker-pending.png', color: '#FFC107', text: 'P' },
  { name: 'donation-marker-completed.png', color: '#2196F3', text: 'C' }
];

icons.forEach(icon => {
  const buffer = createMarkerIcon(icon.color, icon.text);
  fs.writeFileSync(`./frontend/public/icons/${icon.name}`, buffer);
  console.log(`Created ${icon.name}`);
}); 