from flask import Blueprint, request
# from cache import cache
# import requests
# import redis
import os
# import time

from celery import Celery


api_webhooks = Blueprint('api_webhooks', __name__, template_folder='templates')

# nb_url = os.getenv("NETBOX_URL")
# token = os.getenv("NETBOX_TOKEN")

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL'),
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


@api_webhooks.route('/device_update', methods=['POST'])
# @cache.memoize()
def device_update():
    response_code = '500'
    if request.method == 'POST':
        data = request.json
        tags = data['data']['tags']
        if any(['webhook' == tag['name'] for tag in tags]):  # ищем тэг во всех тэгах

            task = celery.send_task('tasks.device_update', args=[data['request_id'], data], kwargs={})

            response_code = task.id
        else:
            response_code = '404'

    return response_code
