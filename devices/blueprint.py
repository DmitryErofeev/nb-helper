from flask import Blueprint, session
from flask import flash, render_template, request
import pynetbox
import os
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, HiddenField

nb_url = os.getenv("NETBOX_URL")
token = os.getenv("NETBOX_TOKEN")

nb = pynetbox.api(nb_url, token)

add_device = Blueprint("add_device", __name__, template_folder="templates")


class RegionForm(FlaskForm):
    regions = SelectField("Регион", choices=[])
    button = SubmitField("Следующий шаг")


class SiteForm(FlaskForm):
    sites = SelectField("Сайт", choices=[])
    button = SubmitField("Следующий шаг")


class DeviceTypeForm(FlaskForm):
    types = SelectField("Выберите модель:", choices=[])
    roles = SelectField("Выберите роль:")
    site = HiddenField()

    button = SubmitField("Следующий шаг")


class VlanForm(FlaskForm):
    vlan = SelectField("Список Vlan-ов", choices=[])
    button = SubmitField("Следующий шаг")


class IpForm(FlaskForm):
    region = StringField("Регион(Region)")
    site = StringField("Сайт(site)")
    device_type = StringField("Модель(DeviceType)")
    role = StringField("Роль устройства:")
    mgmt_interface = SelectField("Интерфейс управления", choices=[])
    vlan = StringField("Номер Vlan-а")
    ip = SelectField("Список свободных адресов", choices=[])
    name_device = StringField("Имя добавляемого устройства")
    status_device = StringField('Статус добавляемого устройства')
    button = SubmitField("Отправить в NetBox")


@add_device.route("/step1", methods=["GET"])
def count_regions():
    form = RegionForm()
    form.regions.choices = [
        (region.slug, ": ".join([str(region.parent), str(region.name)]))
        for region in nb.dcim.regions.all()
        if region.parent
    ]
    return render_template("devices/step1.html", form=form)


@add_device.route("/step2", methods=["POST"])
def count_sites():
    if request.method == "POST":
        form = SiteForm()

        session["region"] = request.form.get("regions")
        sites = nb.dcim.sites.filter(region=session["region"])
        form.sites.choices = [
            (site.slug, ": ".join([str(site.name)])) for site in sites
        ]

    return render_template("devices/step2.html", form=form)


@add_device.route("/step3", methods=["POST"])
def count_device_types():
    if request.method == "POST":
        form = DeviceTypeForm()

        session["site"] = request.form.get("sites")
        device_roles = nb.dcim.device_roles.all()
        device_types = nb.dcim.device_types.all()

        form.types.choices = [
            (
                device_type.slug,
                ": ".join([str(device_type.manufacturer), str(device_type.model)]),
            )
            for device_type in device_types
        ]
        form.roles.choices = [role for role in device_roles]

    return render_template("devices/step3.html", form=form)


@add_device.route("/step4", methods=["POST"])
def count_vlan():
    if request.method == "POST":
        form = VlanForm()
        session["device_type"] = request.form.get("types")
        session["device_role"] = request.form.get("roles")

        _site = nb.dcim.sites.get(slug=session["site"])
        _region = nb.dcim.regions.get(_site.region.id)

        vlan_group = nb.ipam.vlan_groups.get(slug=_region.slug)
        vlans = nb.ipam.vlans.filter(group_id=vlan_group.id)

        form.vlan.choices = [
            (vlan.vid, ": ".join([str(vlan.role), str(vlan)])) for vlan in vlans
        ]

    return render_template("devices/step4.html", form=form)


@add_device.route("/step5", methods=["POST"])
def count_ip():
    if request.method == "POST":
        form = IpForm()

        session["vlan"] = request.form.get("vlan")
        _region = nb.dcim.regions.get(slug=session["region"])
        _site = nb.dcim.sites.get(slug=session["site"])
        _device_type = nb.dcim.device_types.get(slug=session["device_type"])
        _list_ip = nb.ipam.prefixes.get(vlan_vid=session["vlan"]).available_ips.list()
        interface = nb.dcim.interface_templates.filter(
            devicetype_id=_device_type.id, mgmt_only=True
        )

        name_device = "-".join([_region.parent.slug, _site.slug])

        form.region.data = session["region"]
        form.site.data = session["site"]
        form.device_type.data = session["device_type"]
        form.role.data = session["device_role"]
        form.mgmt_interface.choices = [_int for _int in interface]
        form.vlan.data = session["vlan"]
        form.name_device.data = name_device
        form.status_device.data = 'staged'

        form.ip.choices = [
            ip.address
            for ip in _list_ip
            if int(ip.address.split("/")[0].split(".")[-1]) > 25
        ]

    return render_template("devices/step5.html", form=form)


@add_device.route("/step6", methods=["POST"])
def create_device():
    session["interface"] = request.form.get("mgmt_interface")
    session["ip"] = request.form.get("ip")
    session["name_device"] = request.form.get("name_device")
    session["status_device"] = request.form.get("status_device")

    _site = nb.dcim.sites.get(slug=session["site"])
    _device_type = nb.dcim.device_types.get(slug=session["device_type"])
    device_role = nb.dcim.device_roles.get(name=session["device_role"])

    device_params = {
        "site": _site.id,
        "device_type": _device_type.id,
        "name": session["name_device"],
        "device_role": device_role.id,
        "status": session["status_device"]
        }

    _device = None
    _interface = None

    try:
        _device = nb.dcim.devices.create(**device_params)
        flash("Устройство создано!", category="success")
    except pynetbox.core.query.RequestError as ex:
        flash("Устройство уже существует", category="danger")

    if _device:
        _interface = nb.dcim.interfaces.get(
            device_id=_device.id, name=session["interface"]
        )

        _ip_on_interface = None
        try:
            _ip_on_interface = nb.ipam.ip_addresses.create(
                assigned_object_type="dcim.interface",
                assigned_object_id=_interface.id, address=session["ip"]
            )
            flash("IP адрес создан!", category="success")
        except pynetbox.core.query.RequestError as ex:
            flash("IP адрес не создан!", category="danger")

        if _ip_on_interface:
            _device.update({"primary_ip4": _ip_on_interface.id})
            flash("Primary IP адрес установлен!", category="success")

    return render_template("devices/step6.html", nb_url=nb_url, device=_device)
