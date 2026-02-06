import sqlite3
import uuid

class DatabaseHandler:
    def __init__(self, db_name="ratio.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # 1. Transactions Header
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                date TEXT,
                description TEXT,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Journal Entries (Splits)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT,
                account_name TEXT,
                account_type TEXT,
                debit REAL DEFAULT 0.0,
                credit REAL DEFAULT 0.0,
                FOREIGN KEY(transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON transactions(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_acc_name ON journal_entries(account_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_id ON journal_entries(transaction_id)")
        
        self.conn.commit()

    # --- WRITING DATA ---

    def add_transaction(self, date, description, lines):
        cursor = self.conn.cursor()
        trans_id = str(uuid.uuid4())
        
        try:
            cursor.execute("INSERT INTO transactions (id, date, description) VALUES (?, ?, ?)", 
                           (trans_id, date, description))
            
            for l in lines:
                clean_name = l['account_name'].strip().title()
                cursor.execute("""
                    INSERT INTO journal_entries (transaction_id, account_name, account_type, debit, credit)
                    VALUES (?, ?, ?, ?, ?)
                """, (trans_id, clean_name, l['account_type'], l['debit'], l['credit']))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_transaction(self, trans_id, new_date, new_desc, new_lines):
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE transactions SET date = ?, description = ? WHERE id = ?", 
                           (new_date, new_desc, trans_id))
            cursor.execute("DELETE FROM journal_entries WHERE transaction_id = ?", (trans_id,))
            
            for l in new_lines:
                clean_name = l['account_name'].strip().title()
                cursor.execute("""
                    INSERT INTO journal_entries (transaction_id, account_name, account_type, debit, credit)
                    VALUES (?, ?, ?, ?, ?)
                """, (trans_id, clean_name, l['account_type'], l['debit'], l['credit']))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_transaction(self, trans_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM journal_entries WHERE transaction_id = ?", (trans_id,))
            cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    # --- NEW: RESET FUNCTION ---
    def clear_all_data(self):
        """Wipes all transactions and entries. Returns to clean slate."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM journal_entries")
            cursor.execute("DELETE FROM transactions")
            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='journal_entries'")
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    # --- READING DATA ---

    def get_unique_accounts(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT account_name FROM journal_entries ORDER BY account_name ASC")
        return [row[0] for row in cursor.fetchall()]

    def get_full_transaction(self, trans_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT date, description FROM transactions WHERE id=?", (trans_id,))
        res = cursor.fetchone()
        if not res: return None, []
        header = {'date': res[0], 'description': res[1]}
        
        cursor.execute("SELECT account_name, account_type, debit, credit FROM journal_entries WHERE transaction_id=?", (trans_id,))
        lines = []
        for row in cursor.fetchall():
            lines.append({'name': row[0], 'type': row[1], 'debit': row[2], 'credit': row[3]})
        return header, lines

    def get_transaction_details(self, trans_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT account_name, account_type, debit, credit FROM journal_entries WHERE transaction_id = ?", (trans_id,))
        return cursor.fetchall()

    def get_ledger(self, account_name=None):
        cursor = self.conn.cursor()
        sql = """
            SELECT t.id, t.date, j.account_name, j.account_type, t.description, j.debit, j.credit
            FROM journal_entries j
            JOIN transactions t ON j.transaction_id = t.id
        """
        params = ()
        if account_name and account_name != "All":
            sql += " WHERE j.account_name = ?"
            params = (account_name,)
        
        sql += " ORDER BY t.date ASC, t.posted_at ASC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        results = []
        running_bal = 0.0
        
        for tid, date, name, acc_type, desc, dr, cr in rows:
            if acc_type in ["Asset", "Expense"]:
                running_bal += (dr - cr)
            else:
                running_bal += (cr - dr)
            results.append((tid, date, name, acc_type, desc, dr, cr, running_bal))
            
        if not account_name or account_name == "All":
            return sorted(results, key=lambda x: x[1], reverse=True)
        return results

    # --- REPORTING ---

    def get_account_balances(self):
        return self.get_balances_snapshot()

    def get_balances_snapshot(self, as_of_date=None):
        cursor = self.conn.cursor()
        sql = """
            SELECT j.account_name, j.account_type, SUM(j.debit), SUM(j.credit) 
            FROM journal_entries j
            JOIN transactions t ON j.transaction_id = t.id
        """
        params = []
        if as_of_date:
            sql += " WHERE t.date <= ?"
            params.append(as_of_date)
        sql += " GROUP BY j.account_name"
        cursor.execute(sql, params)
        return self._process_balances(cursor.fetchall())

    def get_balances_period(self, start_date=None, end_date=None):
        cursor = self.conn.cursor()
        sql = """
            SELECT j.account_name, j.account_type, SUM(j.debit), SUM(j.credit) 
            FROM journal_entries j
            JOIN transactions t ON j.transaction_id = t.id
        """
        conditions = []
        params = []
        if start_date:
            conditions.append("t.date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("t.date <= ?")
            params.append(end_date)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " GROUP BY j.account_name"
        cursor.execute(sql, params)
        return self._process_balances(cursor.fetchall())

    def _process_balances(self, raw_data):
        accounts = {}
        for name, acc_type, deb_sum, cred_sum in raw_data:
            deb_sum = deb_sum or 0.0
            cred_sum = cred_sum or 0.0
            
            if acc_type in ["Asset", "Expense"]:
                net = deb_sum - cred_sum
            else:
                net = cred_sum - deb_sum
            accounts[name] = {"type": acc_type, "debit_total": deb_sum, "credit_total": cred_sum, "net_balance": net}
        return accounts

    def get_net_income(self, start_date=None, end_date=None):
        if start_date or end_date:
            accounts = self.get_balances_period(start_date, end_date)
        else:
            accounts = self.get_balances_snapshot()
        rev = sum(a['net_balance'] for a in accounts.values() if a['type'] == 'Revenue')
        exp = sum(a['net_balance'] for a in accounts.values() if a['type'] == 'Expense')
        return rev - exp