import sqlite3
import uuid

class DatabaseHandler:
    def __init__(self, db_name="ratio.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Table 1: Transaction Header (Groups the splits)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                date TEXT,
                description TEXT,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table 2: Journal Splits (The actual data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT,
                account_name TEXT,
                account_type TEXT,
                debit REAL DEFAULT 0.0,
                credit REAL DEFAULT 0.0,
                FOREIGN KEY(transaction_id) REFERENCES transactions(id)
            )
        """)
        self.conn.commit()

    def add_transaction(self, date, description, lines):
        """
        Saves a balanced transaction.
        lines = [{'account_name': 'Cash', 'account_type': 'Asset', 'debit': 100, 'credit': 0}, ...]
        """
        cursor = self.conn.cursor()
        trans_id = str(uuid.uuid4())
        
        try:
            # 1. Save Header
            cursor.execute("INSERT INTO transactions (id, date, description) VALUES (?, ?, ?)", 
                           (trans_id, date, description))
            
            # 2. Save Lines
            for l in lines:
                cursor.execute("""
                    INSERT INTO journal_entries (transaction_id, account_name, account_type, debit, credit)
                    VALUES (?, ?, ?, ?, ?)
                """, (trans_id, l['account_name'], l['account_type'], l['debit'], l['credit']))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_ledger(self, account_name=None):
        """
        FIXED: This is the function your UI was missing.
        It joins the tables so the UI can read them as a flat list.
        """
        cursor = self.conn.cursor()
        
        # Base Query: Join Entries with Transaction Details
        sql = """
            SELECT 
                j.id, 
                t.id as transaction_id, 
                t.date, 
                j.account_name, 
                j.account_type, 
                t.description, 
                j.debit, 
                j.credit
            FROM journal_entries j
            JOIN transactions t ON j.transaction_id = t.id
        """
        
        if account_name and account_name != "All":
            sql += " WHERE j.account_name = ? ORDER BY t.date DESC"
            cursor.execute(sql, (account_name,))
        else:
            sql += " ORDER BY t.date DESC, t.posted_at DESC"
            cursor.execute(sql)
            
        return cursor.fetchall()

    def get_unique_accounts(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT account_name FROM journal_entries ORDER BY account_name ASC")
        return [row[0] for row in cursor.fetchall()]

    def get_account_balances(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT account_name, account_type, SUM(debit), SUM(credit) FROM journal_entries GROUP BY account_name")
        data = cursor.fetchall()
        
        accounts = {}
        for name, acc_type, deb_sum, cred_sum in data:
            deb_sum = deb_sum or 0
            cred_sum = cred_sum or 0
            
            if acc_type in ["Asset", "Expense"]:
                balance = deb_sum - cred_sum
            else:
                balance = cred_sum - deb_sum
            accounts[name] = {"type": acc_type, "balance": round(balance, 2)}
        return accounts

    def get_net_income(self):
        accounts = self.get_account_balances()
        revenue = sum(a['balance'] for a in accounts.values() if a['type'] == 'Revenue')
        expenses = sum(a['balance'] for a in accounts.values() if a['type'] == 'Expense')
        return round(revenue - expenses, 2)
        
    def check_trial_balance(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(debit), SUM(credit) FROM journal_entries")
        d, c = cursor.fetchone()
        return round(d or 0, 2) == round(c or 0, 2)