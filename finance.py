from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from csv import DictReader, DictWriter
from sys import path

import sqlite3 as sql


class MainWindow(QMainWindow):
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
        try:
            with sql.connect(f'{self.wrkngDrctry}/finances.db') as db:
                cursor = db.cursor()
                cursor.execute('select Date, Activity, "Transaction Type", "Other Party", Value from finance order by ID desc limit 5')
                export = cursor.fetchall()

            with open(f'{self.wrkngDrctry}/template.csv', 'w') as template:
                writer = DictWriter(template, ['Date', 'Activity', 'Transaction Type', 'Other Party', 'Value'])
                writer.writeheader()
                for record in export:
                    writer.writerow(record)
            
            successMsg = btnPrmpt('Success', 'Single', 'Template successfully exported.')
            successMsg.exec_()
        except Exception as error:
            errorMsg = btnPrmpt('Error Message', 'Single', error.__str__())
            errorMsg.exec_()


    def getCSV(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setNameFilter('Text files (*.csv)')
        dlg.setDirectory(QDir(self.wrkngDrctry))
        
        while dlg.exec_():
            self.csvFile = dlg.selectedFiles()[0]
            if '.csv' in self.csvFile:
                self.importCSV()
                break
            else:
                warning = btnPrmpt('Warning', 'Y / N', 'Selected file must be of type CSV.\nDo you wish to continue?')
                if not warning.exec_():
                    return


    def importCSV(self):
        with open(self.csvFile) as dataImport:
            reader = DictReader(dataImport)
            with sql.connect(f'{self.wrkngDrctry}/finances.db') as db:
                self.failedImports = []
                numImports = 0
                numFailures = 0
                for record in reader:
                    try:
                        if not record['Date'] or not record['Other Party'] or not record['Value'] or \
                            (type(record['Value']) != type(1.5) and type(record['Value']) != type(1)):
                            raise Exception
                        db.execute('insert into finance (Date, Activity, "Transaction Type", "Other Party", Value) values(?, ?, ?, ?, ?);', list(record.values()))
                        numImports += 1
                    except Exception as error:
                        self.failedImports.append(record)
                if self.failedImports:
                    with open(f'{self.wrkngDrctry}/failedImports.csv', 'w') as failures:
                        writer = DictWriter(failures, ['Date', 'Activity', 'Transaction Type', 'Other Party', 'Value'])
                        writer.writeheader()
                        for record in self.failedImports:
                            numFailures += 1
                            writer.writerow(record)
                if numImports or numFailures:
                    successMsg = btnPrmpt('Successes', 'Single', f'{numImports} records successfully imported.\n{numFailures} were not imported.')
                    successMsg.exec_()


    def viewTable(self):
        self.dataWindow = dataWindow(self.height, self.width)
        self.dataWindow.show()


class dataWindow(QWidget):
    def __init__(self, height, width, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Data Window')

        self.height = round(height * 0.5)
        self.width = round(width * 0.5)
        self.posY = round((height / 2) - (self.geometry().height() / 2))
        self.posX = round((width / 2) - (self.geometry().width() / 2))

        self.setMinimumHeight(round(self.height / 2))
        self.setMinimumWidth(round(self.width / 2))
        self.setMaximumHeight(round(height))
        self.setMaximumWidth(round(width))

        self.setGeometry(QRect(self.posX, self.posX, self.width, self.height))

        self.wrkngDrctry = path[0]

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        self.contentTable = QTableWidget()
        self.generateContent()    
        self.tabs.addTab(self.contentTable, 'Contents')

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)


    def generateContent(self):
        try:
            with sql.connect(f'{self.wrkngDrctry}/finances.db') as db:
                cursor = db.cursor()
                cursor.execute('select Date, Activity, "Transaction Type", "Other Party", Value from finance order by ID desc')
                export = cursor.fetchall()
        except Exception as error:
            errorMsg = btnPrmpt('Error Message', 'Single', error.__str__())
            errorMsg.exec_()

        self.contentTable.setRowCount(len(export) + 1)
        self.contentTable.setColumnCount(5)

        self.contentTable.horizontalHeader().setStretchLastSection(True) 
        self.contentTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) 

        for i, title in enumerate(['Date', 'Activity', 'Transaction Type', 'Other Party', 'Value']):
            self.contentTable.setItem(0, i, QTableWidgetItem(title))
            self.contentTable.item(0, i).setTextAlignment(Qt.AlignCenter)


class btnPrmpt(QDialog):

    def __init__(self, title: str, dlgType: str, msg: str, *args, **kwargs):
        super(btnPrmpt, self).__init__(*args, **kwargs)

        self.setWindowTitle(title)
        self.setMinimumHeight(100)
        self.setMinimumWidth(250)

        self.layout = QVBoxLayout()
        
        self.message = QLabel(msg)
        self.message.setAlignment(Qt.AlignCenter)
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