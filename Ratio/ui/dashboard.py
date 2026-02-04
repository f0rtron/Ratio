from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, 
                             QPushButton, QStackedWidget, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont

from ui.journal import JournalPage
from ui.ledger import LedgerPage
from ui.reports import ReportsPage
from ui.stats import StatsPage

# --- HELPER: Live Table ---
class SimpleTablePage(QWidget):
    def __init__(self, title, data_loader_func):
        super().__init__()
        self.loader = data_loader_func
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ADB5; margin: 10px;")
        layout.addWidget(lbl)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Account", "Amount"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
    def refresh(self):
        data = self.loader()
        self.table.setRowCount(len(data))
        for i, (name, amount) in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(f"{amount:,.2f}"))

class DashboardWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Ratio")
        self.resize(1280, 850)
        
        # Styles
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QLabel { color: white; }
            QTableWidget { background-color: #1e1e1e; color: white; gridline-color: #333; border: none; }
            QHeaderView::section { background-color: #333; color: white; padding: 5px; }
        """)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QHBoxLayout(main_widget)
        self.layout.setContentsMargins(0,0,0,0)

        # --- FIX: CREATE FAB FIRST (Before setup_content calls switch_page) ---
        self.fab = QPushButton("+", self)
        self.fab.setFixedSize(60, 60)
        self.fab.setStyleSheet("""
            QPushButton {
                background-color: #00ADB5; 
                color: white; 
                font-size: 30px; 
                border-radius: 30px;
                font-weight: bold;
                padding-bottom: 5px;
            }
            QPushButton:hover { background-color: #00D1DB; }
            QPushButton:pressed { background-color: #008C94; }
        """)
        # Add Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.fab.setGraphicsEffect(shadow)
        
        self.fab.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fab.clicked.connect(self.open_journal)
        
        # --- NOW SETUP UI ---
        self.setup_sidebar()
        self.setup_content() # This triggers switch_page(0), which now finds self.fab safely

    def setup_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #1e1e1e;")
        vbox = QVBoxLayout(sidebar)
        vbox.setSpacing(5)
        
        logo = QLabel("RATIO")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 32px; font-weight: bold; color: #00ADB5; margin-top: 20px; margin-bottom: 20px;")
        vbox.addWidget(logo)
        
        self.btns = []
        # REMOVED "Journal Entry" from this list (It's hidden in FAB)
        self.labels = ["Dashboard", "General Ledger", "Trial Balance", "Income Statement", "Balance Sheet", "Reports & Export"]
        
        for i, text in enumerate(self.labels):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { background: none; color: #AAA; border: none; padding: 15px; text-align: left; font-size: 15px; }
                QPushButton:checked { color: white; font-weight: bold; border-left: 4px solid #00ADB5; background-color: #252525; }
                QPushButton:hover { color: white; background-color: #252525; }
            """)
            btn.clicked.connect(lambda _, idx=i: self.switch_page(idx))
            self.btns.append(btn)
            vbox.addWidget(btn)
            
        vbox.addStretch()
        self.layout.addWidget(sidebar)

    def setup_content(self):
        self.stack = QStackedWidget()
        
        self.stats_page = StatsPage(self.db) 
        self.ledger_page = LedgerPage(self.db)
        self.tb_page = SimpleTablePage("Trial Balance", self.get_tb_data)
        self.is_page = SimpleTablePage("Income Statement", self.get_is_data)
        self.bs_page = SimpleTablePage("Balance Sheet", self.get_bs_data)
        self.reports_page = ReportsPage(self.db)
        
        # Hidden Journal Page (Only accessible via FAB)
        self.journal_page = JournalPage(self.db)
        
        # --- STACK ORDER ---
        # 0: Dashboard
        # 1: Ledger
        # 2: TB
        # 3: IS
        # 4: BS
        # 5: Reports
        # 6: Journal (Hidden Index)
        
        self.stack.addWidget(self.stats_page)   
        self.stack.addWidget(self.ledger_page)  
        self.stack.addWidget(self.tb_page)      
        self.stack.addWidget(self.is_page)      
        self.stack.addWidget(self.bs_page)      
        self.stack.addWidget(self.reports_page) 
        self.stack.addWidget(self.journal_page)
        
        self.layout.addWidget(self.stack)
        self.switch_page(0)

    def switch_page(self, index):
        # Uncheck all buttons
        for btn in self.btns: btn.setChecked(False)
        
        # Check specific button if in range (Journal has no button)
        if index < len(self.btns):
            self.btns[index].setChecked(True)
            self.fab.show() # Show FAB on standard pages
        else:
            self.fab.hide() # Hide FAB when ON the Journal page
            
        self.stack.setCurrentIndex(index)
        
        # Auto-Refresh
        if index == 0: self.stats_page.refresh()
        if index == 1: self.ledger_page.refresh()
        if index == 2: self.tb_page.refresh()
        if index == 3: self.is_page.refresh()
        if index == 4: self.bs_page.refresh()

    def open_journal(self):
        # Index 6 is the Journal Page
        self.stack.setCurrentIndex(6)
        # Uncheck sidebar buttons visually
        for btn in self.btns: btn.setChecked(False)
        self.fab.hide()

    def resizeEvent(self, event):
        # Keep FAB in bottom right
        fab_w, fab_h = 60, 60
        margin = 30
        self.fab.move(self.width() - fab_w - margin, self.height() - fab_h - margin)
        super().resizeEvent(event)

    # --- DATA LOADERS ---
    def get_tb_data(self):
        raw = self.db.get_account_balances()
        return [(n, i['balance']) for n, i in raw.items()]

    def get_is_data(self):
        raw = self.db.get_account_balances()
        data = []
        net = 0
        for name, info in raw.items():
            if info['type'] in ['Revenue', 'Expense']:
                val = info['balance']
                if info['type'] == 'Expense': net -= val
                else: net += val
                data.append((name, val))
        data.append(("NET INCOME", net))
        return data

    def get_bs_data(self):
        raw = self.db.get_account_balances()
        net_income = self.db.get_net_income()
        data = []
        equity_total = 0
        for name, info in raw.items():
            if info['type'] in ['Asset', 'Liability']:
                data.append((name, info['balance']))
            elif info['type'] == 'Equity':
                equity_total += info['balance']
                data.append((name, info['balance']))
        data.append(("Net Income (Retained)", net_income))
        return data