# pylint:disable=undefined-variable
import datetime as dt
import sqlite3 as sql
from csv import DictReader, DictWriter
from sys import path

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


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
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setAlignment(Qt.AlignVCenter)

        self.buttonLayout = QHBoxLayout()

        self.exportButton = QPushButton('Export CSV Template')
        self.exportButton.setStatusTip('Click to export a template csv that contains the last 5 records.')
        self.exportButton.clicked.connect(self.exportTemplate)
        self.buttonLayout.addWidget(self.exportButton)

        self.importButton = QPushButton('Import CSV')
        self.importButton.setStatusTip('Click to import data from CSV.')
        self.importButton.clicked.connect(self.getCSV)
        self.buttonLayout.addWidget(self.importButton)

        self.mainLayout.addLayout(self.buttonLayout)

        self.insertRecord = QPushButton('Insert Record')
        self.insertRecord.setStatusTip('Click to insert record into the database.')
        self.insertRecord.clicked.connect(self.insertWindow)
        widgets.append(self.insertRecord)

        self.dtbsContents = QPushButton('Access Data')
        self.dtbsContents.setStatusTip('Click to view financial data.')
        self.dtbsContents.clicked.connect(self.viewTable)
        widgets.append(self.dtbsContents)

        self.statusBar = QStatusBar(self)
        self.statusBar.setToolTip('Status bar')
        self.setStatusBar(self.statusBar)

        for widge in widgets:
            self.mainLayout.addWidget(widge)

        self.mainWidget = QWidget()
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

        self.setMinimumSize(self.mainLayout.sizeHint() * 2)


    def exportTemplate(self):
        "Exports a template CSV for the user to fill in."
        try:
            with sql.connect(f'{self.wrkngDrctry}/finances.db') as db:
                db.row_factory = dict_factory
                cursor = db.cursor()
                cursor.execute('select ID, Date, Activity, "Transaction Type", "Other Party", Value from finance order by ID desc limit 5')
                export = cursor.fetchall()

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
                                `Other Party` = "{values["Other Party"]}", Value = {values["Value"]}\
                                where ID = {values["ID"]}')
                            db.commit()
                            results['Updates'] += 1
                        else:
                            db.execute(f'insert into finance (Date, Activity, "Transaction Type", "Other Party", Value) values(?, ?, ?, ?, ?);', list(values.values())[1:])
                            db.commit()
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


    def insertWindow(self):
        "Create form for inserting a record."
        self.insert = dataInsertion(self)
        self.insert.show()


    def viewTable(self):
        "Initialises the data window."
        self.dataWindow = dataWindow(self)
        self.dataWindow.show()


