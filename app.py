from flask import Flask
from flask_bootstrap import Bootstrap
import pynetbox, os
from device.blueprint import add_device


app = Flask(__name__)
Bootstrap(app)
app.conﬁg['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'hard to guess string'

app.register_blueprint(add_device, url_prefix='/device')


if __name__ == '__main__':
    app.run()
