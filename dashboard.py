import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest, Forbidden
import hashlib
import json
import os

# Initialize session state variables if they don't exist
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'role' not in st.session_state:
    st.session_state.role = ""

# File to store user credentials
USERS_FILE = "users.json"

# Initialize BigQuery client
try:
    client = bigquery.Client()
except Exception as e:
    st.error(f"Failed to initialize BigQuery client: {str(e)}")
    client = None

# Get available tables in the BigQuery dataset
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_available_tables():
    if client is None:
        return []
    
    try:
        # Try to query the dataset to get actual tables
        dataset_ref = client.dataset('rawc_data', project='bigquery-basics-460109')
        tables = list(client.list_tables(dataset_ref))
        return [f"rawc_data.{table.table_id}" for table in tables]
    except Exception as e:
        # If dataset doesn't exist or any other error, return a default list for demo purposes
        st.warning(f"Could not fetch real tables from BigQuery: {str(e)}")
        st.info("Using demo tables for demonstration purposes.")
        return [
            "demo_table_1",
            "demo_table_2",
            "demo_table_3"
        ]

# Function to check if a table exists
def table_exists(table_name):
    if client is None:
        return False
        
    try:
        # Split table name into dataset and table
        parts = table_name.split('.')
        if len(parts) != 2:
            return False
            
        dataset_id, table_id = parts
        table_ref = client.dataset(dataset_id).table(table_id)
        client.get_table(table_ref)
        return True
    except NotFound:
        return False
    except Exception:
        return False

# Initialize the users file if it doesn't exist
def initialize_users_file():
    if not os.path.exists(USERS_FILE):
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        default_users = {
            "admin": {
                "password": admin_password, 
                "role": "admin",
                "data_access": {
                    "tables": get_available_tables(),  # Admin has access to all tables
                    "row_filters": {}  # No row filters for admin
                }
            },
        }
        with open(USERS_FILE, "w") as f:
            json.dump(default_users, f)

initialize_users_file()

# Function to load users from file
def load_users():
    if not os.path.exists(USERS_FILE):
        initialize_users_file()
    
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
        # Ensure all users have the data_access field
        for username, user_data in users.items():
            if "data_access" not in user_data:
                users[username]["data_access"] = {
                    "tables": [] if user_data["role"] != "admin" else get_available_tables(),
                    "row_filters": {}
                }
        return users

# Function to save users to file
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# Authentication function
def authenticate(username, password):
    users = load_users()
    if username in users:
        stored_password = users[username]["password"]
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if stored_password == hashed_password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]
            return True
    return False

# Logout function
def logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""

# Function to handle user data access management
def user_data_access_management():
    st.subheader("User Data Access Management")
    users = load_users()
    
    # Select user to manage
    non_admin_users = [u for u in users.keys() if users[u]["role"] != "admin" or u == "admin"]
    selected_user = st.selectbox("Select User", non_admin_users)
    
    if selected_user:
        st.write(f"Managing data access for: {selected_user}")
        
        # Get current access settings
        user_data = users[selected_user]
        if "data_access" not in user_data:
            user_data["data_access"] = {"tables": [], "row_filters": {}}
        
        # Table access management
        st.subheader("Table Access")
        available_tables = get_available_tables()
        
        # Create multiselect for tables
        selected_tables = st.multiselect(
            "Select tables user can access",
            available_tables,
            default=[t for t in user_data["data_access"]["tables"] if t in available_tables]
        )
        
        # Row-level filter management
        st.subheader("Row-Level Filters")
        st.write("Define conditions to filter data for this user (SQL WHERE clause conditions)")
        
        row_filters = {}
        for table in selected_tables:
            current_filter = user_data["data_access"]["row_filters"].get(table, "")
            filter_condition = st.text_input(
                f"Filter for {table}", 
                value=current_filter,
                help="SQL WHERE clause (e.g., 'column = value' or 'column IN (value1, value2)')"
            )
            if filter_condition:
                row_filters[table] = filter_condition
        
        # Save changes
        if st.button("Save Access Settings"):
            users[selected_user]["data_access"]["tables"] = selected_tables
            users[selected_user]["data_access"]["row_filters"] = row_filters
            save_users(users)
            st.success(f"Access settings for {selected_user} updated successfully!")

