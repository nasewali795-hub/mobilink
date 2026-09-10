class WebSocketManager {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.reconnectTimer = null;
        this.heartbeatTimer = null;
        this.listeners = {};
    }

    connect(boothId) {
        if (this.ws && this.connected) {
            return;
        }

        const url = `${CONFIG.WS_URL}/${boothId}`;
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.connected = true;
            this.startHeartbeat();
            this.emit('connected');
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e);
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.connected = false;
            this.stopHeartbeat();
            this.emit('disconnected');
            this.scheduleReconnect(boothId);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.emit('error', error);
        };
    }

    handleMessage(data) {
        console.log('WebSocket message:', data);
        
        switch (data.type) {
            case 'transaction_update':
                this.emit('transaction_update', data);
                break;
            case 'pong':
                this.emit('pong');
                break;
            case 'sim_status':
                this.emit('sim_status', data);
                break;
            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    send(data) {
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected, cannot send:', data);
        }
    }

    scheduleReconnect(boothId) {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
        this.reconnectTimer = setTimeout(() => {
            console.log('Attempting to reconnect...');
            this.connect(boothId);
        }, CONFIG.RECONNECT_INTERVAL);
    }

    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatTimer = setInterval(() => {
            this.send({ type: 'ping' });
        }, CONFIG.HEARTBEAT_INTERVAL);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    disconnect() {
        this.stopHeartbeat();
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
    }

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    }
}

const wsManager = new WebSocketManager();
