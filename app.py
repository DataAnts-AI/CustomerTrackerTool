import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Initialize SQLite Database
conn = sqlite3.connect("tracyos_data.db")
cursor = conn.cursor()

# Create Tables
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

# Helper functions
def fetch_customers():
    return pd.read_sql_query("SELECT id, name FROM customers", conn)

def fetch_projects():
    return pd.read_sql_query("""
        SELECT p.id, p.name, p.deadline, p.budget, c.name AS customer
        FROM projects p
        JOIN customers c ON p.customer_id = c.id
    """, conn)

def fetch_reports():
    return pd.read_sql_query("""
        SELECT c.name AS customer, p.name AS project, SUM(h.hours) AS total_hours, MAX(h.date) AS last_logged
        FROM hours h
        JOIN projects p ON h.project_id = p.id
        JOIN customers c ON p.customer_id = c.id
        GROUP BY p.id
    """, conn)

# Streamlit UI
st.title("TracyOS - Customer & Project Management")

menu = st.sidebar.radio("Navigate", ["View & Track", "Add Customers & Projects", "Reports", "Dashboard"])

# Tab 1: View & Track Customers and Projects
if menu == "View & Track":
    st.header("Customer & Project Tracking")
    projects = fetch_projects()
    if not projects.empty:
        st.dataframe(projects)
        project_id = st.selectbox("Select Project to Log Hours", projects["name"])
        project_row = projects[projects["name"] == project_id]
        project_id = project_row["id"].values[0]
        
        hours = st.number_input("Enter Hours Worked", min_value=0.0, step=0.1)
        if st.button("Log Hours"):
            cursor.execute("INSERT INTO hours (project_id, hours) VALUES (?, ?)", (project_id, hours))
            conn.commit()
            st.success(f"{hours} hours logged for project: {project_row['name'].values[0]}")
    else:
        st.warning("No projects found. Add projects first.")

# Tab 2: Add Customers and Projects
elif menu == "Add Customers & Projects":
    st.header("Add New Customer or Project")
    customer_name = st.text_input("Customer Name")
    if st.button("Add Customer"):
        try:
            cursor.execute("INSERT INTO customers (name) VALUES (?)", (customer_name,))
            conn.commit()
            st.success(f"Customer '{customer_name}' added successfully!")
        except sqlite3.IntegrityError:
            st.error(f"Customer '{customer_name}' already exists.")

    st.subheader("Add New Project")
    customers = fetch_customers()
    if not customers.empty:
        customer_id = st.selectbox("Select Customer", customers["name"])
        customer_row = customers[customers["name"] == customer_id]
        customer_id = customer_row["id"].values[0]

        project_name = st.text_input("Project Name")
        deadline = st.date_input("Deadline")
        budget = st.number_input("Budget (in $)", min_value=0.0, step=0.1)
        if st.button("Add Project"):
            cursor.execute("""
                INSERT INTO projects (customer_id, name, deadline, budget)
                VALUES (?, ?, ?, ?)
            """, (customer_id, project_name, deadline, budget))
            conn.commit()
            st.success(f"Project '{project_name}' added successfully!")
    else:
        st.warning("No customers found. Add customers first.")

# Tab 3: Reports
elif menu == "Reports":
    st.header("Reports")
    reports = fetch_reports()
    if not reports.empty:
        st.dataframe(reports)
        st.download_button(
            "Download CSV",
            data=reports.to_csv(index=False),
            file_name="reports.csv",
            mime="text/csv"
        )
    else:
        st.warning("No report data available.")

# Tab 4: Dashboard
elif menu == "Dashboard":
    st.header("Summary Dashboard")
    reports = fetch_reports()
    if not reports.empty:
        st.subheader("Total Hours by Customer")
        customer_summary = reports.groupby("customer")["total_hours"].sum().reset_index()
        fig, ax = plt.subplots()
        ax.bar(customer_summary["customer"], customer_summary["total_hours"], color="skyblue")
        ax.set_title("Total Hours by Customer")
        ax.set_xlabel("Customer")
        ax.set_ylabel("Total Hours")
        st.pyplot(fig)
    else:
        st.warning("No data to display.")

# Close database connection
conn.close()
