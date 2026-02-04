from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, 
                             QSizePolicy, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import matplotlib
matplotlib.use('QtAgg') 
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- THEME COLORS ---
COLOR_BG = "#1e1e1e"
COLOR_ACCENT = "#00ADB5"
COLOR_DANGER = "#FF5555"
COLOR_TEXT = "#E0E0E0"
COLOR_SUBTEXT = "#888888"

class KPICard(QFrame):
    """A clean, uniform KPI Card"""
    def __init__(self, title, value, subtext, is_positive=True):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG};
                border-radius: 10px;
                border: 1px solid #333;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(110)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet(f"color: {COLOR_SUBTEXT}; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none;")
        
        color = COLOR_ACCENT if is_positive else COLOR_DANGER
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold; border: none;")
        
        lbl_sub = QLabel(subtext)
        lbl_sub.setStyleSheet(f"color: {COLOR_SUBTEXT}; font-size: 12px; border: none;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)

class StatsPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        
        # --- SCROLL SETUP ---
        # 1. Main Layout for the Page (contains ONLY the scroll area)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 2. The Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background-color: #121212;") # Matches Dashboard bg
        
        # 3. The Content Widget (Holds the actual charts)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(30, 30, 30, 80) # Extra bottom padding for FAB
        self.content_layout.setSpacing(20)
        
        # --- DASHBOARD CONTENT ---
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Financial Overview")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLOR_TEXT};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.content_layout.addLayout(header_layout)
        
        # KPI Row
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(20)
        self.content_layout.addLayout(self.kpi_layout)
        
        # Charts Grid
        self.charts_grid = QGridLayout()
        self.charts_grid.setSpacing(20)
        self.content_layout.addLayout(self.charts_grid)
        
        # Initialize Canvases
        self.trend_canvas = self.create_chart_canvas()
        self.pie_canvas = self.create_chart_canvas()
        self.bar_canvas = self.create_chart_canvas()
        
        # Setup Grid
        self.charts_grid.addWidget(self.trend_canvas, 0, 0, 1, 2)
        self.charts_grid.addWidget(self.pie_canvas, 1, 0)
        self.charts_grid.addWidget(self.bar_canvas, 1, 1)
        self.charts_grid.setRowStretch(0, 3) 
        self.charts_grid.setRowStretch(1, 2)
        
        # Set Minimum Heights so they scroll instead of shrinking
        self.trend_canvas.setMinimumHeight(300)
        self.pie_canvas.setMinimumHeight(300)
        self.bar_canvas.setMinimumHeight(300)

        # --- FINALIZE SCROLL ---
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def create_chart_canvas(self):
        fig = Figure(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor(COLOR_BG)
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet(f"background-color: {COLOR_BG}; border-radius: 10px; border: 1px solid #333;")
        return canvas

    def refresh(self):
        self.update_kpis()
        balances = self.db.get_account_balances()
        
        self.plot_trend_chart()
        self.plot_expense_donut(balances)
        self.plot_net_worth_bar(balances)
        
        self.trend_canvas.draw()
        self.pie_canvas.draw()
        self.bar_canvas.draw()

    def update_kpis(self):
        while self.kpi_layout.count():
            child = self.kpi_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        balances = self.db.get_account_balances()
        net_income = self.db.get_net_income()
        rev = sum(d['balance'] for d in balances.values() if d['type'] == 'Revenue')
        exp = sum(d['balance'] for d in balances.values() if d['type'] == 'Expense')
        
        self.kpi_layout.addWidget(KPICard("Net Income", f"{net_income:,.2f}", "Total Profit / Loss", net_income >= 0))
        self.kpi_layout.addWidget(KPICard("Total Revenue", f"{rev:,.2f}", "Gross Earnings", True))
        self.kpi_layout.addWidget(KPICard("Total Expenses", f"({exp:,.2f})", "Operational Costs", False))

    def plot_trend_chart(self):
        self.trend_canvas.figure.clear()
        ax = self.trend_canvas.figure.add_subplot(111)
        self.style_ax(ax)
        # Dummy Data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        rev_data = [12000, 15000, 13000, 18000, 22000, 25000]
        exp_data = [8000, 9000, 8500, 10000, 11000, 12000]
        ax.plot(months, rev_data, color=COLOR_ACCENT, linewidth=2, marker='o', label='Revenue')
        ax.plot(months, exp_data, color=COLOR_DANGER, linewidth=2, marker='o', label='Expenses')
        ax.fill_between(months, rev_data, alpha=0.1, color=COLOR_ACCENT)
        ax.legend(frameon=False, labelcolor='white')
        ax.set_title("Cash Flow Trend (6 Months)", color=COLOR_TEXT, fontsize=10, pad=10, loc='left')
        ax.grid(True, color='#333', linestyle='--', linewidth=0.5)

    def plot_expense_donut(self, balances):
        self.pie_canvas.figure.clear()
        ax = self.pie_canvas.figure.add_subplot(111)
        labels = []
        sizes = []
        for name, info in balances.items():
            if info['type'] == 'Expense' and info['balance'] > 0:
                labels.append(name)
                sizes.append(info['balance'])
        
        if not sizes:
            ax.text(0.5, 0.5, "No Data", ha='center', color=COLOR_SUBTEXT)
            ax.axis('off')
            return

        colors = [COLOR_ACCENT, '#222831', '#393E46', '#00ADB5', '#EEEEEE']
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                          startangle=90, colors=colors, pctdistance=0.85)
        centre_circle = matplotlib.patches.Circle((0,0), 0.70, fc=COLOR_BG)
        self.pie_canvas.figure.gca().add_artist(centre_circle)
        for t in texts: t.set_color(COLOR_TEXT)
        for t in autotexts: t.set_color(COLOR_TEXT)
        ax.set_title("Expense Breakdown", color=COLOR_TEXT, fontsize=10, pad=10)

    def plot_net_worth_bar(self, balances):
        self.bar_canvas.figure.clear()
        ax = self.bar_canvas.figure.add_subplot(111)
        self.style_ax(ax)
        assets = sum(d['balance'] for d in balances.values() if d['type'] == 'Asset')
        liabs = sum(d['balance'] for d in balances.values() if d['type'] == 'Liability')
        bars = ax.bar(['Assets', 'Liabilities'], [assets, liabs], color=[COLOR_ACCENT, COLOR_DANGER], width=0.4)
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:,.0f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', color=COLOR_TEXT)
        ax.set_title("Assets vs Liabilities", color=COLOR_TEXT, fontsize=10, pad=10)
        ax.grid(axis='y', color='#333', linestyle='--', linewidth=0.5)

    def style_ax(self, ax):
        ax.set_facecolor(COLOR_BG)
        ax.tick_params(colors=COLOR_SUBTEXT, which='both')
        for spine in ax.spines.values(): spine.set_visible(False)