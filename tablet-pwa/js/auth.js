const Auth = {
    token: localStorage.getItem('token'),
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    booth: JSON.parse(localStorage.getItem('booth') || 'null'),
    activeShift: JSON.parse(localStorage.getItem('activeShift') || 'null'),

    isAuthenticated() {
        return !!this.token && !!this.user;
    },

    isOperator() {
        return this.user && this.user.role === 'operator';
    },

    isAdmin() {
        return this.user && this.user.role === 'admin';
    },

    async login(username, pin) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, pin }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            this.token = data.access_token;
            this.user = data.user;
            
            localStorage.setItem('token', this.token);
            localStorage.setItem('user', JSON.stringify(this.user));
            
            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    },

    async getProfile() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to get profile');
            }

            this.user = await response.json();
            localStorage.setItem('user', JSON.stringify(this.user));
            return this.user;
        } catch (error) {
            console.error('Get profile error:', error);
            throw error;
        }
    },

    logout() {
        this.token = null;
        this.user = null;
        this.booth = null;
        this.activeShift = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('booth');
        localStorage.removeItem('activeShift');
    },

    getAuthHeader() {
        return {
            'Authorization': `Bearer ${this.token}`,
        };
    }
};
