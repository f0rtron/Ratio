from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QLabel, QHeaderView, QMenu, QMessageBox, 
                             QDialog, QAbstractItemView, QStackedWidget)
from PyQt6.QtGui import QAction, QColor, QFont
from PyQt6.QtCore import Qt

class LedgerPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        
        self.stack = QStackedWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        
        # Page 0: Summary
        self.page_summary = QWidget()
        self.setup_summary_page()
        self.stack.addWidget(self.page_summary)
        
        # Page 1: Details
        self.page_details = QWidget()
        self.setup_details_page()
        self.stack.addWidget(self.page_details)
        
        self.stack.setCurrentIndex(0)

    def setup_summary_page(self):
        layout = QVBoxLayout(self.page_summary)
        
        header = QLabel("General Ledger - Chart of Accounts")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #00ADB5; margin: 10px;")
        layout.addWidget(header)
        
        inst = QLabel("Double-click an account to view transaction history.")
        inst.setStyleSheet("color: #888; margin-bottom: 10px;")
        layout.addWidget(inst)
        
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(4)
        self.summary_table.setHorizontalHeaderLabels(["Account Name", "Type", "Net Balance", "Action"])
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.summary_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.summary_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.setStyleSheet("alternate-background-color: #252525;")
        
        self.summary_table.doubleClicked.connect(self.on_account_selected)
        
        layout.addWidget(self.summary_table)

    def setup_details_page(self):
        layout = QVBoxLayout(self.page_details)
        
        # Top Bar
        top_bar = QHBoxLayout()
        btn_back = QPushButton("← Back to Accounts")
        btn_back.setFixedSize(150, 40)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_back.setStyleSheet("""
            QPushButton { background-color: #333; color: white; border: 1px solid #555; border-radius: 5px; }
            QPushButton:hover { background-color: #444; }
        """)
        
        self.lbl_current_account = QLabel("Account History")
        self.lbl_current_account.setStyleSheet("font-size: 20px; font-weight: bold; color: white; margin-left: 20px;")
        
        top_bar.addWidget(btn_back)
        top_bar.addWidget(self.lbl_current_account)
        top_bar.addStretch()
        layout.addLayout(top_bar)
        
        # Details Table
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(7) 
        self.details_table.setHorizontalHeaderLabels(["Date", "Account", "Description", "Debit", "Credit", "Balance", "ID"])
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.details_table.setColumnHidden(6, True) # Hide ID
        self.details_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.details_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        self.details_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.details_table.customContextMenuRequested.connect(self.open_context_menu)
        
        layout.addWidget(self.details_table)

    def refresh(self):
        if self.stack.currentIndex() == 0:
            self.load_summary_data()
        else:
            acc_name = self.lbl_current_account.text().replace("Ledger: ", "")
            self.load_detail_data(acc_name)

    def load_summary_data(self):
        self.summary_table.setRowCount(0)
        balances = self.db.get_account_balances()
        sorted_accs = sorted(balances.items()) 
        self.summary_table.setRowCount(len(sorted_accs))
        
        for i, (name, info) in enumerate(sorted_accs):
            self.summary_table.setItem(i, 0, QTableWidgetItem(name))
            self.summary_table.setItem(i, 1, QTableWidgetItem(info['type']))
            
            bal = info['net_balance']
            bal_str = f"{bal:,.2f}"
            if bal < 0: bal_str = f"({abs(bal):,.2f})"
            
            item_bal = QTableWidgetItem(bal_str)
            item_bal.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            if bal < 0: item_bal.setForeground(QColor("#FF5555"))
            self.summary_table.setItem(i, 2, item_bal)
            
            btn = QTableWidgetItem("View History ➜")
            btn.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            btn.setForeground(QColor("#888"))
            self.summary_table.setItem(i, 3, btn)

    def on_account_selected(self, index):
        row = index.row()
        acc_name = self.summary_table.item(row, 0).text()
        self.load_detail_data(acc_name)
        self.stack.setCurrentIndex(1)

    def load_detail_data(self, account_name):
        self.lbl_current_account.setText(f"Ledger: {account_name}")
        rows = self.db.get_ledger(account_name) 
        self.details_table.setRowCount(len(rows))
        
        for i, row in enumerate(rows):
            tid, date, name, _, desc, dr, cr, run_bal = row
            
            self.details_table.setItem(i, 0, QTableWidgetItem(str(date)))
            self.details_table.setItem(i, 1, QTableWidgetItem(str(name)))
            self.details_table.setItem(i, 2, QTableWidgetItem(str(desc)))
            self.details_table.setItem(i, 3, QTableWidgetItem(f"{dr:,.2f}" if dr > 0 else ""))
            self.details_table.setItem(i, 4, QTableWidgetItem(f"{cr:,.2f}" if cr > 0 else ""))
            
            bal_str = f"{run_bal:,.2f}"
            if run_bal < 0: bal_str = f"({abs(run_bal):,.2f})"
            
            bal_item = QTableWidgetItem(bal_str)
            bal_item.setBackground(QColor("#252525"))
            self.details_table.setItem(i, 5, bal_item)
            self.details_table.setItem(i, 6, QTableWidgetItem(str(tid))) 

    def open_context_menu(self, position):
        row = self.details_table.rowAt(position.y())
        if row == -1: return
        
        trans_id = self.details_table.item(row, 6).text()
        
        menu = QMenu()
        edit_action = QAction("Edit Transaction", self)
        delete_action = QAction("Void / Delete", self)
        
        menu.addAction(edit_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        
        action = menu.exec(self.details_table.viewport().mapToGlobal(position))
        
        if action == edit_action:
            # Call Main Window Switcher
            main_window = self.window()
            if hasattr(main_window, 'edit_transaction'):
                main_window.edit_transaction(trans_id)
                
        elif action == delete_action:
            self.delete_transaction(trans_id)

    def delete_transaction(self, trans_id):
        confirm = QMessageBox.question(self, "Confirm Void", 
                                     "Are you sure you want to void this transaction?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_transaction(trans_id)
            acc_name = self.lbl_current_account.text().replace("Ledger: ", "")
            self.load_detail_data(acc_name)