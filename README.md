# undl_proxy
Proxy app to UNDL searches

Install PostgreSQL
create database "proxy"
create role "proxy" with password "proxy"
grant all privileges in database "proxy" to role "proxy"
alter role proxy CREATEDB -- needed for testing

pip install -r requirements.txt

python create_db.py -- creates proxy database if it does not already exist

