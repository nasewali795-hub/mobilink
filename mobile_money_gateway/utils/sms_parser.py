import re
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ParsedSMS:
    transaction_id: Optional[str]
    amount: Optional[float]
    new_balance: Optional[float]
    reference: Optional[str]
    status: str
    raw_message: str
    sender: Optional[str] = None


class SMSParser:
    PATTERNS = [
        {
            "network": "MTN",
            "success_pattern": r"(?:Y'ello.*(?:received|sent).*ID[:\s]*|Txn\s*ID[:\s]*|ref[:\s]*)([0-9]{10,20})",
            "amount_pattern": r"(?:received|sent|amount)[:\s]*(?:K|ZMW)\s*([\d,]+\.?\d*)",
            "balance_pattern": r"(?:new\s+balance|available\s+balance)[:\s]*(?:K|ZMW)\s*([\d,]+\.?\d*)",
        },
        {
            "network": "Airtel",
            "success_pattern": r"(?:Trans\.?\s*ID[:\s]*|Txn\s*ID[:\s]*|ref[:\s]*)([A-Z0-9]{8,20})",
            "amount_pattern": r"(?:received|sent|amount)[:\s]*(?:K|ZMW)\s*([\d,]+\.?\d*)",
            "balance_pattern": r"(?:new\s+balance|available\s+balance)[:\s]*(?:K|ZMW)\s*([\d,]+\.?\d*)",
        },
        {
            "network": "Zamtel",
            "success_pattern": r"(?:Trans\.?\s*ID[:\s]*|Txn\s*ID[:\s]*|ref[:\s]*)([A-Z0-9]{8,20})",
            "amount_pattern": r"(?:received|sent|amount)[:\s]*(?:K|ZMW)\s*([\d,]+\.?\d*)",
            "balance_pattern": r"(?:new\s+balance|available\s+balance)[:\s]*(?:K|ZMW)\s*([\d,]+\.?\d*)",
        },
    ]

    FAILURE_INDICATORS = [
        "failed", "unsuccessful", "declined", "insufficient", "timeout", "error",
        "not allowed", "invalid", "incorrect", "rejected", "could not",
    ]

    @classmethod
    def parse(cls, message: str, sender: Optional[str] = None) -> ParsedSMS:
        message_lower = message.lower()
        is_failure = any(indicator in message_lower for indicator in cls.FAILURE_INDICATORS)

        if is_failure:
            return ParsedSMS(
                transaction_id=None,
                amount=None,
                new_balance=None,
                reference=None,
                status="failed",
                raw_message=message,
                sender=sender,
            )

        transaction_id = cls._extract(message, "success_pattern")
        amount = cls._extract_amount(message)
        new_balance = cls._extract_balance(message)

        status = "success" if (transaction_id or amount or new_balance) else "unrecognized"

        return ParsedSMS(
            transaction_id=transaction_id,
            amount=amount,
            new_balance=new_balance,
            reference=transaction_id,
            status=status,
            raw_message=message,
            sender=sender,
        )

    @classmethod
    def _extract(cls, message: str, pattern_key: str):
        for pattern_def in cls.PATTERNS:
            pattern = pattern_def.get(pattern_key)
            if pattern:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        return None

    @classmethod
    def _extract_amount(cls, message: str) -> Optional[float]:
        for pattern_def in cls.PATTERNS:
            pattern = pattern_def.get("amount_pattern")
            if pattern:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    raw = match.group(1).replace(",", "")
                    try:
                        return float(raw)
                    except ValueError:
                        continue
        generic_match = re.search(r"(?:K|ZMW|MWK)?\s*([\d,]+\.?\d*)", message)
        if generic_match:
            try:
                return float(generic_match.group(1).replace(",", ""))
            except ValueError:
                pass
        return None

    @classmethod
    def _extract_balance(cls, message: str) -> Optional[float]:
        for pattern_def in cls.PATTERNS:
            pattern = pattern_def.get("balance_pattern")
            if pattern:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    raw = match.group(1).replace(",", "")
                    try:
                        return float(raw)
                    except ValueError:
                        continue
        return None

    @classmethod
    def is_mno_notification(cls, message: str) -> bool:
        mno_keywords = [
            "transaction", "received", "sent", "balance", "airtime", "mobile money",
            "mtn", "airtel", "zamtel", "mno", "payment", "confirmed",
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in mno_keywords)
