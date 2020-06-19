from flask import Flask, flash, get_flashed_messages, render_template, url_for, request
from flask_bootstrap import Bootstrap
import pynetbox, os
from flask_wtf import FlaskForm
from wtforms import TextField, StringField, validators, SelectField, TextAreaField, SubmitField, HiddenField


app = Flask(__name__)
Bootstrap(app)
app.conﬁg['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'hard to guess string'

nb_url = 'http://10.100.3.128:33080/'
token = os.getenv('NETBOX_TOKEN')

nb = pynetbox.api(nb_url, token)


# class SelectForm(FlaskForm):
#     button = SubmitField('Next step')


class RegionForm(FlaskForm):
    regions = SelectField('Регион', choices=[])
    button = SubmitField('Next step')


class SiteForm(FlaskForm):
    sites = SelectField('Сайт', choices=[])
    button = SubmitField('Next step')


class DeviceTypeForm(FlaskForm):
    types = SelectField('Список', choices=[])
    site = HiddenField()
    button = SubmitField('Next step')


class VlanForm(FlaskForm):
    device_type = StringField()
    site = StringField()
    region = StringField()
    vlan = SelectField('Список', choices=[])
    button = SubmitField('Next step')


class IpForm(FlaskForm):
    region = StringField()
    site = StringField()
    device_type = StringField()
    mgmt_interface = SelectField('Список', choices=[])
    vlan = StringField()
    ip = SelectField('Список', choices=[])
    name_device = StringField()
    button = SubmitField('Add device')


@app.route('/step1', methods=['GET'])
def count_regions():
    form = RegionForm()
    form.regions.choices = [(region.slug, ': '.join([str(region.parent), str(region.name)]))  for region in nb.dcim.regions.all() if region.parent]

    return render_template('step1.html', form=form)


@app.route('/step2', methods=['POST'])
def count_sites():
    """
    pynetbox.core.query.RequestError:
    The request failed with code 403 Forbidden:
    {'detail': 'You do not have permission to perform this action.'}
    """
    if request.method == 'POST':
        region = request.form.get('regions')
        sites = nb.dcim.sites.filter(region=region)
        form = SiteForm()
        form.sites.choices = [(site.slug, ': '.join([str(site.name)]))  for site in sites ]

    return render_template('step2.html', form=form, data={'region': region, 'title': "Выбор сайта"})


@app.route('/step3', methods=['POST'])
def count_device_types():
    if request.method == 'POST':
        site = request.form.get('sites')
        form = DeviceTypeForm()
        form.site.data = site
        device_types = nb.dcim.device_types.all()
        form.types.choices = [(device_type.slug, ': '.join([str(device_type.manufacturer), str(device_type.model)]))  for device_type in device_types]

    return render_template('step3.html', form=form)


@app.route('/step4', methods=['POST'])
def count_vlan():
    if request.method == 'POST':
        form = VlanForm()

        device_type = request.form.get('types')
        site = request.form.get('site')
        _site = nb.dcim.sites.get(slug=site)
        region = nb.dcim.regions.get(_site.region.id)
        vlan_group = nb.ipam.vlan_groups.get(slug=region.slug)
        vlans = nb.ipam.vlans.filter(group_id=vlan_group.id)

        form.device_type.data = device_type
        form.site.data = site
        form.region.data = region
        form.vlan.choices = [(vlan.vid, ': '.join( [str(vlan.role), str(vlan)] ))  for vlan in vlans]

    return render_template('step4.html',form=form)


@app.route('/step5', methods=['POST'])
def count_ip():
    if request.method == 'POST':
        form = IpForm()

        region = request.form.get('region')
        _region = nb.dcim.regions.get(name=region)

        site = request.form.get('site')
        _site = nb.dcim.sites.get(slug=site)

        device_type = request.form.get('device_type')
        _device_type = nb.dcim.device_types.get(slug=device_type)

        vlan = request.form.get('vlan')
        _list_ip = nb.ipam.prefixes.get(vlan_vid=vlan).available_ips.list()
        interface = nb.dcim.interface_templates.filter(devicetype_id=_device_type.id, mgmt_only=True)
        name_device = '-'.join([_region.parent.slug, _site.slug])

        form.region.data = region
        form.site.data = site
        form.device_type.data = device_type
        form.mgmt_interface.choices = [_int for _int in interface]
        form.vlan.data = vlan
        form.ip.choices = [ ip['address']  for ip in _list_ip if int(ip['address'].split('/')[0].split('.')[-1]) > 25 ]
        form.name_device.data = name_device

    return render_template('step5.html', form=form)


@app.route('/step6', methods=['POST'])
def create_device():
    DEVICE_ROLE = 'access-switch'

    region = request.form.get('region')

    site = request.form.get('site')
    _site = nb.dcim.sites.get(slug=site)

    device_type = request.form.get('device_type')
    _device_type = nb.dcim.device_types.get(slug=device_type)

    interface = request.form.get('mgmt_interface')
    vlan = request.form.get('vlan')
    ip = request.form.get('ip')
    name_device = request.form.get('name_device')
    device_role = nb.dcim.device_roles.get(slug=DEVICE_ROLE)

    device_params = \
    {
        'site': _site.id,
        'device_type': _device_type.id,
        'name': name_device,
        'device_role': device_role.id
    }

    # errors = []
    _device = None
    _interface = None
    # pynetbox.core.query.RequestError: The request failed with code 400 Bad Request: {'name': ['A device with this name already exists.']}
    try:
        _device = nb.dcim.devices.create(**device_params)
        flash('Устройство создано!', category='success')
    except pynetbox.core.query.RequestError as ex:
        # errors.append(ex.error)
        flash('Устройство уже существует', category='danger')

    if _device:
        _interface = nb.dcim.interfaces.get(device_id=_device.id, name=interface)

        _ip_on_interface = None
        try:
            _ip_on_interface = nb.ipam.ip_addresses.create(interface=_interface.id, address=ip)
            flash('IP адрес создан!', category='success')
        except pynetbox.core.query.RequestError as ex:
            # errors.append(ex.error)
            flash('IP адрес не создан!', category='danger')

        if _ip_on_interface:
            _device.update({'primary_ip4': _ip_on_interface.id})
            flash('Primary IP адрес установлен!', category='success')

    return render_template('step6.html', nb_url=nb_url, device=_device)


if __name__ == '__main__':
    app.run()
