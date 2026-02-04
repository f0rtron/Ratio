import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt, QTimer
from database import DatabaseHandler
from ui.dashboard import DashboardWindow

def main():
    app = QApplication(sys.argv)
    
    # --- Splash Screen ---
    pixmap = QPixmap(400, 300)
    pixmap.fill(QColor("#1e1e1e"))
    
    splash = QSplashScreen(pixmap)
    splash.showMessage("RATIO\nPowered by 1CA", Qt.AlignmentFlag.AlignCenter, QColor("#00ADB5"))
    splash.show()
    
    # --- Database Init ---
    db = DatabaseHandler()
    
    # --- Main Window ---
    window = DashboardWindow(db)
    
    def load_app():
        splash.finish(window)
        window.show()
        
    QTimer.singleShot(2000, load_app)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()