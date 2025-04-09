// Map Service for handling map functionality
// This service uses Leaflet.js with OpenStreetMap (free alternative to Google Maps)

let map = null;
let markers = [];

/**
 * Initialize the map
 * @param {HTMLElement} container - The container element for the map
 * @param {Object} center - The center coordinates {lat, lng}
 * @param {number} zoom - The zoom level
 * @returns {Promise} - Resolves when the map is initialized
 */
const initializeMap = (container, center, zoom = 12) => {
  return new Promise((resolve, reject) => {
    try {
      // Initialize the map
      map = L.map(container).setView([center.lat, center.lng], zoom);
      
      // Add OpenStreetMap tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);
      
      resolve(map);
    } catch (error) {
      console.error('Error initializing map:', error);
      reject(error);
    }
  });
};

/**
 * Add a marker to the map
 * @param {Object} position - The position coordinates {lat, lng}
 * @param {string} title - The marker title
 * @param {string} iconUrl - The URL of the marker icon
 * @returns {Object} - The marker object
 */
const addMarker = (position, title, iconUrl) => {
  if (!map) return null;
  
  // Create custom icon
  const icon = L.icon({
    iconUrl: iconUrl || '/icons/default-marker.png',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32]
  });
  
  // Create marker
  const marker = L.marker([position.lat, position.lng], {
    icon: icon,
    title: title
  }).addTo(map);
  
  markers.push(marker);
  return marker;
};

/**
 * Add a food donation marker to the map
 * @param {Object} position - The position coordinates {lat, lng}
 * @param {Object} donation - The donation data object with details
 * @returns {Object} - The marker object
 */
const addFoodMarker = (position, donation) => {
  if (!map) return null;

  // Get appropriate food icon based on food type
  const iconUrl = getFoodIconUrl(donation.foodType || donation.item);
  
  // Create custom icon with round frame for food
  const icon = L.icon({
    iconUrl: iconUrl,
    iconSize: [50, 50],
    iconAnchor: [25, 50],
    popupAnchor: [0, -45],
    className: 'food-marker-icon' // This allows styling via CSS
  });
  
  // Create marker
  const marker = L.marker([position.lat, position.lng], {
    icon: icon,
    title: donation.item,
    donation: donation // Store donation data in marker for access in popup
  }).addTo(map);
  
  // Create an enhanced popup with detailed donation information
  const popupContent = createDonationPopupContent(donation);
  marker.bindPopup(popupContent, {
    maxWidth: 300,
    className: 'donation-popup'
  });
  
  markers.push(marker);
  return marker;
};

/**
 * Generate a food icon URL based on food type
 * @param {string} foodType - The type of food
 * @returns {string} - The URL to the appropriate food icon
 */
const getFoodIconUrl = (foodType) => {
  // Map food types to appropriate icons
  const foodIcons = {
    'vegetables': '/icons/food/vegetables.png',
    'fruits': '/icons/food/fruits.png',
    'bread': '/icons/food/bread.png',
    'rice': '/icons/food/rice.png',
    'pasta': '/icons/food/pasta.png',
    'meat': '/icons/food/meat.png',
    'dairy': '/icons/food/dairy.png',
    'canned': '/icons/food/canned.png',
    'dessert': '/icons/food/dessert.png',
    'beverage': '/icons/food/beverage.png',
    'mixed': '/icons/food/mixed.png'
  };
  
  // Default case - search for partial matches
  const normalizedFoodType = foodType.toLowerCase();
  
  // Try to find direct match first
  if (foodIcons[normalizedFoodType]) {
    return foodIcons[normalizedFoodType];
  }
  
  // If not found, check for partial matches
  for (const [key, url] of Object.entries(foodIcons)) {
    if (normalizedFoodType.includes(key) || key.includes(normalizedFoodType)) {
      return url;
    }
  }
  
  // Default food icon if no match
  return '/icons/food/mixed.png';
};

/**
 * Create enhanced HTML content for donation popup
 * @param {Object} donation - The donation object with details
 * @returns {string} - HTML content for the popup
 */
const createDonationPopupContent = (donation) => {
  // Calculate how many people the donation can feed
  const servingsEstimate = donation.servings || estimateServings(donation.quantity, donation.item);
  
  // Format expiration time
  const expirationTime = donation.expirationTime ? 
    new Date(donation.expirationTime).toLocaleString() : 
    'Not specified';
  
  // Create the HTML content
  return `
    <div class="donation-popup-content">
      <h3>${donation.item}</h3>
      <p class="donor"><strong>Donor:</strong> ${donation.donor}</p>
      <p class="quantity"><strong>Quantity:</strong> ${donation.quantity}</p>
      <p class="servings"><strong>Serves:</strong> Approximately ${servingsEstimate} people</p>
      <p class="freshness"><strong>Best before:</strong> ${expirationTime}</p>
      <p class="location"><strong>Location:</strong> ${donation.location}</p>
      ${donation.description ? `<p class="description">${donation.description}</p>` : ''}
      <div class="actions">
        <button class="btn-primary" onclick="window.claimDonation('${donation.id}')">Claim</button>
        <button class="btn-secondary" onclick="window.getDirections(${position.lat}, ${position.lng})">Directions</button>
      </div>
    </div>
  `;
};

/**
 * Estimate how many people a food donation can serve
 * @param {string} quantity - The quantity string (e.g., "5kg", "10 loaves")
 * @param {string} foodType - The type of food
 * @returns {number} - Estimated number of people that can be served
 */
