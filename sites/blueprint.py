from flask import Blueprint
from flask import Flask, flash, get_flashed_messages, render_template, url_for, request
import pynetbox, os
from flask_wtf import FlaskForm
from wtforms import TextField, StringField, validators, SelectField, TextAreaField, SubmitField, HiddenField

nb_url = os.getenv('NETBOX_URL')
token = os.getenv('NETBOX_TOKEN')

nb = pynetbox.api(nb_url, token)

add_site = Blueprint('add_site', __name__, template_folder='templates')


class RegionForm(FlaskForm):
    regions = SelectField('Регион', choices=[])
    submit = SubmitField('Next step')


class SiteForm(FlaskForm):
    sites = SelectField('Сайт', choices=[])
    search = StringField('Поиск', validators=[validators.DataRequired()])
    submit = SubmitField('Next step')


@add_site.route('/step1')
def count_regions():
    form = RegionForm()
    form.regions.choices = [(region.slug, ': '.join([str(region.parent), str(region.name)]))  for region in nb.dcim.regions.all() if region.parent]
    return render_template('sites/step1.html', form=form)


@add_site.route('step2', methods=['POST'])
def count_sites():
    form = SiteForm()
    regions = request.form.get('regions')
    sites = nb.dcim.sites.filter(region=regions)
    form.sites.choices = [(site.slug, site.name)  for site in sites ]
    return render_template('sites/step2.html', form=form)


@add_site.route('step3', methods=['POST'])
def search():
    data = request.form.get('search')
    return render_template('sites/step3.html', data=data)