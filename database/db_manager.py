import sqlite3
import os
import json
from datetime import datetime
import pandas as pd
import logging
from utils.encryption import encrypt, decrypt

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Database manager for the finance application
    
    Handles database connections and operations for users, connections,
    accounts, transactions, and budgets.
    """
    
    def __init__(self, db_path=None):
        """
        Initialize the database manager
        
        Parameters:
        -----------
        db_path: str, optional
            Path to the database file, defaults to 'finance_app.db' in the current directory
        """
        # Use provided path or default
        self.db_path = db_path or os.path.join(os.getcwd(), 'finance_app.db')
        
        # Connect to the database
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        
        # Initialize database tables
        self._init_db()
        
        logger.info("Database initialized successfully")
    
    def _init_db(self):
        """Initialize the database tables if they don't exist"""
        # Users table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Bank connections table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS bank_connections (
            connection_id TEXT PRIMARY KEY,
            user_id TEXT,
            provider TEXT,
            access_token TEXT,
            refresh_token TEXT,
            token_expiry TIMESTAMP,
            last_sync TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # Bank accounts table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS bank_accounts (
            account_id TEXT PRIMARY KEY,
            connection_id TEXT,
            user_id TEXT,
            name TEXT,
            type TEXT,
            provider TEXT,
            currency TEXT,
            balance NUMERIC,
            last_updated TIMESTAMP,
            account_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (connection_id) REFERENCES bank_connections(connection_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # Transactions table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            account_id TEXT,
            user_id TEXT,
            date TIMESTAMP,
            description TEXT,
            amount NUMERIC,
            currency TEXT,
            type TEXT,
            category TEXT,
            transaction_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES bank_accounts(account_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # Budgets table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            category TEXT,
            amount NUMERIC,
            period TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, category)
        )
        ''')
        
        # Commit changes
        self.connection.commit()
    
    def create_user(self, user_id):
        """
        Create a new user if not exists
        
        Parameters:
        -----------
        user_id: str
            User ID
            
        Returns:
        --------
        bool
            Whether the user was created
        """
        try:
            # Check if user exists
            self.cursor.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            existing_user = self.cursor.fetchone()
            
            if existing_user:
                return False
            
            # Create new user
            self.cursor.execute(
                "INSERT INTO users (user_id) VALUES (?)",
                (user_id,)
            )
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return False
    
    def save_bank_connection(self, user_id, connection_id, provider, tokens, expiry=None):
        """
        Save bank connection tokens
        
        Parameters:
        -----------
        user_id: str
            User ID
        connection_id: str
            Connection ID
        provider: str
            Provider name (e.g., "TrueLayer")
        tokens: dict
            Dictionary containing access_token and refresh_token
        expiry: str or datetime, optional
            Token expiry date
            
        Returns:
        --------
        bool
            Whether the connection was saved
        """
        try:
            # Ensure user exists
            self.create_user(user_id)
            
            # Encrypt tokens
            access_token = encrypt(tokens["access_token"])
            refresh_token = encrypt(tokens["refresh_token"]) if "refresh_token" in tokens else None
            
            # Format expiry
            if expiry:
                if isinstance(expiry, datetime):
                    expiry = expiry.isoformat()
            
            # Save connection
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO bank_connections 
                (connection_id, user_id, provider, access_token, refresh_token, token_expiry) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (connection_id, user_id, provider, access_token, refresh_token, expiry)
            )
            
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving bank connection: {str(e)}")
            return False
    
    def get_bank_connection(self, connection_id=None, user_id=None):
        """
        Get a bank connection by ID or user
        
        Parameters:
        -----------
        connection_id: str, optional
            Connection ID
        user_id: str, optional
            User ID
            
        Returns:
        --------
        dict or None
            Connection details with decrypted tokens
        """
        try:
            if connection_id:
                self.cursor.execute(
                    "SELECT * FROM bank_connections WHERE connection_id = ?",
                    (connection_id,)
                )
                connection = self.cursor.fetchone()
            elif user_id:
                self.cursor.execute(
                    "SELECT * FROM bank_connections WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                    (user_id,)
                )
                connection = self.cursor.fetchone()
            else:
                return None
            
            if not connection:
                return None
            
            result = dict(connection)
            
            # Decrypt tokens
            if result.get("access_token"):
                result["access_token"] = decrypt(result["access_token"])
            
            if result.get("refresh_token"):
                result["refresh_token"] = decrypt(result["refresh_token"])
            
            return result
        except Exception as e:
            logger.error(f"Error getting bank connection: {str(e)}")
            return None
    
    def get_bank_connections(self, user_id):
        """
        Get all bank connections for a user
        
        Parameters:
        -----------
        user_id: str
            User ID
            
        Returns:
        --------
        list
            List of connection dictionaries
        """
        try:
            self.cursor.execute(
                "SELECT * FROM bank_connections WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            connections = self.cursor.fetchall()
            
            results = []
            for connection in connections:
                result = dict(connection)
                
                # Decrypt tokens
                if result.get("access_token"):
                    result["access_token"] = decrypt(result["access_token"])
                
                if result.get("refresh_token"):
                    result["refresh_token"] = decrypt(result["refresh_token"])
                
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error getting bank connections: {str(e)}")
            return []
    
    def update_connection_sync_time(self, connection_id, sync_time=None):
        """
        Update the last sync time for a connection
        
        Parameters:
        -----------
        connection_id: str
            Connection ID
        sync_time: str or datetime, optional
            Sync time, defaults to current time
            
        Returns:
        --------
        bool
            Whether the update was successful
        """
        try:
            if sync_time is None:
                sync_time = datetime.now().isoformat()
            elif isinstance(sync_time, datetime):
                sync_time = sync_time.isoformat()
            
            self.cursor.execute(
                "UPDATE bank_connections SET last_sync = ? WHERE connection_id = ?",
                (sync_time, connection_id)
            )
            
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating connection sync time: {str(e)}")
            return False
    
    def delete_bank_connection(self, connection_id):
        """
        Delete a bank connection and all related accounts and transactions
        
        Parameters:
        -----------
        connection_id: str
            Connection ID
            
        Returns:
        --------
        bool
            Whether the deletion was successful
        """
        try:
            # Get all accounts for this connection
            self.cursor.execute(
                "SELECT account_id FROM bank_accounts WHERE connection_id = ?",
                (connection_id,)
            )
            accounts = self.cursor.fetchall()
            
            # Delete transactions for these accounts
            for account in accounts:
                account_id = account[0]
                self.cursor.execute(
                    "DELETE FROM transactions WHERE account_id = ?",
                    (account_id,)
                )
            
            # Delete accounts
            self.cursor.execute(
                "DELETE FROM bank_accounts WHERE connection_id = ?",
                (connection_id,)
            )
            
            # Delete connection
            self.cursor.execute(
                "DELETE FROM bank_connections WHERE connection_id = ?",
                (connection_id,)
            )
            
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting bank connection: {str(e)}")
            return False
    
    def save_bank_account(self, account_info):
        """
        Save a bank account
        
        Parameters:
        -----------
        account_info: dict
            Account information dictionary with required fields:
            - account_id: str
            - connection_id: str
            - user_id: str
            - name: str
            - type: str
            - provider: str
            - balance: float
            
        Returns:
        --------
        bool
            Whether the account was saved
        """
        try:
            # Required fields
            required_fields = ["account_id", "connection_id", "user_id", "name", "type", "provider", "balance"]
            for field in required_fields:
                if field not in account_info:
                    logger.error(f"Missing required field for bank account: {field}")
                    return False
            
            # Set last_updated if not provided
            if "last_updated" not in account_info:
                account_info["last_updated"] = datetime.now().isoformat()
            elif isinstance(account_info["last_updated"], datetime):
                account_info["last_updated"] = account_info["last_updated"].isoformat()
            
            # Set currency if not provided
            if "currency" not in account_info:
                account_info["currency"] = "GBP"
            
            # Convert any extra data to JSON
            account_data = {k: v for k, v in account_info.items() if k not in required_fields + ["last_updated", "currency"]}
            account_data_json = json.dumps(account_data) if account_data else None
            
            # Save account
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO bank_accounts 
                (account_id, connection_id, user_id, name, type, provider, balance, currency, last_updated, account_data) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account_info["account_id"],
                    account_info["connection_id"],
                    account_info["user_id"],
                    account_info["name"],
                    account_info["type"],
                    account_info["provider"],
                    account_info["balance"],
                    account_info["currency"],
                    account_info["last_updated"],
                    account_data_json
                )
            )
            
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving bank account: {str(e)}")
            return False
    
    def get_bank_accounts(self, user_id=None, connection_id=None, account_id=None):
        """
        Get bank accounts for a user, connection, or specific account
        
        Parameters:
        -----------
        user_id: str, optional
            User ID
        connection_id: str, optional
            Connection ID
        account_id: str, optional
            Account ID
            
        Returns:
        --------
        list or dict
            List of account dictionaries or single account dictionary
        """
        try:
            if account_id:
                self.cursor.execute(
                    "SELECT * FROM bank_accounts WHERE account_id = ?",
                    (account_id,)
                )
                account = self.cursor.fetchone()
                if not account:
                    return None
                result = dict(account)
                
                # Parse account_data JSON if exists
                if result.get("account_data"):
                    try:
                        result["account_data"] = json.loads(result["account_data"])
                    except:
                        pass
                
                return result
            
            query = "SELECT * FROM bank_accounts"
            params = []
            
            if user_id:
                query += " WHERE user_id = ?"
                params.append(user_id)
                
                if connection_id:
                    query += " AND connection_id = ?"
                    params.append(connection_id)
            elif connection_id:
                query += " WHERE connection_id = ?"
                params.append(connection_id)
            
            query += " ORDER BY created_at DESC"
            
            self.cursor.execute(query, params)
            accounts = self.cursor.fetchall()
            
            results = []
            for account in accounts:
                result = dict(account)
                
                # Parse account_data JSON if exists
                if result.get("account_data"):
                    try:
                        result["account_data"] = json.loads(result["account_data"])
                    except:
                        pass
                
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error getting bank accounts: {str(e)}")
            return [] if not account_id else None
    
    def save_transaction(self, transaction_info):
        """
        Save a transaction
        
        Parameters:
        -----------
        transaction_info: dict
            Transaction information dictionary with required fields:
            - transaction_id: str
            - account_id: str
            - user_id: str
            - date: str or datetime
            - description: str
            - amount: float
            - type: str ('income', 'expense', or 'transfer')
            
        Returns:
        --------
        bool
            Whether the transaction was saved
        """
        try:
            # Required fields
            required_fields = ["transaction_id", "account_id", "user_id", "date", "description", "amount", "type"]
            for field in required_fields:
                if field not in transaction_info:
                    logger.error(f"Missing required field for transaction: {field}")
                    return False
            
            # Format date
            if isinstance(transaction_info["date"], datetime):
                transaction_info["date"] = transaction_info["date"].isoformat()
            
            # Set currency if not provided
            if "currency" not in transaction_info:
                transaction_info["currency"] = "GBP"
            
            # Set category if not provided
            if "category" not in transaction_info:
                transaction_info["category"] = "uncategorized"
            
            # Convert any extra data to JSON
            transaction_data = {k: v for k, v in transaction_info.items() if k not in required_fields + ["currency", "category"]}
            transaction_data_json = json.dumps(transaction_data) if transaction_data else None
            
            # Save transaction
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO transactions 
                (transaction_id, account_id, user_id, date, description, amount, currency, type, category, transaction_data) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_info["transaction_id"],
                    transaction_info["account_id"],
                    transaction_info["user_id"],
                    transaction_info["date"],
                    transaction_info["description"],
                    transaction_info["amount"],
                    transaction_info["currency"],
                    transaction_info["type"],
                    transaction_info["category"],
                    transaction_data_json
                )
            )
            
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving transaction: {str(e)}")
            return False
    
    def save_transactions(self, transactions_list):
        """
        Save multiple transactions
        
        Parameters:
        -----------
        transactions_list: list
            List of transaction dictionaries
            
        Returns:
        --------
        int
            Number of transactions saved
        """
        count = 0
        for transaction in transactions_list:
            if self.save_transaction(transaction):
                count += 1
        
        return count
    
    def get_transactions(self, user_id=None, account_id=None, start_date=None, end_date=None):
        """
        Get transactions for a user or account
        
        Parameters:
        -----------
        user_id: str, optional
            User ID
        account_id: str, optional
            Account ID
        start_date: str or datetime, optional
            Start date for filtering
        end_date: str or datetime, optional
            End date for filtering
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with transactions
        """
        try:
            query = "SELECT * FROM transactions"
            params = []
            
            conditions = []
            
            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)
            
            if account_id:
                conditions.append("account_id = ?")
                params.append(account_id)
            
            if start_date:
                if isinstance(start_date, datetime):
                    start_date = start_date.isoformat()
                conditions.append("date >= ?")
                params.append(start_date)
            
            if end_date:
                if isinstance(end_date, datetime):
                    end_date = end_date.isoformat()
                conditions.append("date <= ?")
                params.append(end_date)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY date DESC"
            
            self.cursor.execute(query, params)
            
            # Get column names
            columns = [desc[0] for desc in self.cursor.description]
            
            # Fetch all transactions
            transactions = self.cursor.fetchall()
            
            if not transactions:
                return pd.DataFrame(columns=columns)
            
            # Convert to list of dicts
            transactions_list = []
            for transaction in transactions:
                transaction_dict = dict(zip(columns, transaction))
                
                # Parse transaction_data JSON if exists
                if transaction_dict.get("transaction_data"):
                    try:
                        transaction_dict["transaction_data"] = json.loads(transaction_dict["transaction_data"])
                    except:
                        pass
                
                transactions_list.append(transaction_dict)
            
            # Create DataFrame
            df = pd.DataFrame(transactions_list)
            
            return df
        except Exception as e:
            logger.error(f"Error getting transactions: {str(e)}")
            return pd.DataFrame()
    
    def save_budget(self, user_id, category, amount, period="monthly"):
        """
        Save a budget for a category
        
        Parameters:
        -----------
        user_id: str
            User ID
        category: str
            Budget category
        amount: float
            Budget amount
        period: str, optional
            Budget period (monthly, weekly, yearly)
            
        Returns:
        --------
        bool
            Whether the budget was saved
        """
        try:
            # Ensure user exists
            self.create_user(user_id)
            
            # Save budget
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO budgets 
                (user_id, category, amount, period) 
                VALUES (?, ?, ?, ?)
                """,
                (user_id, category, amount, period)
            )
            
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving budget: {str(e)}")
            return False
    
    def get_budgets(self, user_id):
        """
        Get all budgets for a user
        
        Parameters:
        -----------
        user_id: str
            User ID
            
        Returns:
        --------
        dict
            Dictionary mapping categories to budget information
        """
        try:
            self.cursor.execute(
                "SELECT category, amount, period FROM budgets WHERE user_id = ?",
                (user_id,)
            )
            
            budgets = self.cursor.fetchall()
            
            result = {}
            for budget in budgets:
                result[budget[0]] = {
                    "amount": budget[1],
                    "period": budget[2]
                }
            
            return result
        except Exception as e:
            logger.error(f"Error getting budgets: {str(e)}")
            return {}
    
    def delete_budget(self, user_id, category):
        """
        Delete a budget
        
        Parameters:
        -----------
        user_id: str
            User ID
        category: str
            Budget category
            
        Returns:
        --------
        bool
            Whether the budget was deleted
        """
        try:
            self.cursor.execute(
                "DELETE FROM budgets WHERE user_id = ? AND category = ?",
                (user_id, category)
            )
            
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting budget: {str(e)}")
            return False
    
    def __del__(self):
        """Close the database connection on cleanup"""
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()