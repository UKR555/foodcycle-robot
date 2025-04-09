import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import mapService from '../../services/mapService';
import './Map.css';

const Map = ({
  center,
  zoom,
  markers,
  onMarkerClick,
  className,
  height = '400px'
}) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);

  useEffect(() => {
    const initializeMap = async () => {
      if (mapRef.current) {
        try {
          mapInstanceRef.current = await mapService.initializeMap(
            mapRef.current,
            center,
            zoom
          );
        } catch (error) {
          console.error('Failed to initialize map:', error);
        }
      }
    };

    initializeMap();

    return () => {
      mapService.clearMarkers();
    };
  }, [center, zoom]);

  useEffect(() => {
    if (mapInstanceRef.current && markers) {
      mapService.clearMarkers();
      markers.forEach(({ position, title, icon, infoWindow }) => {
        const marker = mapService.addMarker(position, title, icon);
        if (marker && infoWindow) {
          mapService.addInfoWindow(marker, infoWindow);
        }
        if (marker && onMarkerClick) {
          marker.addListener('click', () => onMarkerClick(marker));
        }
      });
    }
  }, [markers, onMarkerClick]);

  return (
    <div
      ref={mapRef}
      className={`map-container ${className || ''}`}
      style={{ height }}
    />
  );
};

Map.propTypes = {
  center: PropTypes.shape({
    lat: PropTypes.number.isRequired,
    lng: PropTypes.number.isRequired
  }),
  zoom: PropTypes.number,
  markers: PropTypes.arrayOf(
    PropTypes.shape({
      position: PropTypes.shape({
        lat: PropTypes.number.isRequired,
        lng: PropTypes.number.isRequired
      }).isRequired,
      title: PropTypes.string.isRequired,
      icon: PropTypes.string,
      infoWindow: PropTypes.string
    })
  ),
  onMarkerClick: PropTypes.func,
  className: PropTypes.string,
  height: PropTypes.string
};

export default Map; 