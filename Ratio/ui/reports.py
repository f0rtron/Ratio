from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox, 
                             QFrame, QHBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from utils.pdf_export import PDFExporter

class ReportsPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.exporter = PDFExporter(db)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # --- TITLE ---
        title = QLabel("Reports & Export")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00ADB5;")
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # --- EXPORT CARD ---
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 10px;
                padding: 30px;
            }
        """)
        card_layout = QVBoxLayout(card)
        
        info = QLabel("Generate Comprehensive Financial Report")
        info.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        
        sub_info = QLabel("Includes Income Statement, Balance Sheet, and Full General Ledger.")
        sub_info.setStyleSheet("color: #888; font-size: 14px; margin-bottom: 20px;")
        
        self.export_btn = QPushButton("📄   Download PDF Report")
        self.export_btn.setFixedSize(250, 60)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_all)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ADB5; color: white; border-radius: 8px;
                font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #00D1DB; }
        """)
        
        card_layout.addWidget(info)
        card_layout.addWidget(sub_info)
        card_layout.addWidget(self.export_btn)
        
        layout.addWidget(card)
        layout.addStretch()

    def export_all(self):
        try:
            filename = self.exporter.generate_full_report()
            QMessageBox.information(self, "Export Complete", 
                                  f"Report saved successfully as:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")