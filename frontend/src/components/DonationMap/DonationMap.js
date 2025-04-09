import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import Map from '../Map/Map';
import { donationService } from '../../services/api';
import mapService from '../../services/mapService';
import './DonationMap.css';

const DonationMap = ({ onDonationSelect, filters = {} }) => {
  const [donations, setDonations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [markers, setMarkers] = useState([]);

  useEffect(() => {
    const fetchDonations = async () => {
      try {
        setLoading(true);
        const response = await donationService.getDonations(filters);
        setDonations(response.data);
        
        // Convert donations to markers
        const newMarkers = response.data.map(donation => ({
          position: {
            lat: donation.location.latitude,
            lng: donation.location.longitude
          },
          title: donation.title,
          icon: '/icons/donation-marker.png',
          infoWindow: `
            <div class="donation-info">
              <h3>${donation.title}</h3>
              <p>${donation.description}</p>
              <p>Quantity: ${donation.quantity}</p>
              <p>Expiry: ${new Date(donation.expiryDate).toLocaleDateString()}</p>
              <p>Status: ${donation.status}</p>
            </div>
          `
        }));
        
        setMarkers(newMarkers);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching donations:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDonations();
  }, [filters]);

  const handleMarkerClick = (marker) => {
    const donation = donations.find(d => 
      d.location.latitude === marker.getPosition().lat() &&
      d.location.longitude === marker.getPosition().lng()
    );
    if (donation && onDonationSelect) {
      onDonationSelect(donation);
    }
  };

  if (loading) {
    return <div className="donation-map-loading">Loading map...</div>;
  }

  if (error) {
    return <div className="donation-map-error">Error: {error}</div>;
  }

  return (
    <div className="donation-map">
      <Map
        center={{ lat: 20.5937, lng: 78.9629 }} // Default to India center
        zoom={5}
        markers={markers}
        onMarkerClick={handleMarkerClick}
        className="donation-map-container"
        height="600px"
      />
      <div className="donation-map-legend">
        <h4>Legend</h4>
        <div className="legend-item">
          <img src="/icons/donation-marker.png" alt="Donation" />
          <span>Available Donation</span>
        </div>
        <div className="legend-item">
          <img src="/icons/donation-marker-pending.png" alt="Pending" />
          <span>Pending Donation</span>
        </div>
        <div className="legend-item">
          <img src="/icons/donation-marker-completed.png" alt="Completed" />
          <span>Completed Donation</span>
        </div>
      </div>
    </div>
  );
};

DonationMap.propTypes = {
  onDonationSelect: PropTypes.func,
  filters: PropTypes.shape({
    status: PropTypes.string,
    category: PropTypes.string,
    distance: PropTypes.number,
    latitude: PropTypes.number,
    longitude: PropTypes.number
  })
};

export default DonationMap; 