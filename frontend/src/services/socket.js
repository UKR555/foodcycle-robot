import { io } from 'socket.io-client';

const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || 'http://localhost:5000';

class SocketService {
  constructor() {
    this.socket = null;
  }

  connect() {
    if (!this.socket) {
      this.socket = io(SOCKET_URL);
      
      this.socket.on('connect', () => {
        console.log('Connected to Socket.IO server');
      });

      this.socket.on('disconnect', () => {
        console.log('Disconnected from Socket.IO server');
      });
    }
    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  joinChatRoom(roomId) {
    if (this.socket) {
      this.socket.emit('join_room', roomId);
    }
  }

  leaveChatRoom(roomId) {
    if (this.socket) {
      this.socket.emit('leave_room', roomId);
    }
  }

  sendMessage(roomId, message) {
    if (this.socket) {
      this.socket.emit('send_message', { roomId, message });
    }
  }

  onNewMessage(callback) {
    if (this.socket) {
      this.socket.on('new_message', callback);
    }
  }

  onDonationRequest(callback) {
    if (this.socket) {
      this.socket.on('donation_request', callback);
    }
  }

  onDonationStatusUpdate(callback) {
    if (this.socket) {
      this.socket.on('donation_status_update', callback);
    }
  }
}

export default new SocketService(); 