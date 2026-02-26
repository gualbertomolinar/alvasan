import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytics.settings')

app = Celery('tu_proyecto')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Programación de tareas (Beat)
app.conf.beat_schedule = {
    'sincronizar-todo-al-final-del-dia': {
        'task': 'apps.core.tasks.sincronizacion_total_automatica',
        'schedule': crontab(hour=22, minute=30), # Todos los días a las 22:30
    },
}