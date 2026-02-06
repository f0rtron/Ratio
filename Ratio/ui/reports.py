from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, 
                             QFrame, QDateEdit, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QDate
from utils.pdf_export import PDFExporter

class ReportsPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.exporter = PDFExporter(db)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title = QLabel("Financial Reports")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00ADB5;")
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # --- REPORT CONFIGURATION CARD ---
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e; 
                border-radius: 10px; 
                padding: 30px;
                border: 1px solid #333;
            }
        """)
        card_layout = QVBoxLayout(card)
        
        # Date Selection
        date_layout = QGridLayout()
        date_layout.setSpacing(15)
        
        lbl_start = QLabel("Period Start:")
        lbl_start.setStyleSheet("color: white; font-weight: bold;")
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setStyleSheet("padding: 8px; color: white; background: #333; border: 1px solid #555;")
        
        lbl_end = QLabel("Period End:")
        lbl_end.setStyleSheet("color: white; font-weight: bold;")
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setStyleSheet("padding: 8px; color: white; background: #333; border: 1px solid #555;")
        
        date_layout.addWidget(lbl_start, 0, 0)
        date_layout.addWidget(self.start_date, 0, 1)
        date_layout.addWidget(lbl_end, 1, 0)
        date_layout.addWidget(self.end_date, 1, 1)
        
        card_layout.addLayout(date_layout)
        card_layout.addSpacing(30)
        
        # Info
        info = QLabel("Generate Financial Statements (PDF)")
        info.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        
        sub_info = QLabel("Includes: Income Statement (P&L) and Balance Sheet.")
        sub_info.setStyleSheet("color: #AAA; font-size: 14px; margin-bottom: 20px;")
        
        # --- FIXED BUTTON ---
        self.export_btn = QPushButton("DOWNLOAD REPORT PDF") # Removed Emoji to be safe
        self.export_btn.setFixedHeight(50)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_all)
        self.export_btn.setStyleSheet("""
            QPushButton { 
                background-color: #00ADB5; 
                color: #FFFFFF; 
                border-radius: 5px; 
                font-weight: bold; 
                font-size: 14px;
                border: none;
                padding: 10px;
            }
            QPushButton:hover { background-color: #00D1DB; }
            QPushButton:pressed { background-color: #008C94; }
        """)
        
        card_layout.addWidget(info)
        card_layout.addWidget(sub_info)
        card_layout.addWidget(self.export_btn)
        
        layout.addWidget(card)
        layout.addStretch()

    def export_all(self):
        s_date = self.start_date.date().toString("yyyy-MM-dd")
        e_date = self.end_date.date().toString("yyyy-MM-dd")
        
        try:
            filename = self.exporter.generate_full_report(s_date, e_date)
            QMessageBox.information(self, "Success", f"Report generated successfully:\n\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to generate PDF:\n{str(e)}")