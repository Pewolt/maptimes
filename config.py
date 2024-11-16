# config.py
import configparser

config = configparser.ConfigParser()
config.read('database/config.ini')

# Datenbankkonfiguration
DB_CONFIG = {
    'host': config.get('database', 'host'),
    'dbname': config.get('database', 'dbname'),
    'user': config.get('database', 'user'),
    'password': config.get('database', 'password')
}
