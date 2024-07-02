import pyodbc
from sqlalchemy.engine import URL

DATABASE_CONFIG = {
    'DRIVER': 'SQL Server',
    'SERVER': 'minhhoa',
    'DATABASE': 'movie',
    'UID': 'sa',
    'PWD': '123'
}

connection_string = (
    f"DRIVER={{{DATABASE_CONFIG['DRIVER']}}};"
    f"SERVER={DATABASE_CONFIG['SERVER']};"
    f"DATABASE={DATABASE_CONFIG['DATABASE']};"
    f"UID={DATABASE_CONFIG['UID']};"
    f"PWD={DATABASE_CONFIG['PWD']}"
)

SQLALCHEMY_DATABASE_URI = URL.create(
    "mssql+pyodbc",
    query={"odbc_connect": connection_string}
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
