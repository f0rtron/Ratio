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
        self.styles.add(ParagraphStyle(name='CenterTitle', parent=self.styles['Heading1'], alignment=TA_CENTER, spaceAfter=20))
        self.styles.add(ParagraphStyle(name='SubTitle', parent=self.styles['Normal'], alignment=TA_CENTER, textColor=colors.grey))

    # FIXED: Method name matches UI call
    def generate_full_report(self, filename="Ratio_Financial_Report.pdf"):
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elements = []

        # --- HEADER ---
        elements.append(Paragraph("RATIO", self.styles['CenterTitle']))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d')}", self.styles['SubTitle']))
        elements.append(Spacer(1, 30))

        # --- 1. INCOME STATEMENT ---
        elements.append(Paragraph("Income Statement", self.styles['Heading2']))
        elements.append(self._build_income_statement())
        elements.append(Spacer(1, 30))

        # --- 2. BALANCE SHEET ---
        elements.append(Paragraph("Balance Sheet", self.styles['Heading2']))
        elements.append(self._build_balance_sheet())
        elements.append(PageBreak())

        # --- 3. GENERAL LEDGER ---
        elements.append(Paragraph("General Ledger (Journal)", self.styles['Heading2']))
        elements.append(self._build_ledger_table())

        doc.build(elements)
        return filename

    def _fmt(self, value):
        if value < 0: return f"({abs(value):,.2f})"
        return f"{value:,.2f}"

    def _build_income_statement(self):
        accounts = self.db.get_account_balances()
        data = [['Account', 'Amount']]
        
        rev_total = 0
        exp_total = 0
        
        data.append(['REVENUE', ''])
        for name, info in accounts.items():
            if info['type'] == 'Revenue':
                data.append([name, self._fmt(info['balance'])])
                rev_total += info['balance']
        
        data.append(['EXPENSES', ''])
        for name, info in accounts.items():
            if info['type'] == 'Expense':
                data.append([name, self._fmt(info['balance'])])
                exp_total += info['balance']
        
        net_income = rev_total - exp_total
        data.append(['', ''])
        data.append(['NET INCOME', self._fmt(net_income)])
        
        t = Table(data, colWidths=[350, 100])
        t.setStyle(self._get_table_style(has_total=True))
        return t

    def _build_balance_sheet(self):
        accounts = self.db.get_account_balances()
        net_income = self.db.get_net_income()
        
        data = [['Account', 'Amount']]
        
        asset_total = 0
        liab_total = 0
        equity_total = 0

        data.append(['ASSETS', ''])
        for name, info in accounts.items():
            if info['type'] == 'Asset':
                data.append([name, self._fmt(info['balance'])])
                asset_total += info['balance']
        data.append(['TOTAL ASSETS', self._fmt(asset_total)])
        data.append(['', ''])

        data.append(['LIABILITIES', ''])
        for name, info in accounts.items():
            if info['type'] == 'Liability':
                data.append([name, self._fmt(info['balance'])])
                liab_total += info['balance']
        
        data.append(['EQUITY', ''])
        for name, info in accounts.items():
            if info['type'] == 'Equity':
                data.append([name, self._fmt(info['balance'])])
                equity_total += info['balance']
        
        data.append(['Net Income (Retained)', self._fmt(net_income)])
        equity_total += net_income
        
        total_liab_equity = liab_total + equity_total
        data.append(['TOTAL LIAB. & EQUITY', self._fmt(total_liab_equity)])

        t = Table(data, colWidths=[350, 100])
        t.setStyle(self._get_table_style(has_total=True))
        return t

    def _build_ledger_table(self):
        # We use the new double-entry getter
        entries = self.db.get_ledger()
        data = [['Date', 'Account', 'Desc', 'Debit', 'Credit']]
        
        # entry schema from get_ledger: 
        # (id, trans_id, date, name, type, desc, debit, credit)
        for row in entries:
            data.append([
                row[2], # Date
                row[3], # Name
                row[5], # Desc
                self._fmt(row[6]), # Debit
                self._fmt(row[7])  # Credit
            ])
            
        t = Table(data, colWidths=[80, 120, 150, 70, 70])
        t.setStyle(self._get_table_style())
        return t

    def _get_table_style(self, has_total=False):
        style = [
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'), 
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ]
        if has_total:
            style.append(('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'))
            style.append(('LINEABOVE', (0,-1), (-1,-1), 1, colors.black))
        return TableStyle(style)