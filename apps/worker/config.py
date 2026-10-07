"""
Celery Configuration

Configure Celery tasks, brokers, and worker behavior.
"""

import os
from kombu import Queue, Exchange

# Load from environment or use defaults
CELERY_BROKER_URL = os.environ.get(
    "CELERY_BROKER_URL",
    "amqp://guest:guest@localhost:5672//",
)
CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND",
    "redis://localhost:6379/1",
)


class CeleryConfig:
    """Celery Configuration Object"""

    # Broker Settings
    broker_url = CELERY_BROKER_URL
    result_backend = CELERY_RESULT_BACKEND

    # Task Settings
    task_serializer = "json"
    result_serializer = "json"
    accept_content = ["json"]
    timezone = "UTC"
    enable_utc = True

    # Task Execution Settings
    task_track_started = True
    task_time_limit = 600  # Hard time limit (10 minutes)
    task_soft_time_limit = 540  # Soft time limit (9 minutes)
    task_acks_late = True  # Acknowledge after task completion
    worker_prefetch_multiplier = 1  # Process one task at a time
    worker_max_tasks_per_child = 1000  # Restart worker periodically

    # Retry Settings
    task_autoretry_for = ()
    task_max_retries = 2
    task_default_retry_delay = 60  # Retry after 1 minute

    # Queue Configuration
    task_default_queue = "default"
    task_default_exchange = "tasks"
    task_default_routing_key = "task.default"

    # Define task routes and priorities
    task_routes = {
        "apps.worker.tasks.validate_pdf": {
            "queue": "default",
            "routing_key": "task.validate",
            "priority": 10,
        },
        "apps.worker.tasks.convert_to_xlsx": {
            "queue": "processing",
            "routing_key": "task.xlsx",
            "priority": 5,
        },
        "apps.worker.tasks.convert_to_docx": {
            "queue": "processing",
            "routing_key": "task.docx",
            "priority": 5,
        },
        "apps.worker.tasks.perform_ocr": {
            "queue": "ocr",
            "routing_key": "task.ocr",
            "priority": 1,
        },
        "apps.worker.tasks.cleanup_expired_files": {
            "queue": "maintenance",
            "routing_key": "task.cleanup",
            "priority": 0,
        },
    }

    # Define queues
    task_queues = (
        Queue(
            "default",
            Exchange("tasks", type="direct"),
            routing_key="task.default",
            queue_arguments={"x-max-priority": 10},
        ),
        Queue(
            "processing",
            Exchange("tasks", type="direct"),
            routing_key="task.processing",
            queue_arguments={"x-max-priority": 10},
        ),
        Queue(
            "ocr",
            Exchange("tasks", type="direct"),
            routing_key="task.ocr",
            queue_arguments={"x-max-priority": 10},
        ),
        Queue(
            "maintenance",
            Exchange("tasks", type="direct"),
            routing_key="task.maintenance",
            queue_arguments={"x-max-priority": 10},
        ),
    )

    # Periodic Tasks (Celery Beat)
    beat_schedule = {
        "cleanup-expired-files": {
            "task": "apps.worker.tasks.cleanup_expired_files",
            "schedule": 3600.0,  # Every hour
            "options": {"queue": "maintenance", "priority": 0},
        },
        "publish-pending-events": {
            "task": "apps.worker.tasks.publish_pending_events",
            "schedule": 60.0,  # Every minute
            "options": {"queue": "maintenance", "priority": 0},
        },
    }

    # Worker Settings
    worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
    worker_task_log_format = (
        "[%(asctime)s: %(levelname)s/%(processName)s] "
        "[%(task_name)s(%(task_id)s)] %(message)s"
    )


# Export configuration object
celery_config = CeleryConfig
