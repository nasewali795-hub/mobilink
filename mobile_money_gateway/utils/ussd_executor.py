from typing import Optional, List, Dict
from enum import Enum


class USSDNetwork(str, Enum):
    MTN = "MTN"
    AIRTEL = "Airtel"
    ZAMTEL = "Zamtel"


class USSDOperation(str, Enum):
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"
    BALANCE_CHECK = "balance_check"
    MINI_STATEMENT = "mini_statement"


class USSDCommand:
    def __init__(self, network: USSDNetwork, operation: USSDOperation, slot_index: str):
        self.network = network
        self.operation = operation
        self.slot_index = slot_index
        self.steps: List[Dict] = []

    def build(self, phone_number: str, amount: float, pin: Optional[str] = None) -> List[Dict]:
        if self.network == USSDNetwork.MTN:
            return self._build_mtn(phone_number, amount, pin)
        elif self.network == USSDNetwork.AIRTEL:
            return self._build_airtel(phone_number, amount, pin)
        elif self.network == USSDNetwork.ZAMTEL:
            return self._build_zamtel(phone_number, amount, pin)
        return []

    def _build_mtn(self, phone_number: str, amount: float, pin: Optional[str] = None) -> List[Dict]:
        steps = []
        if self.operation == USSDOperation.CASH_OUT:
            steps.extend([
                {"type": "ussd", "code": "*111#", "sim_slot": self.slot_index},
                {"type": "ussd_response", "expected_pattern": r"(?:Send Money|Transfer)"},
                {"type": "ussd_input", "value": "1"},
                {"type": "ussd_response", "expected_pattern": r"(?:Enter.*number|Phone)"},
                {"type": "ussd_input", "value": phone_number},
                {"type": "ussd_response", "expected_pattern": r"(?:amount|Enter)"},
                {"type": "ussd_input", "value": str(int(amount))},
                {"type": "ussd_response", "expected_pattern": r"(?:PIN|password)"},
                {"type": "ussd_input", "value": pin or ""},
            ])
        elif self.operation == USSDOperation.CASH_IN:
            steps.extend([
                {"type": "ussd", "code": "*112#", "sim_slot": self.slot_index},
                {"type": "ussd_response", "expected_pattern": r"(?:Receive Money|Deposit)"},
                {"type": "ussd_input", "value": "1"},
                {"type": "ussd_response", "expected_pattern": r"(?:Enter.*number|Phone)"},
                {"type": "ussd_input", "value": phone_number},
                {"type": "ussd_response", "expected_pattern": r"(?:amount|Enter)"},
                {"type": "ussd_input", "value": str(int(amount))},
            ])
        return steps

    def _build_airtel(self, phone_number: str, amount: float, pin: Optional[str] = None) -> List[Dict]:
        steps = []
        if self.operation == USSDOperation.CASH_OUT:
            steps.extend([
                {"type": "ussd", "code": "*115#", "sim_slot": self.slot_index},
                {"type": "ussd_response", "expected_pattern": r"(?:Send Money|Transfer)"},
                {"type": "ussd_input", "value": "1"},
                {"type": "ussd_response", "expected_pattern": r"(?:Enter.*number|Phone)"},
                {"type": "ussd_input", "value": phone_number},
                {"type": "ussd_response", "expected_pattern": r"(?:amount|Enter)"},
                {"type": "ussd_input", "value": str(int(amount))},
                {"type": "ussd_response", "expected_pattern": r"(?:PIN|password)"},
                {"type": "ussd_input", "value": pin or ""},
            ])
        elif self.operation == USSDOperation.CASH_IN:
            steps.extend([
                {"type": "ussd", "code": "*114#", "sim_slot": self.slot_index},
                {"type": "ussd_response", "expected_pattern": r"(?:Receive Money|Deposit)"},
                {"type": "ussd_input", "value": "1"},
                {"type": "ussd_response", "expected_pattern": r"(?:Enter.*number|Phone)"},
                {"type": "ussd_input", "value": phone_number},
                {"type": "ussd_response", "expected_pattern": r"(?:amount|Enter)"},
                {"type": "ussd_input", "value": str(int(amount))},
            ])
        return steps

    def _build_zamtel(self, phone_number: str, amount: float, pin: Optional[str] = None) -> List[Dict]:
        steps = []
        if self.operation == USSDOperation.CASH_OUT:
            steps.extend([
                {"type": "ussd", "code": "*811#", "sim_slot": self.slot_index},
                {"type": "ussd_response", "expected_pattern": r"(?:Send Money|Transfer)"},
                {"type": "ussd_input", "value": "1"},
                {"type": "ussd_response", "expected_pattern": r"(?:Enter.*number|Phone)"},
                {"type": "ussd_input", "value": phone_number},
                {"type": "ussd_response", "expected_pattern": r"(?:amount|Enter)"},
                {"type": "ussd_input", "value": str(int(amount))},
                {"type": "ussd_response", "expected_pattern": r"(?:PIN|password)"},
                {"type": "ussd_input", "value": pin or ""},
            ])
        elif self.operation == USSDOperation.CASH_IN:
            steps.extend([
                {"type": "ussd", "code": "*810#", "sim_slot": self.slot_index},
                {"type": "ussd_response", "expected_pattern": r"(?:Receive Money|Deposit)"},
                {"type": "ussd_input", "value": "1"},
                {"type": "ussd_response", "expected_pattern": r"(?:Enter.*number|Phone)"},
                {"type": "ussd_input", "value": phone_number},
                {"type": "ussd_response", "expected_pattern": r"(?:amount|Enter)"},
                {"type": "ussd_input", "value": str(int(amount))},
            ])
        return steps

    def to_dict(self) -> Dict:
        return {
            "network": self.network.value,
            "operation": self.operation.value,
            "slot_index": self.slot_index,
            "steps": self.steps,
        }
