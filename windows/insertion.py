"Contains code related to the insertion window."
import datetime as dt
import sqlite3 as sql

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (QCalendarWidget, QComboBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTextEdit, QVBoxLayout,
                             QWidget)

from helpers import center_window
from .btn_prompt import BtnPrmpt


class DataInsertion(QWidget):
    "Form for the insertion of data into the dtbse."

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Data Insertion')
        self.main_window = parent

        self.setMinimumHeight(self.main_window.minimumHeight())
        self.setMinimumWidth(self.main_window.minimumWidth())
        self.setMaximumHeight(round(self.main_window.maximumHeight()))
        self.setMaximumWidth(round(self.main_window.maximumWidth()))

        self.wrkng_drctry = self.main_window.wrkng_drctry

        self.main_layout = QVBoxLayout()

        self.data_layout = QVBoxLayout()
        self.data_layout.setAlignment(Qt.AlignCenter)

        self.date = QCalendarWidget()
        self.date.setToolTip('Select transaction date.')
        self.date.setWindowTitle('Date')
        self.date.setFirstDayOfWeek(Qt.DayOfWeek(1))
        self.date.setMaximumDate(dt.date.today())
        self.date.setGridVisible(True)
        self.data_layout.addWidget(self.date)

        self.details = QTextEdit('Enter transaction description...')
        self.details.setToolTip('Transaction description')
        self.data_layout.addWidget(self.details)

        self.other_party = QLineEdit('Enter other party...')
        self.other_party.setToolTip('Other party')
        self.data_layout.addWidget(self.other_party)

        self.layout1 = QHBoxLayout()

        self.transaction_type = QComboBox()
        self.transaction_type.addItems(
            ("Payment Received", "Paid", "Loan Return", "Loan", "Borrow From", "Payback"))
        self.transaction_type.setToolTip('Transaction type')
        self.layout1.addWidget(self.transaction_type)

        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator())
        self.value.setToolTip('Value')
        self.layout1.addWidget(self.value)

        self.data_layout.addLayout(self.layout1)
        self.main_layout.addLayout(self.data_layout)

        self.main_layout.addWidget(QLabel())

        self.save_layout = QHBoxLayout()
        self.save_layout.setAlignment(Qt.AlignBottom)
        self.save_layout.setAlignment(Qt.AlignHCenter)

        self.close_btn = QPushButton('Close')
        self.close_btn.setToolTip('Close the window without saving')
        self.close_btn.clicked.connect(self.close)
        self.save_layout.addWidget(self.close_btn)

        self.save_and_close = QPushButton('Save and Close')
        self.save_and_close.setToolTip('Save data and close window')
        self.save_and_close.clicked.connect(self.save_close)
        self.save_layout.addWidget(self.save_and_close)

        self.save_and_continue = QPushButton('Save and Continue')
        self.save_and_continue.setToolTip('Save data and continue')
        self.save_and_continue.clicked.connect(self.save_continue)
        self.save_layout.addWidget(self.save_and_continue)

        self.main_layout.addLayout(self.save_layout)

        self.setLayout(self.main_layout)

        self.setMinimumSize(self.main_layout.sizeHint())
        center_window(self)

    def save_close(self):
        "Save user input and close the window."
        returns = self.collect_data()
        message = BtnPrmpt(*returns)
        message.exec_()
        self.close()

    def save_continue(self):
        "Save the user input and reset the window."
        returns = self.collect_data()
        message = BtnPrmpt(*returns)
        message.exec_()
        self.date.setSelectedDate(dt.date.today())
        self.details.setText('Enter transaction description...')
        self.other_party.setText('Enter other party...')
        self.value.setText('')

    def collect_data(self):
        "Collects data from window and attempts to insert it."
        try:
            results = []
            date = self.date.selectedDate()
            results.append(dt.date(date.year(), date.month(), date.day()))
            results.append(self.details.toPlainText())
            results.append(self.transaction_type.currentText())
            results.append(self.other_party.text())
            results.append(round(float(self.value.text()), 2))

            with sql.connect('finances.db') as dtbse:
                dtbse.execute(
                    'insert into finance (Date, Activity, "Transaction Type", "Other Party", '
                    'Value) values(?, ?, ?, ?, ?)',
                    results
                )
                dtbse.commit()

            return ('Success', 'Single', 'Data capture was successful.')
        except Exception as error:
            return (
                'Failure',
                'Single',
                f'Data capture was unsuccessful.\nError message: {error.__str__()}'
            )