class dataInsertion(QWidget):
    "Form for the insertion of data into the database."
    def __init__(self, parent: MainWindow, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Data Insertion')
        self.mainWindow = parent

        self.setMinimumHeight(self.mainWindow.minimumHeight())
        self.setMinimumWidth(self.mainWindow.minimumWidth())
        self.setMaximumHeight(round(self.mainWindow.maximumHeight()))
        self.setMaximumWidth(round(self.mainWindow.maximumWidth()))

        self.setGeometry(self.mainWindow.geometry())

        self.wrkngDrctry = self.mainWindow.wrkngDrctry

        self.mainLayout = QVBoxLayout()

        self.dataLayout = QVBoxLayout()
        self.dataLayout.setAlignment(Qt.AlignCenter)

        self.date = QCalendarWidget()
        self.date.setToolTip('Select transaction date.')
        self.date.setWindowTitle('Date')
        self.date.setFirstDayOfWeek(Qt.DayOfWeek(1))
        self.date.setMaximumDate(dt.date.today())
        self.date.setGridVisible(True)
        self.dataLayout.addWidget(self.date)

        self.details = QTextEdit('Enter transaction description...')
        self.details.setToolTip('Transaction description')
        self.dataLayout.addWidget(self.details)
        
        self.otherParty = QLineEdit('Enter other party...')
        self.otherParty.setToolTip('Other party')
        self.dataLayout.addWidget(self.otherParty)

        self.layout1 = QHBoxLayout()

        self.transactionType = QComboBox()
        self.transactionType.addItems(("Payment Received", "Loan Return", "Loan", "Paid"))
        self.transactionType.setToolTip('Transaction type')
        self.layout1.addWidget(self.transactionType)

        self.currency = QComboBox()
        self.currency.addItems(("USD", "ZWL"))
        self.currency.setToolTip('Currency')
        self.layout1.addWidget(self.currency)

        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator())
        self.value.setToolTip('Value')
        self.layout1.addWidget(self.value)

        self.dataLayout.addLayout(self.layout1)
        self.mainLayout.addLayout(self.dataLayout)

        self.mainLayout.addWidget(QLabel())

        self.saveLayout = QHBoxLayout()
        self.saveLayout.setAlignment(Qt.AlignBottom)
        self.saveLayout.setAlignment(Qt.AlignHCenter)

        self.closeBtn = QPushButton('Close')
        self.closeBtn.setToolTip('Close the window without saving')
        self.closeBtn.clicked.connect(self.close)
        self.saveLayout.addWidget(self.closeBtn)

        self.saveAndClose = QPushButton('Save and Close')
        self.saveAndClose.setToolTip('Save data and close window')
        self.saveAndClose.clicked.connect(self.saveClose)
        self.saveLayout.addWidget(self.saveAndClose)

        self.saveAndContinue = QPushButton('Save and Continue')
        self.saveAndContinue.setToolTip('Save data and continue')
        self.saveAndContinue.clicked.connect(self.saveContinue)
        self.saveLayout.addWidget(self.saveAndContinue)

        self.mainLayout.addLayout(self.saveLayout)

        self.setLayout(self.mainLayout)

        self.setMinimumSize(self.mainLayout.sizeHint())


    def saveClose(self):
        "Save user input and close the window."
        returns = self.collectData()
        message = btnPrmpt(*returns)
        message.exec_()
        self.close()


    def saveContinue(self):
        "Save the user input and reset the window."
        returns = self.collectData()
        message = btnPrmpt(*returns)
        message.exec_()
        self.date.setSelectedDate(dt.date.today())
        self.details.setText('Enter transaction description...')
        self.otherParty.setText('Enter other party...')
        self.value.setText('')


    def collectData(self):
        try:
            results = []
            date = self.date.selectedDate()
            results.append(dt.date(date.year(), date.month(), date.day()))
            results.append(self.details.toPlainText())
            results.append(self.otherParty.text())
            results.append(self.transactionType.currentText())
            #results.append(self.currency.currentText())
            results.append(round(float(self.value.text()), 2))
            
            with sql.connect('finances.db') as db:
                db.execute('insert into finance (Date, Activity, "Transaction Type", "Other Party", Value) values(?, ?, ?, ?, ?)', results)
                db.commit()
            
            return ('Success', 'Single', 'Data capture was successful.')
        except Exception as error:
            return ('Failure', 'Single', f'Data capture was unsuccessful.\nError message: {error.__str__()}')


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

        self.wrkngDrctry = parent.wrkngDrctry

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        self.contentTable = QTableWidget()
        self.contentQuery = 'select Date, Activity, "Transaction Type", "Other Party", round(Value, 2) Value from finance order by ID desc'
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


    def runQuery(self, query: str):
        "Run given query and return result."
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
            export = self.runQuery(query)
            if export:
                table.setRowCount(len(export))
                table.setColumnCount(5)

                table.horizontalHeader().setStretchLastSection(True) 
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) 

                columns = ['Date', 'Activity', 'Transaction Type', 'Other Party', 'Value']

                for i, title in enumerate(columns):
                    table.setHorizontalHeaderItem( i, QTableWidgetItem(title))

                for row in range(len(export)):
                    for column, col in enumerate(columns):
                        item = str(export[row][col])
                        if col == 'Value':
                            item = '$' + item
                        table.setItem(row, column, QTableWidgetItem(item))
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

        self.setMinimumSize(self.layout.sizeHint())


app = QApplication([])

screenRes = app.desktop().screenGeometry()

window = MainWindow(screenRes)
window.show()

app.exec_()