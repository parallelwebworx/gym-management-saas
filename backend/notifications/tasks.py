from celery import shared_task
from django.conf import settings

from notifications.models import Notification
from notifications.providers import ProviderError
from notifications.service import attempt_send


@shared_task(
    bind=True,
    autoretry_for=(ProviderError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": settings.NOTIFICATION_MAX_ATTEMPTS - 1},
)
def send_notification_task(self, notification_id):
    note = Notification.objects.filter(id=notification_id).first()
    if not note:
        return
    attempt_send(note)  # raises ProviderError -> Celery retries with backoff
