import requests, functools
from flask import Blueprint, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from .transliteration import transliterate
from .slugify import slugify

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

        _trans = transliterate(request.form.get('input_for_transliterate'))
        trans = _trans.replace('.', "")  # TODO: сделать функцией подготовки

        form.output_transliterated.data = trans

        slug = slugify(trans.replace('/', "-"))
        form.output_slugifyed.data = slug

    return render_template('utils/utils_slug.html', form=form)


@functools.lru_cache
@add_utils.route('/utils-mac', methods=['POST', 'GET'])
def utils_mac():
    form = MacVendor()

    if request.method == 'POST':

        mac = request.form.get ('input_mac')
        url = f"https://api.macvendors.com/{mac}"

        response = requests.get(url)
        form.output_mac.data = response.text


    return render_template('utils/utils_mac.html', form=form)