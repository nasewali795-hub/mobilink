# Tablet PWA - Mobile Money Gateway

Booth operator interface for the Multi-Booth Central-SIM Mobile Money Gateway.

## Features

- PIN-based operator authentication
- Shift start with cash declaration
- Cash-In / Cash-Out transaction processing
- Real-time status tracking via WebSocket
- End-of-day reconciliation
- Offline-capable PWA

## Quick Start

1. Update `js/config.js` with your server IP and booth ID
2. Serve the files: `python serve.py`
3. Open `http://localhost:3000` on the booth tablet
4. Login with operator PIN
5. Start shift and process transactions

## Screens

- **PIN Login**: 4-digit operator PIN
- **Shift Start**: Starting cash declaration
- **Transaction Dashboard**: Network/type selection, phone/amount input
- **Status Overlay**: Real-time transaction progress
- **Reconciliation**: End-of-shift cash balancing

## Browser Support

- Chrome/Edge (recommended)
- Safari
- Firefox

## Configuration

Edit `js/config.js`:

```javascript
const CONFIG = {
    API_BASE_URL: 'http://YOUR_SERVER_IP:8000',
    WS_URL: 'ws://YOUR_SERVER_IP:8000/gateway/ws/tablet',
    BOOTH_ID: 'booth-1',
};
```
