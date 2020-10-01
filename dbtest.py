import sqlite3 as sql
from sys import path
from datetime import date

with sql.connect(f'{path[0]}/finances.db') as db:
    cursor = db.cursor()
    cursor.execute('select * from finance')
    content = cursor.fetchall()

    for row in content:
        try:
            print(row)
        except:
            pass