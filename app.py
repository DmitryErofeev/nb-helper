from flask import Flask, render_template
from flask_bootstrap import Bootstrap
import pynetbox, os
from devices.blueprint import add_device
from sites.blueprint import add_site


app = Flask(__name__)
Bootstrap(app)
app.conﬁg['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'hard to guess string'

app.register_blueprint(add_device, url_prefix='/devices')
app.register_blueprint(add_site, url_prefix='/sites')


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
