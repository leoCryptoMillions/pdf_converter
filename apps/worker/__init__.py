"""
PDF Converter Worker - Celery Background Tasks

Processes long-running PDF conversion tasks asynchronously.
"""

from celery import Celery
from apps.worker.config import celery_config

# Create Celery app instance
celery_app = Celery("pdf_converter")
celery_app.config_from_object(celery_config)

# Import tasks to register them
# from apps.worker.tasks import *  # TODO: Implement in F1
