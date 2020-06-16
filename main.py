from flask import Flask, render_template, url_for, request
import pynetbox
from flask_wtf import FlaskForm
from wtforms import TextField, StringField, validators, SelectField, TextAreaField, SubmitField, HiddenField


app = Flask(__name__)
app.conﬁg['SECRET_KEY'] = 'hard to guess string'

nb_url = 'http://10.100.3.128:33080/'
token = '03319cd840dcea602826b4c1ba3012761ee49466'
nb = pynetbox.api(nb_url, token)


class SelectForm(FlaskForm):
    button = SubmitField('Next step')


class RegionForm(SelectForm):
    regions = SelectField('Список', choices=[])


class SiteForm(SelectForm):
    sites = SelectField('Список', choices=[])


class DeviceTypeForm(SelectForm):
    types = SelectField('Список', choices=[])
    site = HiddenField()


class VlanForm(SelectForm):
    device_type = StringField()
    site = StringField()
    region = StringField()
    vlan = SelectField('Список', choices=[])


class IpForm(SelectForm):
    region = StringField()
    site = StringField()
    device_type = StringField()
    mngmt_interface = SelectField('Список', choices=[])
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
        form.mngmt_interface.choices = [_int for _int in interface]
        form.vlan.data = vlan
        form.ip.choices = [ ip['address'].split('/')[0]  for ip in _list_ip if int(ip['address'].split('/')[0].split('.')[-1]) > 25 ]
        form.name_device.data = name_device

    return render_template('step5.html', form=form)


if __name__ == '__main__':
    app.run()
