# pylint:disable=undefined-variable
from PyQt5.QtWidgets import * 
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from csv import DictReader, DictWriter
from sys import path

import sqlite3 as sql, datetime as dt

def dict_factory(cursor, row):
    "Causes SQLite3 queries to return as dictionaries"
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class MainWindow(QMainWindow):
    "Program's main window."
    def __init__(self, res, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Finance Tracker")
        self.setWindowIcon(QIcon(QPixmap('/home/archais/Python Programs/pyqt/Folder.jpg')))

        self.height = res.height()
        self.width = res.width()

        self.setMinimumHeight(round(self.height * 0.25))
        self.setMinimumWidth(round(self.width * 0.25))
        self.setMaximumHeight(round(self.height))
        self.setMaximumWidth(round(self.width))

        self.move(round((self.width / 2) - (self.geometry().width() / 2)), round((self.height / 2) - (self.geometry().height() / 2)))

        self.wrkngDrctry = path[0]

        
        widgets = []
        layout = QVBoxLayout()

        buttonLayout = QHBoxLayout()

        self.exportButton = QPushButton('Export CSV Template')
        self.exportButton.setStatusTip('Click to export a template csv that contains the last 5 records.')
        self.exportButton.clicked.connect(self.exportTemplate)
        buttonLayout.addWidget(self.exportButton)

        self.importButton = QPushButton('Import CSV')
        self.importButton.setStatusTip('Click to import data from CSV.')
        self.importButton.clicked.connect(self.getCSV)
        buttonLayout.addWidget(self.importButton)

        layout.addLayout(buttonLayout)

        self.dtbsContents = QPushButton('Access Data')
        self.dtbsContents.setStatusTip('Click to view financial data.')
        self.dtbsContents.clicked.connect(self.viewTable)
        widgets.append(self.dtbsContents)

        self.statusBar = QStatusBar(self)
        self.statusBar.setToolTip('Status bar')
        widgets.append(self.statusBar)

        for widge in widgets:
            layout.addWidget(widge)

        self.widget = QWidget()
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)


    def exportTemplate(self):
        "Exports a template CSV for the user to fill in."
        try:
            with sql.connect(f'{self.wrkngDrctry}/finances.db') as db:
                db.row_factory = dict_factory
                cursor = db.cursor()
                cursor.execute('select ID, Date, Activity, "Transaction Type", "Other Party", Value from finance order by ID desc limit 5')
                export = cursor.fetchall()
                print('exported content')

            with open(f'{self.wrkngDrctry}/template.csv', 'w') as template:
                cols = ('ID', 'Date', 'Activity', 'Transaction Type', 'Other Party', 'Value')
                writer = DictWriter(template, cols)
                writer.writeheader()
                for record in export:
                    writer.writerow(record)
            
            successMsg = btnPrmpt('Success', 'Single', 'Template successfully exported.\n\nID field must be empty to insert new records, otherwise the record will be updated if there are any matching; dates must be in ISO format otherwise they will not be accepted.')
            successMsg.exec_()
        except Exception as error:
            errorMsg = btnPrmpt('Error Message', 'Single', error.__str__())
            errorMsg.exec_()


    def getCSV(self):
        "Provides a file dialog to allow the user to choose their CSV file."
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setNameFilter('Text files (*.csv)')
        dlg.setDirectory(QDir(self.wrkngDrctry))
        
        while dlg.exec_():
            self.csvFile = dlg.selectedFiles()[0]
            if '.csv' in self.csvFile:
                self.importCSV()
                return True
            else:
                warning = btnPrmpt('Warning', 'Y / N', 'Selected file must be of type CSV.\nDo you wish to continue?')
                if not warning.exec_():
                    return False


    def importCSV(self):
        "Imports user's chosen CSV"
        with open(self.csvFile) as dataImport:
            reader = DictReader(dataImport)
            with sql.connect(f'{self.wrkngDrctry}/finances.db') as db:
                validCSV = True
                msg = 'There were no records to import.'
                keys = ['ID', 'Date', 'Activity', 'Transaction Type', 'Other Party', 'Value']
                self.failedImports = []
                results = {'Inserts': 0, 'Updates': 0, 'Failures': 0}
                for record in reader:
                    values = {}
                    for key in keys:
                        if key not in record.keys():
                            msg = 'Invalid CSV file, please export a template and try again.'
                            validCSV = False
                            break
                        else:
                            values[key] = record[key]
                    if not validCSV:
                        break

                    if not values['ID']:
                        values['ID'] = '-'
 
                    try:
                        if not values['Date'] or not values['Transaction Type'] or not values['Other Party'] or not values['Value']:
                            values['Reason'] = 'Missing values'
                            raise Exception

                        if values['ID'].isnumeric():
                            values['ID'] = int(values['ID'])
                        elif values['ID'] != '-':
                            values['Reason'] = 'Invalid ID'
                            raise Exception

                        try:
                            dateLen = len(values['Date'])
                            dateSep = ''
                            for sep in ['-', '\\', '/']:
                                if sep in values['Date']:
                                    if dateSep:
                                        raise Exception
                                    dateSep = sep
                            if dateLen > 7 and dateLen < 11 and values['Date'].count(dateSep, 4, 8) == 2:
                                print(values["Date"])
                                date = values['Date'].split(dateSep)
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
                                if (len(date[1]) != 1 and len(date[1]) != 2) or month < 1 or month > 12:
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

                        if type(values['ID']) == int:
                            db.execute(f'update finance\
                                set Date = "{values["Date"]}", Activity = "{values["Activity"]}", `Transaction Type` = "{values["Transaction Type"]}",\
                                `Other Party` = "{values["Other Party"]}", Value = {values["Value"]} where ID = {values["ID"]}')
                            results['Updates'] += 1
                        else:
                            db.execute(f'insert into finance (Date, Activity, "Transaction Type", "Other Party", Value) values(?, ?, ?, ?, ?);', list(values.values())[1:])
                            results['Inserts'] += 1

                    except Exception as error:
                        if 'Reason' not in values.keys():
                            values['Reason'] = error.__str__()
                        self.failedImports.append(values)
                if self.failedImports and validCSV:
                    with open(f'{self.wrkngDrctry}/failedImports.csv', 'w') as failures:
                        keys.append('Reason')
                        writer = DictWriter(failures, keys)
                        writer.writeheader()
                        for record in self.failedImports:
                            results['Failures'] += 1
                            writer.writerow(record)
                if (results['Inserts'] or results['Updates'] or results['Failures']) and validCSV:
                    msg = f'{results["Inserts"]} records successfully imported.\n{results["Updates"]} records successfully updated.\n{results["Failures"]} were not imported.'
                successMsg = btnPrmpt('Import Results', 'Single', msg)
                successMsg.exec_()


    def viewTable(self):
        "Initialises the data window."
        self.dataWindow = dataWindow(self)
        self.dataWindow.show()


