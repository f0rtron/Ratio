from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QSizePolicy, QScrollArea, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QCursor

import matplotlib
matplotlib.use('QtAgg') 
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import numpy as np # Needed for Radar math
import datetime

# --- THEME COLORS ---
COLOR_BG = "#121212"
COLOR_CARD = "#1e1e1e"
COLOR_ACCENT = "#00ADB5"
COLOR_DANGER = "#FF5555"
COLOR_SUCCESS = "#00C853"
COLOR_TEXT = "#E0E0E0"
COLOR_SUBTEXT = "#888888"

class KPICard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, value, subtext, is_positive=True, is_neutral=False):
        super().__init__()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD};
                border-radius: 12px;
                border: 1px solid #333;
            }}
            QFrame:hover {{
                border: 1px solid {COLOR_ACCENT};
                background-color: #252525;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet(f"color: {COLOR_SUBTEXT}; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none; background: transparent;")
        
        if is_neutral:
            color = COLOR_TEXT
        else:
            color = COLOR_SUCCESS if is_positive else COLOR_DANGER
            
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold; border: none; background: transparent;")
        
        lbl_sub = QLabel(subtext)
        lbl_sub.setStyleSheet(f"color: {COLOR_SUBTEXT}; font-size: 12px; border: none; background: transparent;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class RecentTransactionsCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{ background-color: {COLOR_CARD}; border-radius: 12px; border: 1px solid #333; }}
            QTableWidget {{ background-color: {COLOR_CARD}; border: none; color: {COLOR_TEXT}; }}
            QHeaderView::section {{ background-color: #333; color: {COLOR_TEXT}; border: none; padding: 4px; }}
        """)
        layout = QVBoxLayout(self)
        
        lbl = QLabel("Recent Activity")
        lbl.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 16px; font-weight: bold; margin-bottom: 10px; border: none; background: transparent;")
        layout.addWidget(lbl)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Date", "Desc", "Amount"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setFixedHeight(200) 
        
        layout.addWidget(self.table)

    def update_data(self, transactions):
        self.table.setRowCount(len(transactions))
        for i, row in enumerate(transactions):
            _, date, _, _, desc, dr, cr, _ = row
            
            if dr > 0:
                amt = f"-{dr:,.0f}" 
                color = COLOR_TEXT
            else:
                amt = f"+{cr:,.0f}"
                color = COLOR_SUCCESS
            
            self.table.setItem(i, 0, QTableWidgetItem(date[5:])) 
            self.table.setItem(i, 1, QTableWidgetItem(desc))
            
            amt_item = QTableWidgetItem(amt)
            amt_item.setForeground(QColor(color))
            self.table.setItem(i, 2, amt_item)

class StatsPage(QWidget):
    go_to_income_stmt = pyqtSignal()
    go_to_ledger = pyqtSignal()
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"border: none; background-color: {COLOR_BG};") 
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(30, 30, 30, 100)
        self.content_layout.setSpacing(25)
        
        # --- HEADER & FILTERS ---
        header_layout = QHBoxLayout()
        title = QLabel("Financial Overview")
        title.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {COLOR_TEXT};")
        
        # Filters
        self.date_filter = QComboBox()
        self.date_filter.addItems(["All Time", "This Month", "Last Month", "Year to Date"])
        self.date_filter.setFixedWidth(140)
        self.date_filter.setStyleSheet("""
            QComboBox { padding: 8px; border: 1px solid #444; border-radius: 5px; background: #252525; color: white; }
            QComboBox::drop-down { border: none; }
        """)
        self.date_filter.currentTextChanged.connect(self.refresh)
        
        self.granularity_filter = QComboBox()
        self.granularity_filter.addItems(["Daily", "Monthly"])
        self.granularity_filter.setFixedWidth(100)
        self.granularity_filter.setStyleSheet(self.date_filter.styleSheet())
        self.granularity_filter.currentTextChanged.connect(self.refresh)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("View:"))
        header_layout.addWidget(self.granularity_filter)
        header_layout.addSpacing(15)
        header_layout.addWidget(QLabel("Period:"))
        header_layout.addWidget(self.date_filter)
        self.content_layout.addLayout(header_layout)
        
        # --- KPI ROW ---
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(20)
        self.content_layout.addLayout(self.kpi_layout)
        
        # --- MIDDLE SECTION (Trend + Recent) ---
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(20)
        
        self.trend_canvas = self.create_chart_canvas()
        self.trend_canvas.setMinimumHeight(350)
        middle_layout.addWidget(self.trend_canvas, stretch=2)
        
        self.recent_list = RecentTransactionsCard()
        middle_layout.addWidget(self.recent_list, stretch=1)
        
        self.content_layout.addLayout(middle_layout)
        
        # --- BOTTOM SECTION (Radar + Net Worth) ---
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        # Renamed variable to reflect new Spider Chart
        self.radar_canvas = self.create_chart_canvas()
        self.radar_canvas.setMinimumHeight(350)
        
        self.net_worth_canvas = self.create_chart_canvas()
        self.net_worth_canvas.setMinimumHeight(350)
        
        bottom_layout.addWidget(self.radar_canvas)
        bottom_layout.addWidget(self.net_worth_canvas)
        self.content_layout.addLayout(bottom_layout)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def create_chart_canvas(self):
        fig = Figure(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor(COLOR_CARD)
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet(f"background-color: {COLOR_CARD}; border-radius: 12px; border: 1px solid #333;")
        return canvas

    def get_date_range(self):
        mode = self.date_filter.currentText()
        today = QDate.currentDate()
        if mode == "This Month":
            start = QDate(today.year(), today.month(), 1)
            return start.toString("yyyy-MM-dd"), today.toString("yyyy-MM-dd")
        elif mode == "Last Month":
            first = QDate(today.year(), today.month(), 1)
            end_last = first.addDays(-1)
            start_last = QDate(end_last.year(), end_last.month(), 1)
            return start_last.toString("yyyy-MM-dd"), end_last.toString("yyyy-MM-dd")
        elif mode == "Year to Date":
            start = QDate(today.year(), 1, 1)
            return start.toString("yyyy-MM-dd"), today.toString("yyyy-MM-dd")
        return None, None

    def refresh(self):
        try:
            start, end = self.get_date_range()
            
            # Fetch Data
            if start:
                period_bals = self.db.get_balances_period(start, end)
            else:
                period_bals = self.db.get_balances_snapshot() 
            
            snap_bals = self.db.get_balances_snapshot(end)
            
            # Update UI
            self.update_kpis(period_bals, start, end)
            self.update_recent_activity()
            
            self.plot_trend_chart(start, end)
            self.plot_expense_radar(period_bals) # NEW RADAR
            self.plot_net_worth_bar(snap_bals)
            
            # Draw
            self.trend_canvas.draw()
            self.radar_canvas.draw()
            self.net_worth_canvas.draw()
        except Exception as e:
            print(f"Stats Refresh Error: {e}")

    def update_kpis(self, balances, start, end):
        while self.kpi_layout.count():
            child = self.kpi_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        rev = sum(d['net_balance'] for d in balances.values() if d['type'] == 'Revenue')
        exp = sum(d['net_balance'] for d in balances.values() if d['type'] == 'Expense')
        net_income = rev - exp
        margin = (net_income / rev * 100) if rev > 0 else 0.0
        period_text = "Selected Period" if start else "All Time"

        card_ni = KPICard("Net Income", f"{net_income:,.2f}", period_text, net_income >= 0)
        card_rev = KPICard("Revenue", f"{rev:,.2f}", period_text, True)
        card_exp = KPICard("Expenses", f"{exp:,.2f}", period_text, False)
        card_mar = KPICard("Profit Margin", f"{margin:.1f}%", "Net / Rev", margin > 0, is_neutral=False)
        
        card_ni.clicked.connect(self.go_to_income_stmt.emit)
        card_rev.clicked.connect(self.go_to_income_stmt.emit)
        card_exp.clicked.connect(self.go_to_income_stmt.emit)
        
        self.kpi_layout.addWidget(card_ni)
        self.kpi_layout.addWidget(card_rev)
        self.kpi_layout.addWidget(card_exp)
        self.kpi_layout.addWidget(card_mar)

    def update_recent_activity(self):
        rows = self.db.get_ledger("All") 
        self.recent_list.update_data(rows[:8])

    def plot_trend_chart(self, start, end):
        self.trend_canvas.figure.clear()
        ax = self.trend_canvas.figure.add_subplot(111)
        self.style_ax(ax)
        
        rows = self.db.get_ledger("All")
        trend_data = {}
        
        granularity = self.granularity_filter.currentText()
        auto_weekly = False
        if granularity == "Daily":
            if start and end:
                s_date = datetime.datetime.strptime(start, "%Y-%m-%d")
                e_date = datetime.datetime.strptime(end, "%Y-%m-%d")
                if (e_date - s_date).days > 60: auto_weekly = True
            elif not start and rows:
                 # Logic for All Time auto-grouping
                 last = datetime.datetime.strptime(rows[0][1], "%Y-%m-%d")
                 first = datetime.datetime.strptime(rows[-1][1], "%Y-%m-%d")
                 if (last - first).days > 60: auto_weekly = True

        for row in rows:
            date_str = row[1]
            if start and (date_str < start or date_str > end): continue
            
            if granularity == "Monthly":
                key = date_str[:7] + "-01"
            elif auto_weekly:
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                start_of_week = dt - datetime.timedelta(days=dt.weekday())
                key = start_of_week.strftime("%Y-%m-%d")
            else:
                key = date_str
            
            if key not in trend_data: trend_data[key] = {'rev': 0.0, 'exp': 0.0}
            
            if row[3] == 'Revenue': trend_data[key]['rev'] += (row[6] - row[5])
            elif row[3] == 'Expense': trend_data[key]['exp'] += (row[5] - row[6])
                
        sorted_keys = sorted(trend_data.keys())
        dates, revs, exps = [], [], []
        
        if not sorted_keys:
             ax.text(0.5, 0.5, "No Activity", ha='center', color=COLOR_SUBTEXT)
             return

        for k in sorted_keys:
            dt = datetime.datetime.strptime(k, "%Y-%m-%d")
            dates.append(dt)
            revs.append(trend_data[k]['rev'])
            exps.append(trend_data[k]['exp'])
            
        ax.plot(dates, revs, color=COLOR_SUCCESS, linewidth=2, marker='o', label='Rev')
        ax.plot(dates, exps, color=COLOR_DANGER, linewidth=2, marker='o', label='Exp')
        ax.fill_between(dates, revs, alpha=0.1, color=COLOR_SUCCESS)
        
        if granularity == "Monthly":
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
        elif auto_weekly:
             ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
        
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.legend(frameon=False, labelcolor='white')
        
        if granularity == "Monthly": title = "Monthly Trend"
        elif auto_weekly: title = "Weekly Trend"
        else: title = "Daily Trend"
        ax.set_title(title, color=COLOR_TEXT, fontsize=10, pad=10, loc='left')

    def plot_expense_radar(self, balances):
        """Generates a Spider/Radar Chart for Expense Composition"""
        self.radar_canvas.figure.clear()
        
        # 1. Filter Data (Top 6 Expenses)
        data = []
        for name, info in balances.items():
            if info['type'] == 'Expense' and info['net_balance'] > 0:
                data.append((name, info['net_balance']))
        
        data.sort(key=lambda x: x[1], reverse=True)
        data = data[:6] # Top 6
        
        # Handle Empty State
        if not data:
            ax = self.radar_canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, "No Expenses", ha='center', color=COLOR_SUBTEXT)
            self.style_ax(ax)
            return
            
        # 2. Setup Polar Plot
        ax = self.radar_canvas.figure.add_subplot(111, polar=True)
        ax.set_facecolor(COLOR_CARD)
        
        # 3. Prepare Math (Angles & Values)
        categories = [x[0] for x in data]
        values = [x[1] for x in data]
        N = len(categories)
        
        # Compute angles (one slice per category)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        
        # Close the loop (repeat first item)
        values += values[:1]
        angles += angles[:1]
        
        # 4. Plot
        ax.plot(angles, values, color=COLOR_DANGER, linewidth=2, linestyle='solid')
        ax.fill(angles, values, color=COLOR_DANGER, alpha=0.25)
        
        # 5. Styling The Web
        # X-Labels (Categories)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, color=COLOR_TEXT, fontsize=9)
        
        # Y-Labels (Radial Rings) - Make them subtle
        ax.set_rlabel_position(0)
        plt_grids = ax.yaxis.get_gridlines()
        for gl in plt_grids:
            gl.set_color('#333')
            gl.set_linestyle('--')
            
        ax.spines['polar'].set_visible(False) # Hide outer circle line
        ax.grid(color='#333', linestyle='--')
        
        # Remove radial numbers to keep it clean (optional, often better for dashboards)
        ax.set_yticklabels([]) 
        
        ax.set_title("Expense Composition", color=COLOR_TEXT, fontsize=10, pad=20, loc='center')

    def plot_net_worth_bar(self, balances):
        self.net_worth_canvas.figure.clear()
        ax = self.net_worth_canvas.figure.add_subplot(111)
        self.style_ax(ax)
        
        assets = sum(d['net_balance'] for d in balances.values() if d['type'] == 'Asset')
        liabs = sum(d['net_balance'] for d in balances.values() if d['type'] == 'Liability')
        equity = assets - liabs
        
        cats = ['Assets', 'Liabilities', 'Equity']
        vals = [assets, liabs, equity]
        cols = [COLOR_SUCCESS, COLOR_DANGER, COLOR_ACCENT]
        
        bars = ax.bar(cats, vals, color=cols, width=0.5)
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f'{h:,.0f}', xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', color=COLOR_TEXT)
        
        ax.set_title("Financial Position", color=COLOR_TEXT, fontsize=10, pad=10, loc='left')

    def style_ax(self, ax):
        ax.set_facecolor(COLOR_CARD)
        ax.tick_params(colors=COLOR_SUBTEXT, which='both')
        for spine in ax.spines.values(): spine.set_visible(False)