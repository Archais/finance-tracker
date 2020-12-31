"Contains code related to the data window."
import sqlite3 as sql
import pyqtgraph as pg

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import (QAction, QHBoxLayout, QHeaderView, QLabel, QTableWidget,
                             QTableWidgetItem, QTabWidget, QToolBar, QVBoxLayout,
                             QWidget)

from helpers import center_window, dict_factory

from .btn_prompt import BtnPrmpt


class DataWindow(QWidget):
    "Displays the contents of the database and other data."

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Data Window')

        self.setMinimumHeight(parent.minimumHeight() * 2)
        self.setMinimumWidth(parent.minimumWidth() * 2)
        self.setMaximumHeight(round(parent.maximumHeight()))
        self.setMaximumWidth(round(parent.maximumWidth()))

        self.wrkng_drctry = parent.wrkng_drctry

        self.layout = QVBoxLayout()

        self.toolbar = QToolBar('Toolbar')
        refresh = QAction('Refresh', self)
        refresh.setToolTip("Refresh Window")
        refresh.triggered.connect(self.refresh)
        self.toolbar.addAction(refresh)
        self.layout.addWidget(self.toolbar)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        # Money totals tab
        self.set_tabs()
        self.tabs.addTab(self.money_totals, 'Balance Sheet')
        self.tabs.addTab(self.content_table, 'Transaction History')
        self.tabs.addTab(self.metrics, "Graphs")

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        center_window(self)

    def set_tabs(self):
        "Set tabs."
        # Money totals tab
        self.money_totals = QWidget()
        self.balance_amnt = QLabel()
        self.debtors = QTableWidget()
        self.creditors = QTableWidget()
        self.balance_sheet()

        # Table for transaction history
        self.content_table = QTableWidget()
        self.create_transaction_history()

        # Balance graphs across the year
        self.metrics = QWidget()
        self.metrics_layout = QVBoxLayout(self.metrics)

        self.income_and_expense = pg.PlotWidget()
        self.draw_ie_chart()
        self.metrics_layout.addWidget(self.income_and_expense)

    def balance_sheet(self, refresh: bool = False):
        "Generate balance sheet."
        # SQL queries for displayed data
        queries = {
            'balance': r"select round(sum(case when `Transaction Type` like '%received%' or "\
                r"`Transaction Type` like '%return%' or `Transaction Type` like '%borrow from%' "\
                r"then Value else Value * -1 end), 2) balance from finance",
            'debtors': "select `Other Party` Debtor, sum(case when `Transaction Type` == "\
                "'Loan' then Value else (case when `Transaction Type` == 'Loan Return' then Value "\
                "* -1 else 0 end) end) 'Amount Owed' from finance group by Debtor having `Amount "\
                "Owed` != 0 order by `Amount Owed` desc",
            'creditors': "select `Other Party` Creditor, sum(case when `Transaction Type` =="\
                " 'Borrow From' then Value else (case when `Transaction Type` == 'Payback' then "\
                "Value * -1 else 0 end) end) 'Amount Owed' from finance group by Creditor having "\
                "`Amount Owed` != 0 order by `Amount Owed` desc"
        }

        # User balance
        balance = self.run_query(queries['balance'])[0]['balance']
        self.balance_amnt.setText('$' + str(balance if balance else 0))

        # Debtors table
        debtors_columns = ["Debtor", "Amount Owed"]
        if self.populate_table(self.debtors, debtors_columns, queries['debtors']):
            if self.debtors.rowCount() < 1:
                self.debtors = QLabel("There are currently no debtors.")
        else:
            self.debtors = QLabel("Error displaying debtors.")

        # Creditors table
        creditors_columns = ["Creditor", "Amount Owed"]
        if self.populate_table(self.creditors, creditors_columns, queries['creditors']):
            if self.creditors.rowCount() < 1:
                self.creditors = QLabel("There are currently no creditors.")
        else:
            self.creditors = QLabel("Error displaying creditors.")

        if not refresh:
            totals_layout = QVBoxLayout()
            totals_layout.setAlignment(Qt.AlignCenter)

            # User balance
            balance_row = QHBoxLayout()
            balance_lbl = QLabel("Balance: ")
            balance_row.addWidget(balance_lbl)
            balance_row.addWidget(self.balance_amnt)
            balance_row.setAlignment(Qt.AlignLeft)
            totals_layout.addLayout(balance_row)

            totals_layout.addWidget(self.debtors)

            totals_layout.addWidget(self.creditors)

            self.money_totals.setLayout(totals_layout)

    def create_transaction_history(self):
        "Generates transaction history table."
        content_query = 'select Date, Activity, "Transaction Type", "Other Party", '\
            'round(Value, 2) Value from finance order by Date desc'
        content_table_columns = [
            'Date', 'Activity', 'Transaction Type', 'Other Party', 'Value']
        if self.populate_table(self.content_table, content_table_columns, content_query):
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

    def run_query(self, query: str, return_dict: bool = True):
        "Run given query and return result."
        try:
            with sql.connect(f'{self.wrkng_drctry}/finances.db') as dtbse:
                if return_dict:
                    dtbse.row_factory = dict_factory
                cursor = dtbse.cursor()
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as error:
            error_msg = BtnPrmpt('Error Message', 'Single', error.__str__())
            error_msg.exec_()
            return None

    def populate_table(self, table: QTableWidget, columns: list, query: str):
        "Populate the given table."
        try:
            table.clearContents()
            export = self.run_query(query, True)
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
                        if col in ('Value', 'Amount Owed'):
                            item = '$' + item
                        item = QTableWidgetItem(item)
                        item.setFlags(Qt.ItemIsEnabled)
                        table.setItem(row[0], column, item)
            return True
        except Exception:
            return False

    def draw_ie_chart(self):
        "Draw chart for monthly income & expense."
        self.income_and_expense.clear()
        income_query = r"select strftime('%m', Date) Month, sum(case when `Transaction "\
            r"Type` in ('Payment Received', 'Loan Return', 'Borrow From') then Value else 0 end) "\
            r"Income from finance where strftime('%Y', Date) = "\
            r"strftime('%Y', 'now') group by strftime('%m', Date);"
        expense_query = r"select strftime('%m', Date) Month, sum(case when `Transaction "\
            r"Type` in ('Paid', 'Loan', 'Payback') then Value else 0 end) "\
            r"Expense from finance where strftime('%Y', Date) = "\
            r"strftime('%Y', 'now') group by strftime('%m', Date);"

        try:
            income_pen = pg.mkPen(color=(0, 255, 0))
            expense_pen = pg.mkPen(color=(255, 0, 0))
            self.income_and_expense.setXRange(1, 12)
            self.income_and_expense.addLegend()
            self.draw_graph(self.income_and_expense,
                            income_query, income_pen, "Income")
            self.draw_graph(self.income_and_expense,
                            expense_query, expense_pen, "Expense")
            self.income_and_expense.setTitle("Monthly Income & Expense")
            self.income_and_expense.setLabel('left', "Money ($)")
            self.income_and_expense.setLabel('bottom', "Month")
            self.income_and_expense.setBackground(
                self.palette().color(QPalette.Window))
            limits = self.income_and_expense.getViewBox().viewRange()
            self.income_and_expense.getViewBox().setLimits(
                xMin=limits[0][0], xMax=limits[0][1], yMin=limits[1][0], yMax=limits[1][1])
            self.setMinimumSize(self.income_and_expense.sizeHint())
        except Exception:
            self.income_and_expense = QLabel(
                "Unable to draw Income & Expense graph.")
            self.income_and_expense.setAlignment(Qt.AlignCenter)

    def draw_graph(self, graph, query: str, pen=None, name: str = None):
        "Draw graph based on the given query."
        results = self.run_query(query, False)
        index = list(range(1, 13))
        values = [0 for i in range(1, 13)]
        for record in results:
            values[int(record[0]) - 1] = float(record[1])
            # index.append(int(record[0]))
            # values.append(float(record[1]))

        for i in range(1, 13):
            if i not in index:
                index.append(i)
                values.append(0)

        if pen:
            graph.plot(index, values, pen=pen, name=name)
        else:
            graph.plot(index, values, name=name)

    def refresh(self):
        "Refresh displayed data."
        self.balance_sheet(refresh=True)
        self.create_transaction_history()
        self.draw_ie_chart()
