"Contains code related to the data window."
import sqlite3 as sql

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QHBoxLayout, QHeaderView, QLabel, QTableWidget,
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

        # Table for transaction history
        self.content_table = QTableWidget()
        self.content_query = 'select Date, Activity, "Transaction Type", "Other Party", '\
            'round(Value, 2) Value from finance order by ID desc'
        self.content_table_columns = [
            'Date', 'Activity', 'Transaction Type', 'Other Party', 'Value']
        if self.populate_table(self.content_table, self.content_table_columns, self.content_query):
            if self.content_table.rowCount() < 1:
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

        # Money totals tab
        self.money_totals = QWidget()
        self.totals_layout = QVBoxLayout()
        self.totals_layout.setAlignment(Qt.AlignCenter)

        # User balance
        self.balance_row = QHBoxLayout()
        self.balance_lbl = QLabel("Balance: ")
        self.balance_row.addWidget(self.balance_lbl)
        self.balance_query = r"select round(sum(case when `Transaction Type` like '%received%' or "\
            r"`Transaction Type` like '%return%' or `Transaction Type` like '%borrow from%' then "\
            r"Value else Value * -1 end), 2) balance from finance"
        self.balance = self.run_query(self.balance_query)[0]['balance']
        self.balance_amnt = QLabel(
            '$' + str(self.balance if self.balance else 0))
        self.balance_row.addWidget(self.balance_amnt)
        self.balance_row.setAlignment(Qt.AlignLeft)
        self.totals_layout.addLayout(self.balance_row)

        # Debtors table
        self.debtors = QTableWidget()
        self.debtors_columns = ["Debtor", "Amount Owed"]
        self.debtors_query = "select `Other Party` Debtor, sum(case when `Transaction Type` == "\
            "'Loan' then Value else (case when `Transaction Type` == 'Loan Return' then Value * -1"\
            " else 0 end) end) 'Amount Owed' from finance group by Debtor having `Amount Owed` != "\
            "0 order by `Amount Owed` desc"
        if self.populate_table(self.debtors, self.debtors_columns, self.debtors_query):
            if self.debtors.rowCount() < 1:
                self.debtors = QLabel("There are currently no debtors.")
        else:
            self.debtors = QLabel("Error displaying debtors.")
        self.totals_layout.addWidget(self.debtors)

        # Creditors table
        self.creditors = QTableWidget()
        self.creditors_columns = ["Creditor", "Amount Owed"]
        self.creditors_query = "select `Other Party` Creditor, sum(case when `Transaction Type` =="\
            " 'Borrow From' then Value else (case when `Transaction Type` == 'Payback' then Value"\
            " * -1 else 0 end) end) 'Amount Owed' from finance group by Creditor having `Amount "\
            "Owed` != 0 order by `Amount Owed` desc"
        if self.populate_table(self.creditors, self.creditors_columns, self.creditors_query):
            if self.creditors.rowCount() < 1:
                self.creditors = QLabel("There are currently no creditors.")
        else:
            self.creditors = QLabel("Error displaying creditors.")
        self.totals_layout.addWidget(self.creditors)

        self.money_totals.setLayout(self.totals_layout)
        self.tabs.addTab(self.money_totals, 'Totals')

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

    def populate_table(self, table: QTableWidget, columns: list, query: str):
        "Populate the given table"
        try:
            export = self.run_query(query)
            if export:
                table.setRowCount(len(export))
                table.setColumnCount(len(columns))

                table.horizontalHeader().setStretchLastSection(True)
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

                table.setSortingEnabled(True)

                for i, title in enumerate(columns):
                    table.setHorizontalHeaderItem(i, QTableWidgetItem(title))

                for row in enumerate(export):
                    for column, col in enumerate(columns):
                        item = str(export[row[0]][col])
                        if col == 'Value':
                            item = '$' + item
                        item = QTableWidgetItem(item)
                        item.setFlags(Qt.ItemIsEnabled)
                        table.setItem(row[0], column, item)
            return True
        except Exception:
            return False
