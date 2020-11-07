"Contains code related to the button prompt."
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class BtnPrmpt(QDialog):
    "Creates a prompt that displays a particular message, with buttons to provide a response."

    def __init__(self, title: str, dlgType: str, msg: str, *args, **kwargs):
        super(BtnPrmpt, self).__init__(*args, **kwargs)

        self.setWindowTitle(title)
        self.setMinimumHeight(100)
        self.setMinimumWidth(250)

        self.layout = QVBoxLayout()

        self.message = QLabel(msg)
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setWordWrap(True)
        self.layout.addWidget(self.message)

        if dlgType == 'Y / N':
            self.q_btn = QDialogButtonBox.Yes | QDialogButtonBox.No
        elif dlgType == 'Single':
            self.q_btn = QDialogButtonBox.Ok
        else:
            self.q_btn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.button_box = QDialogButtonBox(self.q_btn)
        self.button_box.setCenterButtons(True)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

        self.setMinimumSize(self.layout.sizeHint())
