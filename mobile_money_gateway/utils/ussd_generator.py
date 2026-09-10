class USSDGenerator:
    """
    Generates USSD string sequences for hardware gateways to execute.
    """

    @staticmethod
    def airtel_zambia_withdraw(agent_code: str, amount: float, pin: str) -> str:
        """
        Generates the USSD string for a customer to withdraw cash at an agent.
        Typically *115# -> 2 (Get Cash) -> 1 (From Agent) -> Agent Code -> Amount -> PIN
        Note: The customer dials this, but the Gateway can use this for automated testing or internal transfers.
        """
        # Format: *115*2*1*AgentCode*Amount*PIN#
        return f"*115*2*1*{agent_code}*{int(amount)}*{pin}#"

    @staticmethod
    def airtel_zambia_deposit(customer_phone: str, amount: float, pin: str) -> str:
        """
        Generates the USSD string for the Agent (Gateway) to deposit cash into a customer's wallet.
        Typically *115# -> 1 (Send Money) -> 1 (To Airtel) -> Phone -> Amount -> PIN
        """
        # Format: *115*1*1*CustomerPhone*Amount*PIN#
        return f"*115*1*1*{customer_phone}*{int(amount)}*{pin}#"

    @staticmethod
    def mtn_zambia_deposit(customer_phone: str, amount: float, pin: str) -> str:
        """
        Generates the USSD string for the Agent (Gateway) to deposit cash into a customer's MTN wallet.
        Typically *303# -> 1 (Send Money) -> 1 (To MTN) -> Phone -> Amount -> PIN
        """
        return f"*303*1*1*{customer_phone}*{int(amount)}*{pin}#"

    @staticmethod
    def mtn_zambia_withdraw(agent_code: str, amount: float, pin: str) -> str:
        """
        Generates the USSD string for a customer to withdraw cash at an MTN agent.
        Typically *303# -> 2 (Withdraw) -> Agent Code -> Amount -> PIN
        """
        return f"*303*2*{agent_code}*{int(amount)}*{pin}#"

    @staticmethod
    def zamtel_zambia_deposit(customer_phone: str, amount: float, pin: str) -> str:
        """
        Generates the USSD string for Zamtel deposit.
        Typically *344# -> 1 (Send Money) -> 1 (To Zamtel) -> Phone -> Amount -> PIN
        """
        return f"*344*1*1*{customer_phone}*{int(amount)}*{pin}#"

    @staticmethod
    def zamtel_zambia_withdraw(agent_code: str, amount: float, pin: str) -> str:
        """
        Generates the USSD string for Zamtel withdrawal.
        Typically *344# -> 2 (Withdraw) -> Agent Code -> Amount -> PIN
        """
        return f"*344*2*{agent_code}*{int(amount)}*{pin}#"
