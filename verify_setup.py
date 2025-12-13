import os
import sqlite3
# verify_setup.py imports
from src.components.explorer import SchemaDiscovery
from src.components.executor import SQLAgent

DB_PATH = "test_data.db"
DB_URL = f"sqlite:///{DB_PATH}"

def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT, active BOOLEAN)")
    cursor.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL, order_date TEXT, ship_date TEXT)")
    
    # Insert data
    cursor.execute("INSERT INTO users VALUES (1, 'Alice', 'Madrid', 1)")
    cursor.execute("INSERT INTO users VALUES (2, 'Bob', 'Barcelona', 0)")
    cursor.execute("INSERT INTO orders VALUES (101, 1, 100.50, '2023-01-01', '2023-01-05')")
    
    conn.commit()
    conn.close()
    print("Test DB created.")

def run_verification():
    setup_db()
    
    print("\n--- Testing Schema Discovery ---")
    explorer = SchemaDiscovery()
    explorer.run(DB_URL)
    
    print("\n--- Testing SQL Agent ---")
    # Initialize with default Ollama model 'llama3:8b'
    agent = SQLAgent(db_url=DB_URL, model_path="llama3:8b")
    
    # Test 1: Normal Query
    print("\n[Query 1] 'Show me users in Madrid'")
    r1 = agent.handle_query("Show me users in Madrid")
    print(f"Result: {r1}")
    
    # Test 2: Ambiguity
    print("\n[Query 2] 'Show orders by date'")
    r2 = agent.handle_query("Show orders by date")
    print(f"Result: {r2}")
    
    # Test 3: Unsafe Query
    print("\n[Query 3] 'DROP TABLE users'")
    r3 = agent.handle_query("DROP TABLE users")
    print(f"Result: {r3}")

if __name__ == "__main__":
    run_verification()