# Function to handle user management (admin only)
def user_management():
    st.subheader("User Management")
    users = load_users()
    
    # Display existing users with their data access
    st.write("Existing Users:")
    user_data = []
    for username, data in users.items():
        accessible_tables = len(data.get("data_access", {}).get("tables", []))
        has_filters = len(data.get("data_access", {}).get("row_filters", {})) > 0
        user_data.append({
            "Username": username, 
            "Role": data["role"],
            "Tables Access": accessible_tables,
            "Has Row Filters": "Yes" if has_filters else "No"
        })
    
    user_df = pd.DataFrame(user_data)
    st.dataframe(user_df)
    
    # Create new user
    st.subheader("Add New User")
    new_username = st.text_input("Username")
    new_password = st.text_input("Password", type="password")
    new_role = st.selectbox("Role", ["user", "admin"])
    
    if st.button("Add User"):
        if new_username and new_password:
            if new_username in users:
                st.error(f"User '{new_username}' already exists!")
            else:
                hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
                # Initialize with no data access for regular users, full access for admins
                data_access = {
                    "tables": get_available_tables() if new_role == "admin" else [],
                    "row_filters": {}
                }
                users[new_username] = {
                    "password": hashed_password, 
                    "role": new_role,
                    "data_access": data_access
                }
                save_users(users)
                st.success(f"User '{new_username}' added successfully!")
                st.experimental_rerun()
    
    # Delete user
    st.subheader("Delete User")
    delete_username = st.selectbox("Select User to Delete", list(users.keys()))
    if st.button("Delete User"):
        if delete_username != "admin":  # Prevent deleting the main admin account
            del users[delete_username]
            save_users(users)
            st.success(f"User '{delete_username}' deleted successfully!")
            st.experimental_rerun()
        else:
            st.error("Cannot delete the main admin account!")

# Generate demo data for when tables don't exist
def get_demo_data(table_name):
    if table_name == "demo_table_1":
        return pd.DataFrame({
            'patient_id': range(1, 11),
            'name': [f"Patient {i}" for i in range(1, 11)],
            'age': [20 + i*3 for i in range(10)],
            'condition': ['Stable']*5 + ['Critical']*3 + ['Recovering']*2
        })
    elif table_name == "demo_table_2":
        return pd.DataFrame({
            'doctor_id': range(1, 6),
            'name': [f"Dr. {chr(65+i)}" for i in range(5)],
            'specialty': ['Cardiology', 'Neurology', 'Pediatrics', 'Oncology', 'Emergency'],
            'patients': [15, 22, 18, 10, 30]
        })
    else:  # demo_table_3 or any other
        return pd.DataFrame({
            'hospital_id': range(1, 4),
            'name': ['General Hospital', 'Medical Center', 'Children\'s Hospital'],
            'beds': [250, 180, 120],
            'occupancy_rate': [0.85, 0.72, 0.64]
        })

# Define your query based on user access
def get_data():
    users = load_users()
    username = st.session_state.username
    user_data = users[username]
    
    # Admin can see all data
    if user_data["role"] == "admin":
        # For demo purposes, return demo data
        return get_demo_data("demo_table_1")
    
    # For regular users, check their data access permissions
    data_access = user_data.get("data_access", {"tables": [], "row_filters": {}})
    
    # If user has no access to any tables
    if not data_access["tables"]:
        return pd.DataFrame({"message": ["You don't have access to any data tables."]})
    
    # Find the first accessible table
    accessible_tables = [t for t in data_access["tables"] if t in get_available_tables()]
    
    if not accessible_tables:
        return pd.DataFrame({"message": ["None of your accessible tables currently exist."]})
    
    # Use the first table they have access to
    table_to_query = accessible_tables[0]
    
    # For demo purposes, return demo data
    return get_demo_data(table_to_query)

# Function to get specific table data (for user with multiple table access)
def get_table_data(table_name):
    if client is None:
        st.warning("BigQuery client is not available. Using demo data instead.")
        return get_demo_data(table_name)
    
    users = load_users()
    username = st.session_state.username
    user_data = users[username]
    data_access = user_data.get("data_access", {"tables": [], "row_filters": {}})
    
    # Check if user has access to this table
    if table_name not in data_access["tables"] and user_data["role"] != "admin":
        return pd.DataFrame({"message": [f"You don't have access to {table_name}."]})
    
    # Check if the table exists
    if not table_exists(table_name):
        st.warning(f"Table {table_name} does not exist in BigQuery. Using demo data instead.")
        return get_demo_data(table_name)
    
    try:
        # Apply row filter if exists
        row_filter = data_access["row_filters"].get(table_name, "")
        where_clause = f"WHERE {row_filter}" if row_filter else ""
        
        # Split table name into dataset and table
        parts = table_name.split('.')
        if len(parts) != 2:
            st.error(f"Invalid table name format: {table_name}. Expected format: dataset.table")
            return get_demo_data(table_name)
            
        dataset_id, table_id = parts
        
        query = f"""
        SELECT *
        FROM `bigquery-basics-460109.{dataset_id}.{table_id}`
        {where_clause}
        LIMIT 100
        """
        
        return client.query(query).to_dataframe()
    except NotFound:
        st.warning(f"Table {table_name} not found. Using demo data instead.")
        return get_demo_data(table_name)
    except BadRequest as e:
        st.error(f"Query error: {str(e)}")
        # If there's a syntax error in the filter, try without it
        if row_filter:
            st.warning("Trying query without filters...")
            try:
                query = f"""
                SELECT *
                FROM `bigquery-basics-460109.{dataset_id}.{table_id}`
                LIMIT 100
                """
                return client.query(query).to_dataframe()
            except Exception as inner_e:
                st.error(f"Still failed: {str(inner_e)}")
                return get_demo_data(table_name)
        return get_demo_data(table_name)
    except Forbidden as e:
        st.error(f"Access denied to BigQuery table: {str(e)}")
        return get_demo_data(table_name)
    except Exception as e:
        st.error(f"Error querying table {table_name}: {str(e)}")
        return get_demo_data(table_name)

