from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QLabel, QHeaderView, QAbstractItemView, QMenu, QMessageBox)
from PyQt6.QtGui import QColor, QAction
from PyQt6.QtCore import Qt

class GeneralJournalPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        lbl = QLabel("General Journal (Book of Original Entry)")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ADB5; margin: 10px;")
        layout.addWidget(lbl)
        
        # Table
        self.table = QTableWidget()
        # Added hidden "ID" column at index 5
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Transaction / Description", "Account", "Debit", "Credit", "ID"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Styling: Widen the Description column
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Hide ID Column
        self.table.setColumnHidden(5, True)
        
        # Read-Only & Selection Mode
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # Context Menu (Right-Click)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        
        # Double Click to Edit
        self.table.doubleClicked.connect(self.on_double_click)
        
        layout.addWidget(self.table)

    def refresh(self):
        # Fetch all transactions chronologically
        rows = self.db.get_ledger("All") 
        self.table.setRowCount(len(rows))
        
        for i, row in enumerate(rows):
            # row: (tid, date, name, type, desc, dr, cr, run_bal)
            tid, date, name, _, desc, dr, cr, _ = row
            
            self.table.setItem(i, 0, QTableWidgetItem(date))
            self.table.setItem(i, 1, QTableWidgetItem(desc))
            self.table.setItem(i, 2, QTableWidgetItem(name))
            
            # Debit Formatting
            dr_item = QTableWidgetItem(f"{dr:,.2f}" if dr > 0 else "")
            if dr > 0: dr_item.setForeground(QColor("#00ADB5")) # Teal
            self.table.setItem(i, 3, dr_item)
            
            # Credit Formatting
            cr_item = QTableWidgetItem(f"{cr:,.2f}" if cr > 0 else "")
            if cr > 0: cr_item.setForeground(QColor("#FF5555")) # Red
            self.table.setItem(i, 4, cr_item)
            
            # Hidden ID
            self.table.setItem(i, 5, QTableWidgetItem(str(tid)))

    def on_double_click(self, index):
        row = index.row()
        trans_id = self.table.item(row, 5).text()
        self.trigger_edit(trans_id)

    def open_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row == -1: return
        
        trans_id = self.table.item(row, 5).text()
        
        menu = QMenu()
        edit_action = QAction("Edit Transaction", self)
        delete_action = QAction("Void / Delete", self)
        
        menu.addAction(edit_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        
        action = menu.exec(self.table.viewport().mapToGlobal(position))
        
        if action == edit_action:
            self.trigger_edit(trans_id)
        elif action == delete_action:
            self.delete_transaction(trans_id)

    def trigger_edit(self, trans_id):
        # Call Main Window Switcher
        main_window = self.window()
        if hasattr(main_window, 'edit_transaction'):
            main_window.edit_transaction(trans_id)

    def delete_transaction(self, trans_id):
        confirm = QMessageBox.question(self, "Confirm Void", 
                                     "Are you sure you want to void this transaction?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_transaction(trans_id)
            self.refresh()