class dataWindow(QWidget):
    "Displays the contents of the database and other data."
    def __init__(self, parent: MainWindow, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Data Window')

        self.setMinimumHeight(parent.minimumHeight())
        self.setMinimumWidth(parent.minimumWidth())
        self.setMaximumHeight(round(parent.maximumHeight()))
        self.setMaximumWidth(round(parent.maximumWidth()))

        self.setGeometry(parent.geometry())

        self.wrkngDrctry = path[0]

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        self.contentTable = QTableWidget()
        self.contentQuery = 'select Date, Activity, "Transaction Type", "Other Party", Value from finance order by ID desc'
        if self.populateTable(self.contentTable, self.contentQuery):
            numRows = self.contentTable.rowCount()
            if numRows > 0:
                self.tabs.addTab(self.contentTable, 'Contents')
            else:
                self.contentTable = QLabel('No results to display')
                self.contentTable.setAlignment(Qt.AlignCenter)
                font = self.contentTable.font()
                font.setPointSize(font.pointSize() * 5)
                self.contentTable.setFont(font)
        else:
            self.contentTable = QLabel('Error occurred when trying to display results.')
            self.contentTable.setAlignment(Qt.AlignCenter)
            font = self.contentTable.font()
            font.setPointSize(font.pointSize() * 5)
            self.contentTable.setFont(font)
        self.tabs.addTab(self.contentTable, 'Transaction History')

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)


    def generateContent(self, query: str):
        "Run given query and return result"
        try:
            with sql.connect(f'{self.wrkngDrctry}/finances.db') as db:
                db.row_factory = dict_factory
                cursor = db.cursor()
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as error:
            errorMsg = btnPrmpt('Error Message', 'Single', error.__str__())
            errorMsg.exec_()
            return None


    def populateTable(self, table: QTableWidget, query: str):
        "Populate the given table"
        try:
            export = self.generateContent(query)
            if export:
                table.setRowCount(len(export))
                table.setColumnCount(5)

                table.horizontalHeader().setStretchLastSection(True) 
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) 

                columns = ['Date', 'Activity', 'Transaction Type', 'Other Party', 'Value']

                for i, title in enumerate(columns):
                    table.setHorizontalHeaderItem( i, QTableWidgetItem(title))
                print(export)
                for row in range(len(export)):
                    for column, col in enumerate(columns):
                        table.setItem(row, column, QTableWidgetItem(str(export[row][col])))
            return True
        except Exception:
            return False

class btnPrmpt(QDialog):
    "Creates a prompt that displays a particular message, with buttons to provide a response."
    def __init__(self, title: str, dlgType: str, msg: str, *args, **kwargs):
        super(btnPrmpt, self).__init__(*args, **kwargs)

        self.setWindowTitle(title)
        self.setMinimumHeight(100)
        self.setMinimumWidth(250)

        self.layout = QVBoxLayout()
        
        self.message = QLabel(msg)
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setWordWrap(True)
        self.layout.addWidget(self.message)

        if dlgType == 'Y / N':
            self.QBtn = QDialogButtonBox.Yes | QDialogButtonBox.No
        elif dlgType == 'Single':
            self.QBtn = QDialogButtonBox.Ok
        else:
            self.QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(self.QBtn)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)


app = QApplication([])

screenRes = app.desktop().screenGeometry()

window = MainWindow(screenRes)
window.show()

app.exec_()