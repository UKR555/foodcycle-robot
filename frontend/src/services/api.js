import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to requests if it exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth Service
export const authService = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (userData) => api.post('/auth/register', userData),
  getCurrentUser: () => api.get('/auth/me'),
  updateProfile: (userData) => api.put('/auth/profile', userData)
};

// Donation Service
export const donationService = {
  createDonation: (donationData) => api.post('/donations', donationData),
  getDonations: (filters) => api.get('/donations', { params: filters }),
  getDonationById: (id) => api.get(`/donations/${id}`),
  updateDonation: (id, donationData) => api.put(`/donations/${id}`, donationData),
  deleteDonation: (id) => api.delete(`/donations/${id}`),
  acceptDonation: (id) => api.post(`/donations/${id}/accept`),
  rejectDonation: (id) => api.post(`/donations/${id}/reject`),
  completeDonation: (id) => api.post(`/donations/${id}/complete`)
};

// Chat Service
export const chatService = {
  getChatRooms: () => api.get('/chat/rooms'),
  getChatMessages: (roomId) => api.get(`/chat/rooms/${roomId}/messages`),
  sendMessage: (roomId, message) => api.post(`/chat/rooms/${roomId}/messages`, { message }),
  createChatRoom: (participants) => api.post('/chat/rooms', { participants })
};

// User Service
export const userService = {
  getUsers: (filters) => api.get('/users', { params: filters }),
  getUserById: (id) => api.get(`/users/${id}`),
  updateUser: (id, userData) => api.put(`/users/${id}`, userData),
  deleteUser: (id) => api.delete(`/users/${id}`)
};

// Notification Service
export const notificationService = {
  getNotifications: () => api.get('/notifications'),
  markAsRead: (notificationId) => api.put(`/notifications/${notificationId}/read`),
  markAllAsRead: () => api.put('/notifications/read-all'),
  deleteNotification: (notificationId) => api.delete(`/notifications/${notificationId}`)
};

export default api; 