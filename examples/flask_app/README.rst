A teeny Flask app to demonstrate how Grift can be used
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install requirements:
    ``pip install -r requirements.txt``

Start the server:
    ``python app.py``

Start the server in debug mode with an environment variable:
    ``DEBUG=1 python app.py``

Once the server is running, try:
    ``curl http://localhost:5000/varz``
    ``curl http://localhost:5000/check/grift``


Caveats
~~~~~~~
The ``AppConfig`` class has a number of properties that are unused:
this is just to demonstrate some of the ``ConfigProperty`` options.

To explore further, try adding a Postgres database url to your environment
(e.g. ``export DATABASE_URL=postgres://...``). What happens if you start the 
server with a non-existent database configured? (hint: it shouldn't go well). 
NOTE: You'll need to ``pip install psycopg2`` before you try this.

