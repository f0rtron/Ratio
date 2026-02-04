from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QLabel, QHeaderView

class LedgerPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Filter
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All")
        self.filter_combo.currentTextChanged.connect(self.load_data)
        layout.addWidget(QLabel("Filter by Account:"))
        layout.addWidget(self.filter_combo)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Account", "Type", "Desc", "Debit", "Credit"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
    def refresh(self):
        current = self.filter_combo.currentText()
        self.filter_combo.clear()
        self.filter_combo.addItem("All")
        self.filter_combo.addItems(self.db.get_unique_accounts())
        self.filter_combo.setCurrentText(current)
        self.load_data()

    # In ui/ledger.py
    def load_data(self):
        acc = self.filter_combo.currentText()
        rows = self.db.get_ledger(acc) # Now this function exists!
        self.table.setRowCount(len(rows))
        
        for i, row in enumerate(rows):
            # row = (id, trans_id, date, name, type, desc, deb, cred)
            self.table.setItem(i, 0, QTableWidgetItem(row[2])) # Date
            self.table.setItem(i, 1, QTableWidgetItem(row[3])) # Account
            self.table.setItem(i, 2, QTableWidgetItem(row[4])) # Type
            self.table.setItem(i, 3, QTableWidgetItem(row[5])) # Desc
            self.table.setItem(i, 4, QTableWidgetItem(f"{row[6]:.2f}")) # Debit
            self.table.setItem(i, 5, QTableWidgetItem(f"{row[7]:.2f}")) # Credit