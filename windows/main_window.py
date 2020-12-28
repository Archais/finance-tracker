"Contains code related to the main window."
import datetime as dt
import sqlite3 as sql
from csv import DictReader, DictWriter
from sys import path

from PyQt5.QtCore import QDir, QRect, Qt
from PyQt5.QtWidgets import (QFileDialog, QHBoxLayout, QMainWindow,
                             QPushButton, QStatusBar, QVBoxLayout, QWidget)

from helpers import center_window, dict_factory

from .btn_prompt import BtnPrmpt
from .data_window import DataWindow
from .insertion import DataInsertion


class MainWindow(QMainWindow):
    "Program's main window."

    def __init__(self, res: QRect, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Finance Tracker")

        self.height = res.height()
        self.width = res.width()

        self.setMinimumHeight(round(self.height * 0.25))
        self.setMinimumWidth(round(self.width * 0.25))
        self.setMaximumHeight(round(self.height))
        self.setMaximumWidth(round(self.width))

        self.move(round((self.width / 2) - (self.geometry().width() / 2)),
                  round((self.height / 2) - (self.geometry().height() / 2)))

        self.wrkng_drctry = path[0]

        widgets = []
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignVCenter)

        self.button_layout = QHBoxLayout()

        self.csv_file = ""
        self.export_button = QPushButton('Export CSV Template')
        self.export_button.setStatusTip(
            'Click to export a template csv that contains the last 5 records.')
        self.export_button.clicked.connect(self.export_template)
        self.button_layout.addWidget(self.export_button)

        self.import_button = QPushButton('Import CSV')
        self.import_button.setStatusTip('Click to import data from CSV.')
        self.import_button.clicked.connect(self.get_csv)
        self.button_layout.addWidget(self.import_button)

        self.main_layout.addLayout(self.button_layout)

        self.insert_record = QPushButton('Insert Record')
        self.insert_record.setStatusTip(
            'Click to insert record into the database.')
        self.insert = None
        self.insert_record.clicked.connect(self.insert_window)
        widgets.append(self.insert_record)

        self.dtbs_contents = QPushButton('Access Data')
        self.dtbs_contents.setStatusTip('Click to view financial data.')
        self.data_window = None
        self.dtbs_contents.clicked.connect(self.view_table)
        widgets.append(self.dtbs_contents)

        self.status_bar = QStatusBar(self)
        self.status_bar.setToolTip('Status bar')
        self.setStatusBar(self.status_bar)

        for widge in widgets:
            self.main_layout.addWidget(widge)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        self.setMinimumSize(self.main_layout.sizeHint() * 2)
        center_window(self)

    def export_template(self):
        "Exports a template CSV for the user to fill in."
        try:
            with sql.connect(f'{self.wrkng_drctry}/finances.db') as dtbse:
                dtbse.row_factory = dict_factory
                cursor = dtbse.cursor()
                cursor.execute(
                    'select ID, Date, Activity, "Transaction Type", "Other Party", Value'
                    ' from finance order by ID desc limit 5')
                export = cursor.fetchall()

            with open(f'{self.wrkng_drctry}/template.csv', 'w') as template:
                cols = ('ID', 'Date', 'Activity',
                        'Transaction Type', 'Other Party', 'Value')
                writer = DictWriter(template, cols)
                writer.writeheader()
                for record in export:
                    writer.writerow(record)

            success_msg = BtnPrmpt(
                'Success',
                'Single',
                'Template successfully exported.\n\nID field must be empty to insert new records, '
                'otherwise the record will be updated if there are any matching; dates must be in '
                'ISO format otherwise they will not be accepted.')
            success_msg.exec_()
        except Exception as error:
            error_msg = BtnPrmpt('Error Message', 'Single', error.__str__())
            error_msg.exec_()

    def get_csv(self):
        "Provides a file dialog to allow the user to choose their CSV file."
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setNameFilter('Text files (*.csv)')
        dlg.setDirectory(QDir(self.wrkng_drctry))

        while dlg.exec_():
            self.csv_file = dlg.selectedFiles()[0]
            if '.csv' in self.csv_file:
                self.import_csv()
                return True
            warning = BtnPrmpt(
                'Warning', 'Y / N', 'Selected file must be of type CSV.\nDo you wish to continue?')
            if not warning.exec_():
                return False

    def import_csv(self):
        "Imports user's chosen CSV"
        with open(self.csv_file) as data_import:
            reader = DictReader(data_import)
            with sql.connect(f'{self.wrkng_drctry}/finances.db') as dtbse:
                valid_csv = True
                msg = 'There were no records to import.'
                keys = ['ID', 'Date', 'Activity',
                        'Transaction Type', 'Other Party', 'Value']
                failed_imports = []
                results = {'Inserts': 0, 'Updates': 0, 'Failures': 0}
                for record in reader:
                    values = {}
                    for key in keys:
                        if key not in record.keys():
                            msg = 'Invalid CSV file, please export a template and try again.'
                            valid_csv = False
                            break
                        else:
                            values[key] = record[key]
                    if not valid_csv:
                        break

                    if not values['ID']:
                        values['ID'] = '-'

                    try:
                        if not values['Date'] or not values['Transaction Type'] \
                                or not values['Other Party'] or not values['Value']:
                            values['Reason'] = 'Missing values'
                            raise Exception

                        if values['ID'].isnumeric():
                            values['ID'] = int(values['ID'])
                        elif values['ID'] != '-':
                            values['Reason'] = 'Invalid ID'
                            raise Exception

                        try:
                            date_len = len(values['Date'])
                            date_sep = ''
                            for sep in ['-', '\\', '/']:
                                if sep in values['Date']:
                                    if date_sep:
                                        raise Exception
                                    date_sep = sep
                            if 6 < date_len < 11 and values['Date'].count(date_sep, 4, 8) == 2:
                                date = values['Date'].split(date_sep)
                                if len(date) != 3:
                                    raise Exception
                                for elem in date:
                                    for digit in elem:
                                        if not digit.isnumeric():
                                            raise Exception
                                year = int(date[0])
                                if len(date[0]) != 4:
                                    raise Exception
                                month = int(date[1])
                                if (len(date[1]) != 1 and len(date[1]) != 2) or 12 < month < 1:
                                    raise Exception
                                day = int(date[2])
                                if (len(date[2]) != 1 and len(date[2]) != 2) or day < 1 or day > 31:
                                    raise Exception
                            else:
                                raise Exception
                            values['Date'] = dt.date(year, month, day)
                        except Exception:
                            values['Reason'] = 'Invalid date'
                            raise Exception

                        try:
                            values['Value'] = float(values['Value'])
                        except Exception:
                            values['Reason'] = "Invalid transaction value"
                            raise Exception

                        if isinstance(values['ID'], int):
                            dtbse.execute(f'update finance\
                                set Date = "{values["Date"]}", Activity = "{values["Activity"]}", `Transaction Type` = "{values["Transaction Type"]}",\
                                `Other Party` = "{values["Other Party"]}", Value = {values["Value"]}\
                                where ID = {values["ID"]}')
                            dtbse.commit()
                            results['Updates'] += 1
                        else:
                            dtbse.execute(
                                'insert into finance (Date, Activity, "Transaction Type", '
                                '"Other Party", Value) values(?, ?, ?, ?, ?);',
                                list(values.values())[1:]
                            )
                            dtbse.commit()
                            results['Inserts'] += 1

                    except Exception as error:
                        if 'Reason' not in values.keys():
                            values['Reason'] = error.__str__()
                        failed_imports.append(values)
                if failed_imports and valid_csv:
                    with open(f'{self.wrkng_drctry}/failed_imports.csv', 'w') as failures:
                        keys.append('Reason')
                        writer = DictWriter(failures, keys)
                        writer.writeheader()
                        for record in failed_imports:
                            results['Failures'] += 1
                            writer.writerow(record)
                if (results['Inserts'] or results['Updates'] or results['Failures']) and valid_csv:
                    msg = f'{results["Inserts"]} records successfully imported.'\
                        f'\n{results["Updates"]} records successfully updated.'\
                        f'\n{results["Failures"]} were not imported.'
                success_msg = BtnPrmpt('Import Results', 'Single', msg)
                success_msg.exec_()

    def insert_window(self):
        "Create form for inserting a record."
        self.insert = DataInsertion(self)
        self.insert.show()

    def view_table(self):
        "Initialises the data window."
        self.data_window = DataWindow(self)
        self.data_window.show()
