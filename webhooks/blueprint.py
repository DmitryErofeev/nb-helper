from flask import Blueprint, request
from cache import cache
# import requests
import redis


r = redis.StrictRedis(
host='192.168.81.130',
port=36379,)
# password='password')

api_webhooks = Blueprint('api_webhooks', __name__, template_folder='templates')


@api_webhooks.route('/api/', methods=['POST'])
@cache.memoize()
def get_webhooks():
    if request.method == 'POST':
        response_code = ''
        data = request.json
        try:
            r.set(data['request_id'], request.data)
            response_code = '200'
        except:
            response_code = '500'

    return response_code

