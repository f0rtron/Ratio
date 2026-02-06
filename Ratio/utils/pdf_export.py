from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime

class PDFExporter:
    def __init__(self, db):
        self.db = db
        self.styles = getSampleStyleSheet()
        self.create_custom_styles()

    def create_custom_styles(self):
        self.styles.add(ParagraphStyle(name='CenterTitle', parent=self.styles['Heading1'], alignment=TA_CENTER, spaceAfter=10))
        self.styles.add(ParagraphStyle(name='SubTitle', parent=self.styles['Normal'], alignment=TA_CENTER, textColor=colors.grey))

    def generate_full_report(self, start_date, end_date, filename="Ratio_Report.pdf"):
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elements = []

        # Header
        elements.append(Paragraph("FINANCIAL REPORT", self.styles['CenterTitle']))
        elements.append(Paragraph(f"Period: {start_date} to {end_date}", self.styles['SubTitle']))
        elements.append(Spacer(1, 30))

        # 1. Income Statement
        elements.append(Paragraph(f"Income Statement", self.styles['Heading2']))
        elements.append(self._build_income_statement(start_date, end_date))
        elements.append(Spacer(1, 30))

        # 2. Balance Sheet
        elements.append(Paragraph(f"Balance Sheet (As of {end_date})", self.styles['Heading2']))
        elements.append(self._build_balance_sheet(end_date))
        
        try:
            doc.build(elements)
            return filename
        except Exception as e:
            raise e

    def _fmt(self, value):
        """Formats numbers: standard accounting format (negatives in parens)."""
        try:
            val = float(value)
        except:
            return str(value)
            
        if val < 0:
            return f"({abs(val):,.2f})" # Returns (1,000.00) for negative
        return f"{val:,.2f}"

    def _build_income_statement(self, start, end):
        accounts = self.db.get_balances_period(start, end)
        data = [['Account', 'Amount']]
        
        rev = 0.0
        exp = 0.0
        
        # REVENUE
        data.append(['REVENUE', ''])
        for name, info in accounts.items():
            if info['type'] == 'Revenue':
                val = info['net_balance']
                data.append([name, self._fmt(val)])
                rev += val
        
        # EXPENSES
        data.append(['EXPENSES', ''])
        for name, info in accounts.items():
            if info['type'] == 'Expense':
                val = info['net_balance']
                data.append([name, self._fmt(val)])
                exp += val
        
        # NET INCOME CALCULATION
        net = rev - exp
        
        data.append(['', ''])
        
        # DYNAMIC LABEL: Changes based on Profit or Loss
        if net >= 0:
            label = "NET INCOME"
        else:
            label = "NET LOSS"
            
        data.append([label, self._fmt(net)])
        
        t = Table(data, colWidths=[350, 100])
        t.setStyle(self._get_table_style(has_total=True))
        return t

    def _build_balance_sheet(self, as_of):
        accounts = self.db.get_balances_snapshot(as_of)
        net_income = self.db.get_net_income(end_date=as_of) 
        
        data = [['Account', 'Amount']]
        
        asset = 0.0
        liab = 0.0
        equity = 0.0
        
        data.append(['ASSETS', ''])
        for name, info in accounts.items():
            if info['type'] == 'Asset':
                val = info['net_balance']
                data.append([name, self._fmt(val)])
                asset += val
        data.append(['TOTAL ASSETS', self._fmt(asset)])
        data.append(['', ''])
        
        data.append(['LIABILITIES', ''])
        for name, info in accounts.items():
            if info['type'] == 'Liability':
                val = info['net_balance']
                data.append([name, self._fmt(val)])
                liab += val
        
        data.append(['EQUITY', ''])
        for name, info in accounts.items():
            if info['type'] == 'Equity':
                val = info['net_balance']
                data.append([name, self._fmt(val)])
                equity += val
                
        # Retained Earnings
        data.append(['Retained Earnings (Net Income)', self._fmt(net_income)])
        equity += net_income
        
        data.append(['TOTAL LIAB & EQUITY', self._fmt(liab + equity)])
        
        t = Table(data, colWidths=[350, 100])
        t.setStyle(self._get_table_style(has_total=True))
        return t

    def _get_table_style(self, has_total=False):
        style = [
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), # Header Bold
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),            # Numbers Right Aligned
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),    # Grid Lines
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke), # Header Color
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ]
        
        if has_total:
            # Bold the last row
            style.append(('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'))
            # Add line above total
            style.append(('LINEABOVE', (0,-1), (-1,-1), 1.5, colors.black))
            
        return TableStyle(style)