# Main dashboard content for users
def user_view():
    st.title('User Dashboard')
    st.write(f"Welcome, {st.session_state.username}!")
    
    # Get user's accessible tables
    users = load_users()
    user_data = users[st.session_state.username]
    data_access = user_data.get("data_access", {"tables": [], "row_filters": {}})
    accessible_tables = [t for t in data_access["tables"] if t in get_available_tables()]
    
    if not accessible_tables:
        st.warning("You don't have access to any data tables. Please contact an administrator.")
        
        # Show demo data anyway for demonstration
        st.subheader("Demo Data (For Demonstration)")
        st.info("This is sample data shown for demonstration purposes only.")
        df = get_demo_data("demo_table_1")
        st.dataframe(df)
        return
    
    # Let user select which table to view
    selected_table = st.selectbox("Select table to view", accessible_tables)
    
    if selected_table:
        st.subheader(f'Data from {selected_table}')
        df = get_table_data(selected_table)
        
        # Check if the result is an error message
        if 'message' in df.columns and len(df.columns) == 1:
            st.warning(df['message'].iloc[0])
        else:
            st.dataframe(df)
            
            # Show applied filters if any
            row_filter = data_access["row_filters"].get(selected_table, "")
            if row_filter:
                st.info(f"Note: Data is filtered with condition: {row_filter}")

# Main dashboard content for admins
def admin_view():
    st.title('Admin Dashboard')
    st.write(f"Welcome, {st.session_state.username} (Admin)!")
    
    # Tabs for different admin sections
    tab1, tab2, tab3 = st.tabs(["Data View", "User Management", "Data Access Control"])
    
    with tab1:
        st.subheader('BigQuery Data Explorer')
        
        # Check if BigQuery client is available
        if client is None:
            st.error("BigQuery client could not be initialized. Check your credentials.")
            st.info("Showing demo data for demonstration purposes.")
        
        # Let admin select which table to view
        available_tables = get_available_tables()
        
        if not available_tables:
            st.warning("No tables found in BigQuery. Check your project and dataset configuration.")
            st.info("Showing demo tables for demonstration.")
            available_tables = ["demo_table_1", "demo_table_2", "demo_table_3"]
        
        selected_table = st.selectbox("Select table to view", available_tables)
        
        if selected_table:
            st.subheader(f'Data from {selected_table}')
            df = get_table_data(selected_table)
            
            # Check if the result is an error message
            if 'message' in df.columns and len(df.columns) == 1:
                st.warning(df['message'].iloc[0])
            else:
                st.dataframe(df)
    
    with tab2:
        user_management()
    
    with tab3:
        user_data_access_management()

# Main app layout
def main():
    # Sidebar with login/logout
    with st.sidebar:
        st.title("Dashboard Controls")
        
        if st.session_state.authenticated:
            st.write(f"Logged in as: {st.session_state.username}")
            st.write(f"Role: {st.session_state.role}")
            if st.button("Logout"):
                logout()
                st.experimental_rerun()
        else:
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                if authenticate(username, password):
                    st.success("Logged in successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password")
    
    # Main content
    if st.session_state.authenticated:
        if st.session_state.role == "admin":
            admin_view()
        else:
            user_view()
    else:
        st.title("Welcome to Dashboard")
        st.write("Please login to access the dashboard.")
        
        # Display connection status
        if client is None:
            st.error("BigQuery connection not available. The dashboard will operate in demo mode.")
        else:
            try:
                # Test the connection by listing datasets
                list(client.list_datasets())
                st.success("Connected to BigQuery successfully.")
            except Exception as e:
                st.error(f"BigQuery connection test failed: {str(e)}")
                st.info("The dashboard will operate in demo mode.")

if __name__ == "__main__":
    main()
