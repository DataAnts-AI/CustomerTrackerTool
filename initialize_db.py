import sqlite3

# Create the database file
conn = sqlite3.connect("tracyos_data.db")
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    name TEXT,
    deadline DATE,
    budget REAL,
    FOREIGN KEY (customer_id) REFERENCES customers (id)
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS hours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    hours REAL,
    date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id)
)
""")
conn.commit()
conn.close()

print("Database initialized successfully.")
