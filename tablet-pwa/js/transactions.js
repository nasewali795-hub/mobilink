const Transactions = {
    async createTransaction(transactionData) {
        try {
            const type = transactionData.transaction_type;
            const endpoint = type === 'balance' ? 'balance' : (type === 'deposit' ? 'deposit' : 'withdraw');
            const response = await fetch(`${CONFIG.API_BASE_URL}/transactions/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...Auth.getAuthHeader(),
                },
                body: JSON.stringify(transactionData),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Transaction failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Create transaction error:', error);
            throw error;
        }
    },

    async getTransaction(transactionId) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/transactions/${transactionId}`, {
                headers: {
                    ...Auth.getAuthHeader(),
                },
            });

            if (!response.ok) {
                throw new Error('Transaction not found');
            }

            return await response.json();
        } catch (error) {
            console.error('Get transaction error:', error);
            throw error;
        }
    },

    async getShiftTransactions(shiftId) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/transactions/shift/${shiftId}`, {
                headers: {
                    ...Auth.getAuthHeader(),
                },
            });

            if (!response.ok) {
                throw new Error('Failed to get shift transactions');
            }

            return await response.json();
        } catch (error) {
            console.error('Get shift transactions error:', error);
            throw error;
        }
    },

    calculateFee(amount, type) {
        if (type === 'balance') return 0;
        const feeRate = type === 'deposit' ? CONFIG.FEES.cash_in : CONFIG.FEES.cash_out;
        const fee = amount * feeRate;
        return Math.max(fee, CONFIG.FEES.min_fee);
    },

    formatCurrency(amount) {
        return `K ${parseFloat(amount).toFixed(2)}`;
    },

    formatPhoneNumber(phone) {
        const cleaned = phone.replace(/\D/g, '');
        if (cleaned.length === 10 && cleaned.startsWith('0')) {
            return cleaned.replace(/(\d{4})(\d{3})(\d{3})/, '$1 $2 $3');
        }
        return phone;
    },

    validatePhoneNumber(phone) {
        const cleaned = phone.replace(/\s/g, '');
        return /^[0-9]{10,13}$/.test(cleaned);
    },

    validateAmount(amount) {
        const num = parseFloat(amount);
        return !isNaN(num) && num > 0 && num <= CONFIG.MAX_TRANSACTION_AMOUNT;
    }
};
