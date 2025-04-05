const express = require('express');
const router = express.Router();
const db = require('../db/database');

// Get all donations
router.get('/donations', (req, res) => {
  const status = req.query.status || 'available';
  
  db.all(
    `SELECT d.*, u.name as donor_name 
     FROM donations d
     JOIN users u ON d.donor_id = u.id
     WHERE d.status = ?
     ORDER BY d.created_at DESC`,
    [status],
    (err, rows) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      res.json({ donations: rows });
    }
  );
});

// Get donation by ID
router.get('/donations/:id', (req, res) => {
  const { id } = req.params;
  
  db.get(
    `SELECT d.*, u.name as donor_name, u.email as donor_email
     FROM donations d
     JOIN users u ON d.donor_id = u.id
     WHERE d.id = ?`,
    [id],
    (err, donation) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      if (!donation) {
        return res.status(404).json({ error: 'Donation not found' });
      }
      res.json({ donation });
    }
  );
});

// Create a new donation
router.post('/donations', (req, res) => {
  const { 
    donor_id, 
    food_name, 
    quantity, 
    expiry_date, 
    description, 
    location 
  } = req.body;
  
  if (!donor_id || !food_name || !quantity) {
    return res.status(400).json({ error: 'Missing required fields' });
  }
  
  db.run(
    `INSERT INTO donations (
      donor_id, food_name, quantity, expiry_date, description, location
    ) VALUES (?, ?, ?, ?, ?, ?)`,
    [donor_id, food_name, quantity, expiry_date, description, location],
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      // Get the newly created donation
      db.get(
        `SELECT * FROM donations WHERE id = ?`,
        [this.lastID],
        (err, donation) => {
          if (err) {
            return res.status(500).json({ error: err.message });
          }
          res.status(201).json({ 
            message: 'Donation created successfully',
            donation 
          });
        }
      );
    }
  );
});

// Update donation status
router.patch('/donations/:id', (req, res) => {
  const { id } = req.params;
  const { status } = req.body;
  
  if (!status) {
    return res.status(400).json({ error: 'Status is required' });
  }
  
  if (!['available', 'reserved', 'completed'].includes(status)) {
    return res.status(400).json({ error: 'Invalid status value' });
  }
  
  db.run(
    `UPDATE donations SET status = ? WHERE id = ?`,
    [status, id],
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      if (this.changes === 0) {
        return res.status(404).json({ error: 'Donation not found' });
      }
      
      res.json({ 
        message: 'Donation status updated successfully',
        id,
        status
      });
    }
  );
});

// Delete a donation
router.delete('/donations/:id', (req, res) => {
  const { id } = req.params;
  
  db.run(
    `DELETE FROM donations WHERE id = ?`,
    [id],
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      if (this.changes === 0) {
        return res.status(404).json({ error: 'Donation not found' });
      }
      
      res.json({ message: 'Donation deleted successfully', id });
    }
  );
});

// Get donations by user (donor)
router.get('/users/:userId/donations', (req, res) => {
  const { userId } = req.params;
  
  db.all(
    `SELECT * FROM donations WHERE donor_id = ? ORDER BY created_at DESC`,
    [userId],
    (err, rows) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      res.json({ donations: rows });
    }
  );
});

module.exports = router; 