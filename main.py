from flask import Flask, render_template, url_for, request
import pynetbox
from flask_wtf import FlaskForm
from wtforms import TextField, StringField, validators, SelectField, TextAreaField, SubmitField, HiddenField


app = Flask(__name__)
app.conﬁg['SECRET_KEY'] = 'hard to guess string'

nb_url = 'http://10.100.3.128:33080/'
token = '03319cd840dcea602826b4c1ba3012761ee49466'
nb = pynetbox.api(nb_url, token)

_list =  nb.dcim.regions.all()


class RegionForm(FlaskForm):
    regions = SelectField('Список', choices=[])
    button = SubmitField('Next step')


class SiteForm(FlaskForm):
    sites = SelectField('Список', choices=[])
    button = SubmitField('Next step')


class DeviceTypeForm(FlaskForm):
    types = SelectField('Список', choices=[])
    site = HiddenField()
    button = SubmitField('Next step')


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
        form.types.choices = [(device_type.manufacturer.slug, ': '.join([str(device_type.model)]))  for device_type in device_types]

    return render_template('step3.html', form=form)


if __name__ == '__main__':
    app.run()
