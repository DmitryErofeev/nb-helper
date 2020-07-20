import requests
from flask import Blueprint, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
import utils
from cache import cache

add_utils = Blueprint('add_utils', __name__, template_folder='templates')


class UtilsForm(FlaskForm):
    input_for_transliterate = StringField('Введите адрес:')
    output_transliterated = StringField('Вывод транслита')

    output_slugifyed = StringField('Вывод слага')
    submit_slug = SubmitField('Сделать слаг')


class MacVendor(FlaskForm):
    input_mac = StringField('Введите МАК:')
    output_mac = TextAreaField('Вендор МАКа:')
    submit = SubmitField('Узнать Вендора')


@add_utils.route('/utils-slug', methods=['POST', 'GET'])
def utils_slug():
    form = UtilsForm()

    if request.method == 'POST':

        _data = request.form.get('input_for_transliterate')
        form.output_transliterated.data = utils.transliterate_name(_data)

        _data2 = form.output_transliterated.data
        form.output_slugifyed.data = utils.slugify_name(_data2)

    return render_template('utils/utils_slug.html', form=form)


@add_utils.route('/utils-mac', methods=['POST', 'GET'])
def utils_mac():
    form = MacVendor()

    if request.method == 'POST':

        res = get_mac_request(request.form.get ('input_mac'))
        form.output_mac.data = res

    return render_template('utils/utils_mac.html', form=form)

@cache.memoize()
def get_mac_request(mac: str) -> str:
        url = f"https://api.macvendors.com/{mac}"

        response = requests.get(url)
        print("get_mac_request()", mac, response.status_code)

        if response.ok:
            return response.text
        else:
            return response.reason
