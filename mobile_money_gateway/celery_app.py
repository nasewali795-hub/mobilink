import os
from celery import Celery

# Use Redis as both the broker and the backend for Celery
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "mobilink_queue",
    broker=redis_url,
    backend=redis_url,
    include=["mobile_money_gateway.services.queue_engine"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True, # Ensure tasks are acknowledged only after processing
)
