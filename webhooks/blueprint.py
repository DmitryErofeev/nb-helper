from flask import Blueprint, render_template, abort, request
from manuf import manuf
# from requests.api import request
from cache import cache
import requests
api_webhooks = Blueprint('api_webhooks', __name__, template_folder='templates')


@api_webhooks.route('/api/', methods=['POST'])
@cache.memoize()
def get_webhooks():
    if request.method == 'POST':

        print(request.json)


    return render_template('data.html', data=request.json)