const estimateServings = (quantity, foodType) => {
  // Extract numeric value from quantity
  const match = quantity.match(/(\d+(\.\d+)?)/);
  if (!match) return 'unknown number of';
  
  const numericValue = parseFloat(match[1]);
  
  // Estimate servings based on food type
  const servingsMap = {
    'rice': 5, // people per kg
    'pasta': 6, // people per kg
    'bread': 2, // people per loaf
    'vegetables': 3, // people per kg
    'fruits': 4, // people per kg
    'canned': 2, // people per can
    'meat': 4, // people per kg
    'meals': 1 // people per meal (direct)
  };
  
  // Handle special cases in quantity units
  if (quantity.toLowerCase().includes('meal') || quantity.toLowerCase().includes('portion')) {
    return numericValue;
  }
  
  if (quantity.toLowerCase().includes('kg') || quantity.toLowerCase().includes('kilo')) {
    // Find best matching food type
    for (const [key, servingsPerUnit] of Object.entries(servingsMap)) {
      if (foodType.toLowerCase().includes(key)) {
        return Math.round(numericValue * servingsPerUnit);
      }
    }
    // Default for kg if no specific match
    return Math.round(numericValue * 4);
  }
  
  if (quantity.toLowerCase().includes('loaves') || quantity.toLowerCase().includes('loaf')) {
    return Math.round(numericValue * 2);
  }
  
  if (quantity.toLowerCase().includes('cans') || quantity.toLowerCase().includes('can')) {
    return Math.round(numericValue * 2);
  }
  
  // Default estimate - rough approximation
  return Math.round(numericValue * 3);
};

/**
 * Add an info window to a marker
 * @param {Object} marker - The marker object
 * @param {string} content - The HTML content for the info window
 * @returns {Object} - The marker with the info window
 */
const addInfoWindow = (marker, content) => {
  if (!marker) return null;
  
  marker.bindPopup(content);
  return marker;
};

/**
 * Remove a marker from the map
 * @param {Object} marker - The marker object to remove
 */
const removeMarker = (marker) => {
  if (!map || !marker) return;
  
  map.removeLayer(marker);
  markers = markers.filter(m => m !== marker);
};

/**
 * Clear all markers from the map
 */
const clearMarkers = () => {
  if (!map) return;
  
  markers.forEach(marker => {
    map.removeLayer(marker);
  });
  
  markers = [];
};

/**
 * Set the map center and zoom
 * @param {Object} center - The center coordinates {lat, lng}
 * @param {number} zoom - The zoom level
 */
const setCenterAndZoom = (center, zoom) => {
  if (!map) return;
  
  map.setView([center.lat, center.lng], zoom);
};

/**
 * Get the current map center
 * @returns {Object} - The center coordinates {lat, lng}
 */
const getCenter = () => {
  if (!map) return { lat: 0, lng: 0 };
  
  const center = map.getCenter();
  return { lat: center.lat, lng: center.lng };
};

/**
 * Get the current map zoom level
 * @returns {number} - The zoom level
 */
const getZoom = () => {
  if (!map) return 12;
  
  return map.getZoom();
};

/**
 * Draw a route between points
 * @param {Array} points - Array of points {lat, lng}
 * @param {Object} options - Route options
 * @returns {Object} - The route object
 */
const drawRoute = (points, options = {}) => {
  if (!map) return null;
  
  const routeCoordinates = points.map(point => [point.lat, point.lng]);
  
  const route = L.polyline(routeCoordinates, {
    color: options.color || '#4CAF50',
    weight: options.weight || 3,
    opacity: options.opacity || 0.8
  }).addTo(map);
  
  return route;
};

/**
 * Geocode an address to coordinates
 * @param {string} address - The address to geocode
 * @returns {Promise} - Resolves with the coordinates {lat, lng}
 */
const geocodeAddress = (address) => {
  return new Promise((resolve, reject) => {
    // Use OpenStreetMap Nominatim API for geocoding
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
      .then(response => response.json())
      .then(data => {
        if (data && data.length > 0) {
          resolve({
            lat: parseFloat(data[0].lat),
            lng: parseFloat(data[0].lon)
          });
        } else {
          reject(new Error('Address not found'));
        }
      })
      .catch(error => {
        console.error('Geocoding error:', error);
        reject(error);
      });
  });
};

/**
 * Reverse geocode coordinates to an address
 * @param {Object} position - The position coordinates {lat, lng}
 * @returns {Promise} - Resolves with the address
 */
const reverseGeocode = (position) => {
  return new Promise((resolve, reject) => {
    // Use OpenStreetMap Nominatim API for reverse geocoding
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.lat}&lon=${position.lng}`)
      .then(response => response.json())
      .then(data => {
        if (data && data.display_name) {
          resolve(data.display_name);
        } else {
          reject(new Error('Location not found'));
        }
      })
      .catch(error => {
        console.error('Reverse geocoding error:', error);
        reject(error);
      });
  });
};

// Export the map service
export const mapService = {
  initializeMap,
  addMarker,
  addFoodMarker,
  getFoodIconUrl,
  estimateServings,
  addInfoWindow,
  removeMarker,
  clearMarkers,
  setCenterAndZoom,
  getCenter,
  getZoom,
  drawRoute,
  geocodeAddress,
  reverseGeocode
}; 