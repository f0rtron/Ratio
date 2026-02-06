from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
                             QPushButton, QStackedWidget, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGraphicsDropShadowEffect, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

# Imports
from ui.journal import JournalPage
from ui.ledger import LedgerPage
from ui.general_journal import GeneralJournalPage 
from ui.reports import ReportsPage
from ui.stats import StatsPage

class SimpleTablePage(QWidget):
    def __init__(self, title, headers, data_loader_func):
        super().__init__()
        self.loader = data_loader_func
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ADB5; margin: 10px;")
        layout.addWidget(lbl)
        
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("alternate-background-color: #252525;")
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
    def refresh(self):
        data = self.loader()
        self.table.setRowCount(len(data))
        for r, row_data in enumerate(data):
            for c, item in enumerate(row_data):
                if isinstance(item, (float, int)) and c > 0:
                    val = float(item)
                    if val < 0:
                        val_str = f"({abs(val):,.2f})"
                        table_item = QTableWidgetItem(val_str)
                        table_item.setForeground(QColor("#FF5555"))
                    else:
                        val_str = f"{val:,.2f}"
                        table_item = QTableWidgetItem(val_str)
                        table_item.setForeground(QColor("white"))
                    self.table.setItem(r, c, table_item)
                else:
                    self.table.setItem(r, c, QTableWidgetItem(str(item)))

class DashboardWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Ratio - The Art of Accounting")
        self.resize(1380, 850)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QLabel { color: white; }
            QTableWidget { background-color: #1e1e1e; color: white; gridline-color: #333; border: none; }
            QHeaderView::section { background-color: #333; color: white; padding: 5px; font-weight: bold; }
        """)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QHBoxLayout(main_widget)
        self.layout.setContentsMargins(0,0,0,0)

        # FAB Setup
        self.fab = QPushButton("+", self)
        self.fab.setFixedSize(60, 60)
        self.fab.setStyleSheet("""
            QPushButton {
                background-color: #00ADB5; color: white; font-size: 30px; 
                border-radius: 30px; font-weight: bold; padding-bottom: 5px;
            }
            QPushButton:hover { background-color: #00D1DB; }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.fab.setGraphicsEffect(shadow)
        self.fab.clicked.connect(self.open_new_entry)
        
        self.setup_sidebar()
        self.setup_content()

    def setup_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #1e1e1e;")
        vbox = QVBoxLayout(sidebar)
        vbox.setSpacing(5)
        
        logo = QLabel("RATIO")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 32px; font-weight: bold; color: #00ADB5; margin: 20px;")
        vbox.addWidget(logo)
        
        self.btns = []
        self.labels = [
            "Dashboard", "General Journal", "General Ledger", 
            "Trial Balance", "Income Statement", "Balance Sheet", "Reports"
        ]
        
        for i, text in enumerate(self.labels):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { background: none; color: #AAA; border: none; padding: 15px; text-align: left; font-size: 15px; }
                QPushButton:checked { color: white; font-weight: bold; border-left: 4px solid #00ADB5; background-color: #252525; }
                QPushButton:hover { color: white; background-color: #252525; }
            """)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            self.btns.append(btn)
            vbox.addWidget(btn)
            
        vbox.addStretch()
        
        # --- NEW: RESET BUTTON ---
        btn_reset = QPushButton("Reset All Data")
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.setStyleSheet("""
            QPushButton { 
                background-color: transparent; 
                color: #FF5555; 
                border: 1px solid #FF5555; 
                border-radius: 5px; 
                padding: 10px; 
                margin: 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #FF5555; color: white; }
        """)
        btn_reset.clicked.connect(self.reset_data)
        vbox.addWidget(btn_reset)
        
        self.layout.addWidget(sidebar)

    def setup_content(self):
        self.stack = QStackedWidget()
        
        self.stats_page = StatsPage(self.db) 
        self.journal_view_page = GeneralJournalPage(self.db) 
        self.ledger_page = LedgerPage(self.db)
        self.tb_page = SimpleTablePage("Trial Balance", ["Account", "Debit Total", "Credit Total"], self.get_tb_data)
        self.is_page = SimpleTablePage("Income Statement", ["Line Item", "Amount"], self.get_is_data)
        self.bs_page = SimpleTablePage("Balance Sheet", ["Line Item", "Amount"], self.get_bs_data)
        self.reports_page = ReportsPage(self.db)
        self.journal_entry_page = JournalPage(self.db)
        
        # Connect Dashboard Signals
        self.stats_page.go_to_income_stmt.connect(lambda: self.switch_page(4))
        self.stats_page.go_to_ledger.connect(lambda: self.switch_page(2))
        
        self.stack.addWidget(self.stats_page)        # 0
        self.stack.addWidget(self.journal_view_page) # 1
        self.stack.addWidget(self.ledger_page)       # 2
        self.stack.addWidget(self.tb_page)           # 3
        self.stack.addWidget(self.is_page)           # 4
        self.stack.addWidget(self.bs_page)           # 5
        self.stack.addWidget(self.reports_page)      # 6
        self.stack.addWidget(self.journal_entry_page)# 7
        
        self.layout.addWidget(self.stack)
        self.switch_page(0)

    def switch_page(self, index):
        for btn in self.btns: btn.setChecked(False)
        
        if index < len(self.btns):
            self.btns[index].setChecked(True)
            self.fab.show()
        else:
            self.fab.hide()
            
        self.stack.setCurrentIndex(index)
        
        if index == 0: self.stats_page.refresh()
        if index == 1: self.journal_view_page.refresh()
        if index == 2: self.ledger_page.refresh()
        if index == 3: self.tb_page.refresh()
        if index == 4: self.is_page.refresh()
        if index == 5: self.bs_page.refresh()

    def open_new_entry(self):
        self.switch_page(7)
        self.journal_entry_page.reset_form()

    def edit_transaction(self, trans_id):
        self.switch_page(7)
        self.journal_entry_page.load_transaction(trans_id)

    # --- RESET DATA LOGIC ---
    def reset_data(self):
        confirm = QMessageBox.question(self, "Danger Zone", 
                                     "Are you sure you want to delete ALL transactions?\n\nThis cannot be undone. The app will return to a clean state.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.db.clear_all_data()
                QMessageBox.information(self, "Success", "Database has been wiped clean.")
                # Return to dashboard and refresh
                self.switch_page(0) 
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def resizeEvent(self, event):
        self.fab.move(self.width() - 90, self.height() - 90)
        super().resizeEvent(event)

    # --- DATA LOADERS ---
    def get_tb_data(self):
        raw = self.db.get_account_balances()
        data = []
        tot_dr = 0; tot_cr = 0
        for name in sorted(raw.keys()):
            info = raw[name]
            dr = info['debit_total']; cr = info['credit_total']
            data.append((name, dr, cr))
            tot_dr += dr; tot_cr += cr
        data.append(("TOTAL", tot_dr, tot_cr))
        return data

    def get_is_data(self):
        raw = self.db.get_account_balances()
        data = []
        rev_total = 0; exp_total = 0
        
        data.append(("--- REVENUE ---", ""))
        for name, info in raw.items():
            if info['type'] == 'Revenue':
                data.append((name, info['net_balance']))
                rev_total += info['net_balance']
        data.append(("Total Revenue", rev_total))
        
        data.append(("--- EXPENSES ---", ""))
        for name, info in raw.items():
            if info['type'] == 'Expense':
                data.append((name, info['net_balance']))
                exp_total += info['net_balance']
        data.append(("Total Expenses", exp_total))
        
        net_income = float(rev_total - exp_total)
        data.append(("", ""))
        data.append(("NET INCOME", net_income))
        return data

    def get_bs_data(self):
        raw = self.db.get_account_balances()
        net_income = self.db.get_net_income()
        data = []
        asset_total = 0; liab_total = 0; equity_total = 0
        
        data.append(("--- ASSETS ---", ""))
        for name, info in raw.items():
            if info['type'] == 'Asset':
                data.append((name, info['net_balance']))
                asset_total += info['net_balance']
        data.append(("TOTAL ASSETS", asset_total))
        data.append(("", ""))

        data.append(("--- LIABILITIES ---", ""))
        for name, info in raw.items():
            if info['type'] == 'Liability':
                data.append((name, info['net_balance']))
                liab_total += info['net_balance']
        
        data.append(("--- EQUITY ---", ""))
        for name, info in raw.items():
            if info['type'] == 'Equity':
                data.append((name, info['net_balance']))
                equity_total += info['net_balance']
        
        data.append(("Retained Earnings", net_income))
        equity_total += net_income
        
        data.append(("TOTAL LIAB. & EQUITY", liab_total + equity_total))
        return data