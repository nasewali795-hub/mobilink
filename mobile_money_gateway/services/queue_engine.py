from typing import Optional
from mobile_money_gateway.celery_app import celery_app

class QueueEngine:
    def __init__(self):
        pass

    async def enqueue_transaction(self, sim_card_id: str, transaction_id: str, network_name: str):
        # Dispatch to Celery
        celery_app.send_task(
            "mobile_money_gateway.services.queue_engine.process_ussd_transaction",
            args=[sim_card_id, transaction_id, network_name]
        )
        return 1  # Dummy queue position for Celery

    def get_queue_status(self, sim_card_id: str) -> Optional[dict]:
        return {
            "sim_card_id": sim_card_id,
            "network_name": "unknown",
            "queue_length": 0,
            "is_processing": False,
            "current_task": None,
        }

    def get_transaction_position(self, sim_card_id: str, transaction_id: str) -> Optional[int]:
        return 1

    async def process_next(self, sim_card_id: str):
        return None

    def mark_complete(self, sim_card_id: str):
        pass

    def mark_failed(self, sim_card_id: str):
        pass

queue_engine = QueueEngine()

@celery_app.task(bind=True, max_retries=3, name="mobile_money_gateway.services.queue_engine.process_ussd_transaction")
def process_ussd_transaction(self, sim_card_id: str, transaction_id: str, network_name: str):
    import httpx
    try:
        # In a real scenario, this would send an HTTP POST to FastAPI to broadcast to the gateway WS.
        # Here we use the simulate endpoint to fulfill the process.
        response = httpx.post(f"http://127.0.0.1:8000/gateway/simulate/transaction/{transaction_id}", timeout=10.0)
        response.raise_for_status()
    except Exception as e:
        raise self.retry(exc=e, countdown=5)
