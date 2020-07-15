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


@add_utils.route('/', methods=['POST', 'GET'])
def utils():
    form = UtilsForm()
    if request.method == 'POST':
        _trans = transliterate(request.form.get('input_for_transliterate'))
        trans = _trans.replace('.', "")  # TODO: сделать функцией подготовки

        form.output_transliterated.data = trans

        slug = slugify(trans.replace('/', "-"))
        form.output_slugifyed.data = slug
    return render_template('utils/utils.html', form=form)