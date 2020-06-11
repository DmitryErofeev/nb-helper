from flask import Flask, render_template
import pynetbox
from flask_wtf import FlaskForm
from wtforms import TextField, StringField, validators, SelectField, TextAreaField

app = Flask(__name__)
app.conﬁg['SECRET_KEY'] = 'hard to guess string'

nb_url = 'http://10.100.3.128:33080/'
token = '03319cd840dcea602826b4c1ba3012761ee49466'
nb = pynetbox.api(nb_url, token)

_list =  nb.dcim.regions.all()


class RegionForm(FlaskForm):
    regions = SelectField('Список регионов с родителями', choices=[])


@app.route('/', methods=['GET','POST'])
def count_regions():

    form = RegionForm()
    form.regions.choices = [(region.slug, ': '.join([str(region.parent), str(region.name)]))  for region in nb.dcim.regions.all() if region.parent]
    return render_template('index.html', list=_list, form=form)
    # print(_list)


if __name__ == '__main__':
    app.run()
