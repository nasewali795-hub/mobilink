# Multi-Booth Central-SIM Mobile Money Gateway

A distributed point-of-sale (POS) network for multi-booth mobile money transactions with a centralized SIM gateway.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Booth      │     │  Backend    │     │  Gateway    │
│  Tablet     │────▶│  Server     │────▶│  Android    │
│  (PWA)      │◀────│  (FastAPI)  │◀────│  Phone      │
│             │ WS  │             │ WS  │             │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          │ REST API
                          ▼
                   ┌─────────────┐
                   │  SQLite DB  │
                   └─────────────┘
```

## Components

### Backend (`mobile_money_gateway/`)
- **FastAPI** REST API + WebSocket server
- **SQLAlchemy** ORM with SQLite database
- **JWT** authentication
- **Queue Engine**: SIM-specific sequential transaction queues
- **SMS Parser**: Regex-based MNO confirmation parsing
- **Float Tracker**: Real-time balance management

### Android Gateway (`GatewayApp/`)
- **GatewayService**: Foreground service with WebSocket client
- **USDDListenerService**: Accessibility service for USSD interception
- **SMSReceiver**: Broadcast receiver for MNO confirmations
- **DualSimManager**: SIM slot selection and subscription management
- **USSDExecutor**: MTN/Airtel/Zamtel step builders

### Tablet PWA (`tablet-pwa/`)
- **PIN Login**: 4-digit operator authentication
- **Shift Management**: Start/close with cash declaration
- **Transaction Dashboard**: Network/type selection, form validation
- **Live Status**: Real-time progress via WebSocket
- **Reconciliation**: End-of-shift cash balancing

## Quick Start

### 1. Start Backend
```bash
cd mobile_money_gateway
pip install -r requirements.txt
python ../run_gateway.py
```
Server runs at `http://0.0.0.0:8000`

### 2. Build Android Gateway
```bash
cd GatewayApp
# Open in Android Studio and build APK
# Install on gateway device
# Enable Accessibility Service
```

### 3. Start Tablet PWA
```bash
cd tablet-pwa
python serve.py
```
Open `http://localhost:3000` on booth tablets.

## Configuration

### Backend
Edit `mobile_money_gateway/.env`:
```env
DATABASE_URL=sqlite:///./mobile_money_gateway.db
SECRET_KEY=your-secret-key
```

### Android Gateway
Update WebSocket URL in `GatewayApp/app/src/main/java/com/mobilemoney/gateway/service/GatewayService.kt`:
```kotlin
val serverUri = URI.create("ws://YOUR_SERVER_IP:8000/gateway/ws/connect/gateway-1")
```

### Tablet PWA
Update `tablet-pwa/js/config.js`:
```javascript
const CONFIG = {
    API_BASE_URL: 'http://YOUR_SERVER_IP:8000',
    WS_URL: 'ws://YOUR_SERVER_IP:8000/gateway/ws/tablet',
    BOOTH_ID: 'booth-1',
};
```

## API Endpoints

### Authentication
- `POST /auth/login` - Operator/Admin login
- `POST /auth/register` - Create new user (admin only)
- `GET /auth/me` - Current user profile

### Transactions
- `POST /transactions` - Create new transaction
- `GET /transactions/{id}` - Get transaction details
- `GET /transactions/shift/{shift_id}` - Get shift transactions
- `POST /transactions/{id}/cancel` - Cancel transaction

### Shifts
- `POST /shifts/start?booth_id={id}` - Start new shift
- `POST /shifts/{id}/close` - Close shift with reconciliation
- `GET /shifts/operator/me` - Get operator's shifts

### SIM Cards
- `POST /sim-cards` - Register SIM card (admin only)
- `GET /sim-cards` - List all SIM cards
- `PATCH /sim-cards/{id}/status` - Update SIM status

### Admin
- `GET /admin/balances` - Get all float balances
- `POST /admin/float/adjust` - Adjust SIM float
- `GET /admin/transactions/pending-review` - Manual review queue

### Gateway
- `WS /gateway/ws/connect/{gateway_id}` - Gateway WebSocket
- `WS /gateway/ws/tablet/{booth_id}` - Tablet WebSocket
- `POST /gateway/sms/inbound` - SMS webhook

## Database Schema

- `users` - Operators and admins
- `sim_cards` - Master SIM cards with float balances
- `booths` - Booth locations
- `shifts` - Operator shifts with cash reconciliation
- `transactions` - Transaction records with state machine
- `float_adjustments` - Float adjustment audit trail

## Transaction Flow

1. Operator enters transaction on tablet
2. Tablet sends POST to backend
3. Backend validates float and queues transaction
4. Backend dispatches via WebSocket to gateway phone
5. Gateway executes USSD steps
6. MNO sends SMS confirmation
7. Gateway parses SMS and sends to backend
8. Backend updates status and notifies tablet

## Transaction States

- `pending` - Queued for processing
- `processing` - USSD in progress
- `success` - Completed successfully
- `failed` - Transaction failed
- `requires_manual_review` - SMS parsing failed

## Security

- TLS/WSS encryption for all communications
- JWT-based authentication
- Role-based access control (admin/operator)
- PIN hashing with bcrypt
- Fallback logging for manual review

## License

Proprietary
