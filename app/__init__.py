from flask import Flask
from sqlalchemy import create_engine

app = Flask(__name__)
app.secret_key = "this is a secret shh"

DBHOST = 'localhost'
DBPORT = 5432
DBNAME = 'namely'
DBUSER = 'local_user'
DBPASS = 'a'
DBURI = ('postgresql+psycopg2://{}:{}@{}:{}/{}').format(DBUSER, DBPASS, DBHOST, DBPORT, DBNAME)

app.engine = create_engine(DBURI)

# db stuff..
# mkdir db
# initdb -D db
# postgres -D db >logfile 2>&1 &
# psql -c "CREATE ROLE local_user SUPERUSER LOGIN CREATEDB CREATEROLE REPLICATION;"
# psql -c "CREATE DATABASE namely;"
# psql -c "GRANT ALL PRIVILEGES ON DATABASE namely TO local_user;"
# createdb namely
# psql namely < schema.sql


from app import views

