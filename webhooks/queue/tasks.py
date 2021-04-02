import os
import datetime
import pynetbox
from celery import Celery


CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL'),
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')

celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

nb_url = os.getenv("NETBOX_URL")
nb_token = os.getenv("NETBOX_TOKEN")

nb = pynetbox.api(nb_url, nb_token)
now = datetime.datetime.now()

current_date = now.strftime('%Y%m%d')


@celery.task(name='tasks.device_update')
def device_update(request_id: str, data: dict) -> str:
    print(data)
    # device = nb.dcim.devices.get(name=data['name'])
    # print(device)
    return 'ok'
