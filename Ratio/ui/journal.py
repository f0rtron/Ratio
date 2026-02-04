from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, 
                             QComboBox, QPushButton, QLabel, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

class JournalPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        
        # Main Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)
        self.setLayout(self.layout)
        
        # --- TITLE ---
        title = QLabel("New Journal Entry")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00ADB5;")
        self.layout.addWidget(title)
        
        # --- SECTION 1: DETAILS (Date & Description) ---
        details_frame = QFrame()
        details_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 8px; padding: 20px;")
        df_layout = QGridLayout(details_frame)
        
        self.date_input = QLineEdit()
        self.date_input.setText(QDate.currentDate().toString("yyyy-MM-dd"))
        self.date_input.setPlaceholderText("YYYY-MM-DD")
        
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description (e.g. Purchase of Equipment)")
        
        df_layout.addWidget(QLabel("Date:"), 0, 0)
        df_layout.addWidget(self.date_input, 0, 1)
        df_layout.addWidget(QLabel("Description:"), 1, 0)
        df_layout.addWidget(self.desc_input, 1, 1)
        
        self.layout.addWidget(details_frame)
        
        # --- SECTION 2: THE TRANSACTION (From -> To) ---
        trans_frame = QFrame()
        trans_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 8px; padding: 30px;")
        tf_layout = QHBoxLayout(trans_frame)
        
        # Left: CREDIT SIDE (Source)
        self.cr_group = self.create_account_group("FROM (Credit)", "Liability")
        
        # Center: ARROW & AMOUNT
        center_layout = QVBoxLayout()
        
        arrow = QLabel("➜")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow.setStyleSheet("font-size: 30px; color: #555; margin: 10px;")
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.amount_input.setStyleSheet("""
            QLineEdit {
                font-size: 28px; font-weight: bold; color: #00ADB5;
                background-color: #121212; border: 2px solid #333; border-radius: 8px; padding: 10px;
            }
            QLineEdit:focus { border: 2px solid #00ADB5; }
        """)
        
        center_layout.addStretch()
        center_layout.addWidget(QLabel("Amount"))
        center_layout.addWidget(self.amount_input)
        center_layout.addWidget(arrow)
        center_layout.addStretch()
        
        # Right: DEBIT SIDE (Destination)
        self.dr_group = self.create_account_group("TO (Debit)", "Asset")
        
        tf_layout.addLayout(self.cr_group['layout'])
        tf_layout.addLayout(center_layout)
        tf_layout.addLayout(self.dr_group['layout'])
        
        self.layout.addWidget(trans_frame)
        
        # --- SECTION 3: ACTIONS ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.post_btn = QPushButton("POST TRANSACTION")
        self.post_btn.setFixedSize(200, 50)
        self.post_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.post_btn.clicked.connect(self.post_transaction)
        self.post_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ADB5; color: white; font-weight: bold; font-size: 16px; border-radius: 5px;
            }
            QPushButton:hover { background-color: #00D1DB; }
        """)
        
        btn_layout.addWidget(self.post_btn)
        self.layout.addLayout(btn_layout)
        self.layout.addStretch()

    def create_account_group(self, title, default_type):
        layout = QVBoxLayout()
        
        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: bold; color: #888; font-size: 14px; margin-bottom: 10px;")
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Account Name")
        name_input.setStyleSheet("padding: 10px; background-color: #2b2b2b; border: none; color: white;")
        
        type_combo = QComboBox()
        type_combo.addItems(["Asset", "Liability", "Equity", "Revenue", "Expense"])
        type_combo.setCurrentText(default_type)
        type_combo.setStyleSheet("padding: 8px; background-color: #2b2b2b; color: white; border: none;")
        
        layout.addWidget(lbl)
        layout.addWidget(name_input)
        layout.addWidget(type_combo)
        layout.addStretch()
        
        return {'layout': layout, 'name': name_input, 'type': type_combo}

    def post_transaction(self):
        # 1. Validation
        try:
            amt = float(self.amount_input.text())
            if amt <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter a valid positive amount.")
            return
            
        desc = self.desc_input.text().strip()
        dr_name = self.dr_group['name'].text().strip()
        cr_name = self.cr_group['name'].text().strip()
        
        if not desc or not dr_name or not cr_name:
            QMessageBox.warning(self, "Error", "Please fill in all fields (Desc, From, To).")
            return

        # 2. Logic (Mobile Style: Auto-Create 2 Lines)
        lines = [
            {
                "account_name": dr_name,
                "account_type": self.dr_group['type'].currentText(),
                "debit": amt,
                "credit": 0.0
            },
            {
                "account_name": cr_name,
                "account_type": self.cr_group['type'].currentText(),
                "debit": 0.0,
                "credit": amt
            }
        ]

        # 3. Save
        try:
            self.db.add_transaction(self.date_input.text(), desc, lines)
            QMessageBox.information(self, "Success", "Transaction Posted Successfully!")
            
            # Clear Inputs
            self.amount_input.clear()
            self.desc_input.clear()
            self.dr_group['name'].clear()
            self.cr_group['name'].clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))