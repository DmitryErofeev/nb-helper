from flask import Blueprint, render_template, abort
from manuf import manuf
from cache import cache

api_bp = Blueprint('api_bp', __name__, template_folder='templates')


@api_bp.route('/mac/<mac>', methods=['GET'])
@cache.memoize()
def get_mac_info(mac):
    data = None
    try:
        query = manuf.MacParser(update=True)
        data = query.get_manuf_long(mac)

    except:
        abort(400, 'Record not found')

    if not data:
        abort(404, "Not found")

    return render_template('api/mac.html', data=data)
