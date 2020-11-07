"Contains code related to the data window."
import sqlite3 as sql

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QHeaderView, QLabel, QTableWidget,
                             QTableWidgetItem, QTabWidget, QVBoxLayout,
                             QWidget)

from helpers import dict_factory

from .btn_prompt import BtnPrmpt


class DataWindow(QWidget):
    "Displays the contents of the database and other data."

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Data Window')

        self.setMinimumHeight(parent.minimumHeight())
        self.setMinimumWidth(parent.minimumWidth())
        self.setMaximumHeight(round(parent.maximumHeight()))
        self.setMaximumWidth(round(parent.maximumWidth()))

        self.setGeometry(parent.geometry())

        self.wrkng_drctry = parent.wrkng_drctry

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        self.content_table = QTableWidget()
        self.content_query = 'select Date, Activity, "Transaction Type", "Other Party", '\
            'round(Value, 2) Value from finance order by ID desc'
        if self.populate_table(self.content_table, self.content_query):
            num_rows = self.content_table.rowCount()
            if num_rows > 0:
                self.tabs.addTab(self.content_table, 'Contents')
            else:
                self.content_table = QLabel('No results to display')
                self.content_table.setAlignment(Qt.AlignCenter)
                font = self.content_table.font()
                font.setPointSize(font.pointSize() * 5)
                self.content_table.setFont(font)
        else:
            self.content_table = QLabel(
                'Error occurred when trying to display results.')
            self.content_table.setAlignment(Qt.AlignCenter)
            font = self.content_table.font()
            font.setPointSize(font.pointSize() * 5)
            self.content_table.setFont(font)
        self.tabs.addTab(self.content_table, 'Transaction History')

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def run_query(self, query: str):
        "Run given query and return result."
        try:
            with sql.connect(f'{self.wrkng_drctry}/finances.db') as dtbse:
                dtbse.row_factory = dict_factory
                cursor = dtbse.cursor()
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as error:
            error_msg = BtnPrmpt('Error Message', 'Single', error.__str__())
            error_msg.exec_()
            return None

    def populate_table(self, table: QTableWidget, query: str):
        "Populate the given table"
        try:
            export = self.run_query(query)
            if export:
                table.setRowCount(len(export))
                table.setColumnCount(5)

                table.horizontalHeader().setStretchLastSection(True)
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

                columns = ['Date', 'Activity',
                           'Transaction Type', 'Other Party', 'Value']

                for i, title in enumerate(columns):
                    table.setHorizontalHeaderItem(i, QTableWidgetItem(title))

                for row in enumerate(export):
                    for column, col in enumerate(columns):
                        item = str(export[row[0]][col])
                        if col == 'Value':
                            item = '$' + item
                        table.setItem(row[0], column, QTableWidgetItem(item))
            return True
        except Exception:
            return False
