from flask import Blueprint, session
from flask import flash, render_template, request
import pynetbox
import os
import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, HiddenField

nb_url = os.getenv("NETBOX_URL")
token = os.getenv("NETBOX_TOKEN")

nb = pynetbox.api(nb_url, token)

now = datetime.datetime.now()

del_device = Blueprint("del_device", __name__, template_folder="templates")


class SelectRegion(FlaskForm):
    regions = SelectField("Выберите регион:", choices=[])
    button = SubmitField("Следующий шаг")


class SelectSite(FlaskForm):
    sites = SelectField("Выберите сайт:", choices=[])
    button = SubmitField("Следующий шаг")


class SelectDevice(FlaskForm):
    devices = SelectField("Выберите коммутатор:", choices=[])
    button = SubmitField("Следующий шаг")


class VerifyForm(FlaskForm):
    region = StringField("Регион:")
    site = StringField("Сайт:")
    name_device = StringField("Новое имя удаляемого коммутатора:")
    status_device = StringField('Новый статус удаляемого коммутатора:')
    cable_link = StringField("Линки от этого коммутатора:")
    device = HiddenField()
    button = SubmitField("Отправить в NetBox")


@del_device.route("/step1", methods=["GET"])
def get_region():
    form = SelectRegion()
    form.regions.choices = [
        (region.slug, ": ".join([str(region.parent), str(region.name)]))
        for region in nb.dcim.regions.all()
        if region.parent
    ]

    return render_template("del_device/step1.html", form=form)


@del_device.route("/step2", methods=["POST"])
def get_site():
    if request.method == 'POST':
        form = SelectSite()
        session['region'] = request.form.get('regions')
        sites = nb.dcim.sites.filter(region=session['region'])

        form.sites.choices = [
            (site.slug, ':'.join([site.name])) for site in sites
            ]
    return render_template("del_device/step2.html", form=form)


@del_device.route("/step3", methods=["POST"])
def get_device():
    if request.method == 'POST':
        form = SelectDevice()
        session['site'] = request.form.get('sites')

        devices = nb.dcim.devices.filter(site=session['site'])

        form.devices.choices = [
            (device, ':'.join([device.name])) for device in devices
            ]
    return render_template("del_device/step3.html", form=form)


@del_device.route("/step4", methods=["POST"])
def check_device():
    if request.method == "POST":
        form = VerifyForm()
        session['device'] = request.form.get('devices')
        device = nb.dcim.devices.get(name=session['device'])

        interfaces = nb.dcim.interfaces.filter(
            device_id=device.id, cabled=True)
        session['device'] = request.form.get('devices')

        session['cable_link_ids'] = [id.cable_peer.cable for id in interfaces]

        form.region.data = session["region"]
        form.site.data = session["site"]

        current_date = now.strftime('%Y%m%d')
        session['date_remove'] = now.strftime('%Y-%m-%d')

        form.name_device.data = request.form.get('devices') + '-' + current_date
        session['new_device_name'] = form.name_device.data

        form.status_device.data = 'offline'
        session['device_status'] = form.status_device.data

        form.cable_link.data = [link for link in interfaces]

    return render_template("del_device/step4.html", form=form)


@del_device.route("/step5", methods=["POST"])
def rename_device():

    _new_device_name = session['new_device_name']
    _cable_links = session['cable_link_ids']
    _date_remove = session['date_remove']
    _device_status = session['device_status']

    try:
        for cable_link in _cable_links:
            link = nb.dcim.cables.get(cable_link)
            link.delete()
        flash('Линки коммутатора удалены', category='success')
    except:
        flash('Линки коммутатора не удалены', category='danger')


    try:
        device = nb.dcim.devices.get(name=session['device'])

        device.name = _new_device_name
        device.status = _device_status
        device.custom_fields['dateRemove'] = _date_remove
        device.save()
        flash('Коммутатор переименован', category='success')
    except:
        flash('Коммутатор не переименован', category='danger')

    return render_template("del_device/step5.html", nb_url=nb_url, device=device)
