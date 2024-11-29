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

# Helper Functions
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

# Sidebar Navigation
menu = st.sidebar.selectbox("Menu", ["Home", "Add Customers", "Add Projects", "Log Hours", "View Reports", "Dashboard"])

if menu == "Home":
    st.write("Welcome to TracyOS!")
    st.write("Use the sidebar to navigate through the app.")

elif menu == "Add Customers":
    st.header("Add New Customer")
    customer_name = st.text_input("Customer Name")
    if st.button("Add Customer"):
        if customer_name:
            try:
                cursor.execute("INSERT INTO customers (name) VALUES (?)", (customer_name,))
                conn.commit()
                st.success(f"Customer '{customer_name}' added successfully!")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Customer name cannot be empty.")

elif menu == "Add Projects":
    st.header("Add New Project")
    customers = fetch_customers()
    if not customers.empty:
        customer_id = st.selectbox("Select Customer", customers["name"], index=0)
        customer_id = customers[customers["name"] == customer_id]["id"].values[0]
        project_name = st.text_input("Project Name")
        deadline = st.date_input("Deadline")
        budget = st.number_input("Budget (in $)", min_value=0.0, step=0.1)
        if st.button("Add Project"):
            if project_name:
                try:
                    cursor.execute("""
                        INSERT INTO projects (customer_id, name, deadline, budget)
                        VALUES (?, ?, ?, ?)
                    """, (customer_id, project_name, deadline, budget))
                    conn.commit()
                    st.success(f"Project '{project_name}' added successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Project name cannot be empty.")
    else:
        st.warning("No customers found. Add customers first.")

elif menu == "Log Hours":
    st.header("Log Hours")
    projects = fetch_projects()
    if not projects.empty:
        project_id = st.selectbox("Select Project", projects["name"], index=0)
        project_id = projects[projects["name"] == project_id]["id"].values[0]
        hours = st.number_input("Hours Worked", min_value=0.0, step=0.1)
        if st.button("Log Hours"):
            if hours > 0:
                try:
                    cursor.execute("INSERT INTO hours (project_id, hours) VALUES (?, ?)", (project_id, hours))
                    conn.commit()
                    st.success(f"Logged {hours} hours for the selected project.")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Hours must be greater than 0.")
    else:
        st.warning("No projects found. Add projects first.")

elif menu == "View Reports":
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
        st.warning("No data available.")

elif menu == "Dashboard":
    st.header("Dashboard")
    reports = fetch_reports()
    if not reports.empty:
        # Summary Chart
        st.subheader("Hours Logged by Customer")
        customer_summary = reports.groupby("customer")["total_hours"].sum().reset_index()
        fig, ax = plt.subplots()
        ax.bar(customer_summary["customer"], customer_summary["total_hours"], color="skyblue")
        ax.set_xlabel("Customer")
        ax.set_ylabel("Total Hours")
        ax.set_title("Hours Logged by Customer")
        st.pyplot(fig)
    else:
        st.warning("No data available to display.")
