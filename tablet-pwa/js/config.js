const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    WS_URL: 'ws://YOUR_SERVER_IP:8000/gateway/ws/tablet',
    BOOTH_ID: null,
    RECONNECT_INTERVAL: 3000,
    HEARTBEAT_INTERVAL: 30000,
    TRANSACTION_TIMEOUT: 180000,
    FEES: {
        cash_in: 0.025,
        cash_out: 0.025,
        min_fee: 10
    }
};
