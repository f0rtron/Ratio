import sys
import os
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt, QTimer
from database import DatabaseHandler
from ui.dashboard import DashboardWindow
from seed_gui import SetupWindow

def main():
    app = QApplication(sys.argv)
    
    # CRITICAL FIX: Prevents app from closing when SetupWindow is closed, 
    # ensuring the transition to DashboardWindow happens smoothly.
    app.setQuitOnLastWindowClosed(False)
    
    # Global references to keep windows alive
    windows = {}

    def launch_dashboard():
        # 1. Init Database
        db = DatabaseHandler()
        
        # 2. Show Ratio Splash
        pixmap = QPixmap(400, 300)
        pixmap.fill(QColor("#1e1e1e"))
        splash = QSplashScreen(pixmap)
        splash.showMessage("RATIO\nPowered by 1CA", Qt.AlignmentFlag.AlignCenter, QColor("#00ADB5"))
        splash.show()
        
        # 3. Create Dashboard (Hidden initially)
        dashboard = DashboardWindow(db)
        windows['dashboard'] = dashboard
        
        def show_main():
            # Close Setup if it exists
            if 'setup' in windows:
                windows['setup'].close()
                
            splash.finish(dashboard)
            dashboard.show()
            
            # Now we can allow the app to quit if Dashboard is closed
            app.setQuitOnLastWindowClosed(True)
            
        QTimer.singleShot(2000, show_main)

    # --- Logic: Check for DB ---
    db_file = "ratio.db"
    
    if not os.path.exists(db_file):
        # 1. No DB found? Show Setup
        setup = SetupWindow()
        windows['setup'] = setup
        setup.setup_complete.connect(launch_dashboard)
        setup.show()
    else:
        # 2. DB exists? Go straight to Dashboard
        launch_dashboard()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()