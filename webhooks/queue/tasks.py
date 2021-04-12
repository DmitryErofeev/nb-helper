import os
import time
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
date_remove = now.strftime('%Y-%m-%d')

@celery.task(name='tasks.device_update')
def device_update(request_id: str, data: dict) -> str:

    device_status = data['data']['status']['value']

    if device_status == 'offline':
        device = nb.dcim.devices.get(data['data']['id'])

        new_device_name = device['name'] + '-' + current_date
        print(f'Имя коммутатора: {new_device_name}')

        new_status = 'offline'
        print(f'Новый статус: {new_status}')

        print(f'Дата удаления: {current_date}')

        interfaces = nb.dcim.interfaces.filter(device_id=device.id, cabled=True)
        print(interfaces)

        ids_cable_links = [id.cable_peer.cable for id in interfaces]
        print(ids_cable_links)

        try:
            for cable_link in ids_cable_links:
                link = nb.dcim.cables.get(cable_link)
                link.delete()
            print('Линки коммутатора удалены')

        except Exception:
            print('Линки коммутатора не удалены')

        try:
            device = nb.dcim.devices.get(device.id)

            device.name = new_device_name
            device.status = new_status
            device.custom_fields['dateRemove'] = date_remove
            device.save()
            print('Коммутатор переименован')

        except Exception:
            print('Коммутатор не переименован')

            return 'failure'


        return 'ok'

    return 'ignore'