import sqlite3 as sql
from os import system
from sys import path

requirements = ['pyqt5']

for item in requirements:
    system(f'pip3 install {item}')


with sql.connect(f'{path[0]}/finances.db') as db:
    try:
        db.execute('''create table if not exists finance (
            ID integer primary key,
            Date text not null,
            Activity text,
            "Transaction Type" Text not null,
            "Other Party" Text,
            Value float not null
        )''')
        db.commit()
    except Exception as error:
        print(error)
    