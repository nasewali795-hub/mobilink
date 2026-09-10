from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from mobile_money_gateway.models.models import Booth, BoothStatus, User, UserStatus, SystemConfig, AdminActionLog
import hashlib
import os

class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def _log_admin_action(self, admin_id: str, action_type: str, target_booth: Optional[str] = None):
        log = AdminActionLog(
            admin_id=admin_id,
            action_type=action_type,
            target_booth=target_booth
        )
        self.db.add(log)
        self.db.commit()

    def block_booth(self, booth_id: str, admin_id: str):
        booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
        if booth:
            booth.status = BoothStatus.BLOCKED
            self.db.commit()
            self._log_admin_action(admin_id, f"BLOCKED_BOOTH", target_booth=booth_id)
        return booth

    def suspend_booth(self, booth_id: str, admin_id: str, duration_hours: int = 24):
        booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
        if booth:
            booth.status = BoothStatus.SUSPENDED
            booth.suspend_until = datetime.utcnow() + timedelta(hours=duration_hours)
            self.db.commit()
            self._log_admin_action(admin_id, f"SUSPENDED_BOOTH_{duration_hours}H", target_booth=booth_id)
        return booth

    def delete_booth(self, booth_id: str, admin_id: str):
        booth = self.db.query(Booth).filter(Booth.id == booth_id).first()
        if booth:
            self.db.delete(booth)
            self.db.commit()
            self._log_admin_action(admin_id, f"DELETED_BOOTH")
        return True

    def reset_operator_password(self, operator_id: str, admin_id: str):
        operator = self.db.query(User).filter(User.id == operator_id).first()
        new_password = None
        if operator:
            new_password = os.urandom(4).hex()
            operator.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            self.db.commit()
            self._log_admin_action(admin_id, f"RESET_PASSWORD_OPERATOR_{operator_id}")
        return new_password

    def deactivate_operator(self, operator_id: str, admin_id: str):
        operator = self.db.query(User).filter(User.id == operator_id).first()
        if operator:
            operator.status = UserStatus.INACTIVE
            self.db.commit()
            self._log_admin_action(admin_id, f"DEACTIVATED_OPERATOR_{operator_id}")
        return operator

    def update_transaction_limits(self, network: str, new_limit: str, admin_id: str):
        key = f"transaction_limit_{network}"
        config = self.db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config:
            config.value = str(new_limit)
        else:
            config = SystemConfig(key=key, value=str(new_limit))
            self.db.add(config)
        self.db.commit()
        self._log_admin_action(admin_id, f"UPDATED_TX_LIMIT_{network}")
        return config

    def set_queue_priority(self, rules: str, admin_id: str):
        key = "queue_priority_rules"
        config = self.db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config:
            config.value = rules
        else:
            config = SystemConfig(key=key, value=rules)
            self.db.add(config)
        self.db.commit()
        self._log_admin_action(admin_id, "UPDATED_QUEUE_PRIORITY")
        return config
