from flask import Flask, render_template
from flask_bootstrap import Bootstrap
import os
from devices.blueprint import add_device
from sites.blueprint import add_site
from utils.blueprint import add_utils
from cache import cache

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or os.urandom(32)
app.config['CACHE_TYPE'] = os.getenv('CACHE_TYPE') or 'simple'
cache.init_app(app)


app.register_blueprint(add_device, url_prefix='/devices')
app.register_blueprint(add_site, url_prefix='/sites')
app.register_blueprint(add_utils, url_prefix='/utils')


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
