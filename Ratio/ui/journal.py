from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, 
                             QComboBox, QPushButton, QLabel, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

class JournalPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_trans_id = None # Track if we are editing
        
        # Main Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)
        self.setLayout(self.layout)
        
        # --- TITLE ---
        self.title_lbl = QLabel("New Journal Entry")
        self.title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #00ADB5;")
        self.layout.addWidget(self.title_lbl)
        
        # --- SECTION 1: DETAILS ---
        details_frame = QFrame()
        details_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 8px; padding: 20px;")
        df_layout = QGridLayout(details_frame)
        
        self.date_input = QLineEdit()
        self.date_input.setText(QDate.currentDate().toString("yyyy-MM-dd"))
        self.date_input.setPlaceholderText("YYYY-MM-DD")
        self.date_input.setStyleSheet("padding: 8px; background: #333; color: white; border: none;")
        
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description (e.g. Purchase of Equipment)")
        self.desc_input.setStyleSheet("padding: 8px; background: #333; color: white; border: none;")
        
        df_layout.addWidget(QLabel("Date:"), 0, 0)
        df_layout.addWidget(self.date_input, 0, 1)
        df_layout.addWidget(QLabel("Description:"), 1, 0)
        df_layout.addWidget(self.desc_input, 1, 1)
        
        self.layout.addWidget(details_frame)
        
        # --- SECTION 2: THE TRANSACTION ---
        trans_frame = QFrame()
        trans_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 8px; padding: 30px;")
        tf_layout = QHBoxLayout(trans_frame)
        
        # Left: CREDIT SIDE
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
        
        # Right: DEBIT SIDE
        self.dr_group = self.create_account_group("TO (Debit)", "Asset")
        
        tf_layout.addLayout(self.cr_group['layout'])
        tf_layout.addLayout(center_layout)
        tf_layout.addLayout(self.dr_group['layout'])
        
        self.layout.addWidget(trans_frame)
        
        # --- SECTION 3: ACTIONS ---
        btn_layout = QHBoxLayout()
        
        # Delete Button (Hidden by default)
        self.btn_delete = QPushButton("DELETE TRANSACTION")
        self.btn_delete.setFixedSize(200, 50)
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.clicked.connect(self.delete_current_transaction)
        self.btn_delete.hide()
        self.btn_delete.setStyleSheet("""
            QPushButton { background-color: #FF5555; color: white; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #FF7777; }
        """)
        
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        
        self.post_btn = QPushButton("POST TRANSACTION")
        self.post_btn.setFixedSize(200, 50)
        self.post_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.post_btn.clicked.connect(self.post_transaction)
        self.post_btn.setStyleSheet("""
            QPushButton { background-color: #00ADB5; color: white; font-weight: bold; font-size: 16px; border-radius: 5px; }
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

    # --- MODE SWITCHING ---
    
    def load_transaction(self, trans_id):
        """Called by other pages to Edit a transaction"""
        self.current_trans_id = trans_id
        
        # Fetch Data
        # We need a new DB function to get Header + Splits nicely
        # For now, we will hack it using existing fetchers:
        details = self.db.get_ledger("All") # Inefficient but works with existing code
        # Filter manually (Ideally create db.get_transaction(id))
        
        # Let's use the splits fetcher we made for the dialog
        splits = self.db.get_transaction_details(trans_id)
        
        # We also need the date/desc which is in the transactions table
        # Add this helper to database.py if missing:
        # cursor.execute("SELECT date, description FROM transactions WHERE id=?", (id,))
        
        # Assuming you add that, or we assume the caller passed the data.
        # To keep it simple for you, let's assume we implement `db.get_full_transaction(id)`
        
        header, lines = self.db.get_full_transaction(trans_id) 
        
        # Populate UI
        self.title_lbl.setText("Edit Transaction")
        self.post_btn.setText("UPDATE TRANSACTION")
        self.btn_delete.show()
        
        self.date_input.setText(header['date'])
        self.desc_input.setText(header['description'])
        
        # Fill Splits (Logic assumes 2 lines for simple UI)
        # Identify Dr and Cr lines
        dr_line = next((l for l in lines if l['debit'] > 0), None)
        cr_line = next((l for l in lines if l['credit'] > 0), None)
        
        if dr_line:
            self.dr_group['name'].setText(dr_line['name'])
            self.dr_group['type'].setCurrentText(dr_line['type'])
            self.amount_input.setText(str(dr_line['debit']))
            
        if cr_line:
            self.cr_group['name'].setText(cr_line['name'])
            self.cr_group['type'].setCurrentText(cr_line['type'])

    def reset_form(self):
        """Resets to 'Create New' mode"""
        self.current_trans_id = None
        self.title_lbl.setText("New Journal Entry")
        self.post_btn.setText("POST TRANSACTION")
        self.btn_delete.hide()
        
        self.date_input.setText(QDate.currentDate().toString("yyyy-MM-dd"))
        self.desc_input.clear()
        self.amount_input.clear()
        self.dr_group['name'].clear()
        self.cr_group['name'].clear()

    # --- ACTIONS ---

    def post_transaction(self):
        try:
            amt = float(self.amount_input.text())
            if amt <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid Amount")
            return
            
        desc = self.desc_input.text().strip()
        
        lines = [
            {
                "account_name": self.dr_group['name'].text().strip(),
                "account_type": self.dr_group['type'].currentText(),
                "debit": amt, "credit": 0.0
            },
            {
                "account_name": self.cr_group['name'].text().strip(),
                "account_type": self.cr_group['type'].currentText(),
                "debit": 0.0, "credit": amt
            }
        ]

        try:
            if self.current_trans_id:
                # UPDATE MODE
                self.db.update_transaction(self.current_trans_id, self.date_input.text(), desc, lines)
                QMessageBox.information(self, "Success", "Transaction Updated!")
                self.reset_form() # Go back to create mode? Or stay? usually reset.
            else:
                # CREATE MODE
                self.db.add_transaction(self.date_input.text(), desc, lines)
                QMessageBox.information(self, "Success", "Transaction Posted!")
                self.reset_form()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def delete_current_transaction(self):
        if not self.current_trans_id: return
        
        confirm = QMessageBox.question(self, "Confirm Delete", "Delete this transaction permanently?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_transaction(self.current_trans_id)
            QMessageBox.information(self, "Deleted", "Transaction removed.")
            self.reset_form()