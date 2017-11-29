"""A teeny Flask app to demonstrate how Grift can be used

Install requirements:
  pip install -r requirements.txt

Start the server:
  python app.py

Start the server in DEBUG mode:
  DEBUG=1 python app.py

Once the server is running, try:
  curl http://localhost:5000/varz
  curl http://localhost:5000/check/grift
"""
import logging

import flask

from config import app_config

app = flask.Flask(__name__)
# Set the debug level and configure logging
app.debug = app_config.DEBUG
app.logger.setLevel(app_config.LOG_LEVEL)

# NOT IMPLEMENTED:
# - Use a Postgres database, using app_config.DATABASE_URL as the
#   database url
# - Use another API with app_config.API_TOKEN and app_config.API_URL


@app.route('/check/<name>')
def check(name):
    """Check if a thing is awesome"""
    app.logger.info('Checking if %s is awesome', name)
    return '{} is awesome!!\n'.format(name)


@app.route('/varz')
def varz():
    """Expose non-sensitive settings"""
    return flask.json.jsonify(app_config.varz)


if __name__ == '__main__':
    # Run the app on the configured port
    app.run(port=app_config.PORT)



