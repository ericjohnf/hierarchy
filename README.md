Setup instructions:

#### Install requirements 
```sh
pip install -r requirements.txt
```

#### Install PostgreSQL
```sh
brew install postgres
```

#### To run database locally
```sh
initdb -D /usr/local/pgsql/data
pg_ctl -D /usr/local/pgsql/data -l logfile start
createdb namely
psql -c "CREATE ROLE local_user SUPERUSER LOGIN CREATEDB CREATEROLE REPLICATION;"
psql -c "GRANT ALL PRIVILEGES ON DATABASE namely TO local_user;"
psql namely < schema.sql
```
#### Run the app
```sh
python run.py
```
