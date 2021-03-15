from flask.globals import session
import requests
from flask import Blueprint, flash, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.fields.core import SelectField
import utils
import pynetbox
import os
from cache import cache
from config import MAC_API_URL


nb_url = os.getenv('NETBOX_URL')
nb_token = os.getenv('NETBOX_TOKEN')

nb = pynetbox.api(nb_url, nb_token)

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


class GetREgion(FlaskForm):
    get_region = SelectField('Выберите регион:')
    submit = SubmitField('Дальше:')


class GetSite(FlaskForm):
    get_site = SelectField('Выберите сайт:')
    submit = SubmitField('Дальше:')


class GetDevice(FlaskForm):
    get_device = SelectField('Выберите коммутатор:')
    submit = SubmitField('Дальше:')


class GetLink(FlaskForm):
    get_cable_link = SelectField('Выберите линк для удаления:')
    submit = SubmitField('Удалить линк:')


@add_utils.route('/del_cable_step1', methods=['GET'])
def get_region():
    form = GetREgion()

    form.get_region.choices = [(region.slug, ':'.join([str(region.parent), str(region.name)]))
                                for region in nb.dcim.regions.all()
                                if region.parent
                                ]

    return render_template('utils/step1.html', form=form)


@add_utils.route('del_cable_step2', methods=['POST'])
def get_site():
    form = GetSite()

    session['region'] = request.form.get('get_region')
    sites = nb.dcim.sites.filter(region=session['region'])
    form.get_site.choices = [site.slug for site in sites]

    return render_template('utils/step2.html', form=form)


@add_utils.route('del_cable_step3', methods=['POST'])
def get_device():
    form = GetDevice()

    session['site'] = request.form.get('get_site')
    devices = nb.dcim.devices.filter(site=session['site'])
    form.get_device.choices = [device for device in devices]

    return render_template('utils/step3.html', form=form)


@add_utils.route('del_cable_step4', methods=['POST'])
def get_cable():
    form = GetLink()

    session['device'] = request.form.get('get_device')
    _device = nb.dcim.devices.get(name=session['device'])
    _interfaces = nb.dcim.interfaces.filter(device_id=_device.id, cabled=True)

    form.get_cable_link.choices = [link_id.cable_peer.cable for link_id in _interfaces]

    return render_template('utils/step4.html', form=form)


@add_utils.route('del_cable_step5', methods=['POST'])
def del_cable():
    session['cable'] = request.form.get('get_cable_link')
    # _device = nb.dcim.devices.get(name=session['device'])
    _cable = nb.dcim.cables.get(session['cable'])
    try:
        _cable.delete()
        flash('Линк удален', category='success')
    except:
        flash('Ошибка', category='danger')

    return render_template('utils/step5.html',nb_url=nb_url, device=_device)


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
        url = f"{MAC_API_URL}{mac}"

        response = requests.get(url)
        print("get_mac_request()", mac, response.status_code)

        if response.ok:
            return response.text
        else:
            return response.reason
