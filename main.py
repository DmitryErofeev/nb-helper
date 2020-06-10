from flask import Flask, render_template
import pynetbox

app = Flask(__name__)

nb_url = 'http://10.100.3.128:33080/'
token = '03319cd840dcea602826b4c1ba3012761ee49466'

