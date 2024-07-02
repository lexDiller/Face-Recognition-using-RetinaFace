from celery import shared_task
from .scripts import face_lets_go
@shared_task()
def task_1():
    face_lets_go()
