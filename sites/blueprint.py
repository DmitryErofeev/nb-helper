from os import abort
from flask import Blueprint, flash, render_template, request, session, abort
import pynetbox, os, requests, functools, re
from flask_wtf import FlaskForm
from wtforms import StringField, validators, SelectField, SubmitField
from utils.transliteration import transliterate
from utils.slugify import slugify

nb_url = os.getenv('NETBOX_URL')
token = os.getenv('NETBOX_TOKEN')

nb = pynetbox.api(nb_url, token)

add_site = Blueprint('add_site', __name__, template_folder='templates')


class RegionForm(FlaskForm):
    regions = SelectField('Регион', choices=[])
    submit = SubmitField('Следующий шаг')


class SiteForm(FlaskForm):
    search = StringField('Поиск', validators=[validators.DataRequired()])
    submit = SubmitField('Следующий шаг')


class FiasForm(FlaskForm):
    search = StringField('Поиск')
    houses = SelectField('Выберите номер дома, если он есть в КЛАДРе:', choices=[])
    submit = SubmitField('Отправить в NetBox')


FIAS_CODE = {
"dm": "5000002600400",
"kb": "5000002615000",
"ku": "5002400300000",
"oz": "5000002600000",
"ld": "5000005800000",
}

@functools.lru_cache
def fias(query: str, cityid: str) -> requests.Response:
    url = 'https://kladr-api.ru/api.php'
    params = {
        'query': query.replace('/', '\/'),
        'cityId': cityid,
        'contentType': 'building',
        'withParent': 1,
        'limit': 30,
        'oneString': 1,
        'regionId': 5000000000000
            }
    response = requests.get(url, params=params)
    return response


@add_site.route('/step1')
def count_regions():
    form = RegionForm()
    form.regions.choices = [(region.slug, ': '.join([str(region.parent), str(region.name)]))  for region in nb.dcim.regions.all() if region.parent]
    return render_template('sites/step1.html', form=form)


@add_site.route('step2', methods=['POST'])
def count_sites():
    form = SiteForm()

    region = request.form.get('regions')
    _region = nb.dcim.regions.get(slug=region)

    session['region_slug'] = _region.slug
    session['region_parent_slug'] = _region.parent.slug

    return render_template('sites/step2.html', form=form)


@add_site.route('step3', methods=['POST'])
def search():
    form = FiasForm()

    search = request.form.get('search')
    region = session['region_parent_slug']

    _fias = fias(search, FIAS_CODE[region]).json()

    session['result'] = _fias['result']

    if _fias['result'] is None:

        flash('Нет такого адреса, повторите ввод!', category='danger')
        form.houses.choices = []

    else:
        form.houses.choices = [(item['guid'], '. '.join([ item['typeShort'], item['name'] ])) for item in _fias['result']]

    return render_template('sites/step3.html', form=form)


def result_search(fiasId, elements):
    return [element for element in elements if element['guid'] == fiasId]


@add_site.route('step4', methods=['POST'])
def final_step():

    search = request.form.get('search')
    fiasId = request.form.get('houses')
    if not (fiasId or session['result']):
        abort(400)
    _resu = result_search(fiasId, session['result'])[0]
    site_params = {
    "name": '',
    "slug": '',
    "region": '',
    "description": '',
    }

    if _resu['contentType'] == 'building':
        print(_resu['fullName'])
        _street = result_search(_resu['parentGuid'], _resu["parents"])[0]

        site_name1 = ' '.join([_street['typeShort'], _street['name'], _resu['name']])
        site_name2 = transliterate(site_name1)

        site_name3 = ' '.join([session['region_parent_slug'], site_name2.replace('/', '-')])
        site_name4 = slugify(site_name3)

        site_desc1 = '. '.join([_street['typeShort'], _street['name']])
        site_desc2 = ' '.join([site_desc1, _resu['name']])

        region = nb.dcim.regions.filter(slug=session['region_slug'])[0]

        site_params = {
            "name": site_name2,
            "slug": site_name4,
            "region": region.id,
            "description": site_desc2,
        }
        try:
            nb.dcim.sites.create(**site_params)
            flash('Сайт создан успешно', category='success')
        except pynetbox.core.query.RequestError as ex:
            flash('Такой сайт уже существует', category='warning')


    else:
        flash('Такого дома в КЛАДРе нет.', category='warning')
        flash('Используем номер дома введенного вручную', category='warning')
        number_of_house = search.split(' ')[-1]
        _number_of_house = re.match('^\d+', number_of_house)

        if _number_of_house:

            _site_name_rus = ' '.join ([ _resu['typeShort'], _resu['name'], number_of_house ])
            _site_name_trans = transliterate(_site_name_rus)

            _slug_eng = ' '.join([ session['region_parent_slug'], _site_name_trans.replace('/', '-') ])
            _slug_slugifyed = slugify(_slug_eng)

            _site_desc = '. '.join([ _resu['typeShort'], _resu['name'] ])
            _site_desc2 = ' '.join([_site_desc, number_of_house])

            region = nb.dcim.regions.filter(slug=session['region_slug'])[0]

            site_params = {
                "slug": _slug_slugifyed,
                "name": _site_name_trans,
                "region": region.id,
                "description": _site_desc2,
            }

            try:
                nb.dcim.sites.create(**site_params)
                flash('Сайт создан успешно', category='success')
            except:
                flash('Такой сайт уже существует', category='warning')
        else:
           flash('Вы неправильно ввели в поиске номер дома', category='danger')


    return render_template('sites/step4.html', data={'site_params': site_params} )