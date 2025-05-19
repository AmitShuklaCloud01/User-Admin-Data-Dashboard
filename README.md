# Cloudphysician Dashboard

A Streamlit dashboard application for BigQuery data with role-based access control, data access permissions, and comprehensive error handling.

## Project Overview

This dashboard provides a secure interface to BigQuery data with separate admin and user views. Admins can manage users and control access to specific tables and rows, while users can only view the data they have permission to access.

## Features

### Authentication System
- Secure login with username/password
- Password hashing with SHA-256
- Role-based access (admin/user)
- Session management

### Admin View
- View data from all BigQuery tables
- Manage users (add/delete)
- Control data access permissions at table and row level
- Monitor which users have access to specific data

### User View
- View only authorized data tables
- Data automatically filtered based on permissions
- Clear indication of applied filters

### Data Access Control
- **Table-Level Access**: Control which tables each user can access
- **Row-Level Filtering**: Apply SQL WHERE conditions to filter data for specific users
- **Access Management**: Dedicated interface for managing permissions

### Error Handling & Fallback System
- Robust error handling for BigQuery operations
- Graceful degradation to demo mode when tables don't exist
- Clear user feedback about connection status and errors
- Fallback to sample data when necessary

## Files & Structure

- **dashboard.py**: Main Streamlit application
  - Authentication and session management
  - User interface for both admin and user views
  - BigQuery data access and querying
  - Data access control implementation
  - Error handling and demo data generation

- **users.json**: User data storage (created automatically)
  - User credentials (username, hashed passwords)
  - User roles
  - Data access permissions

- **requirements.txt**: Dependencies file
  - Streamlit
  - Pandas
  - Google Cloud BigQuery

## Setup & Installation

1. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

2. **BigQuery Setup**:
   - Ensure you have Google Cloud credentials configured
   - Set up appropriate permissions for the BigQuery dataset
   - The application will automatically connect to BigQuery if credentials are available

3. **Run the Dashboard**:
   ```
   streamlit run dashboard.py
   ```

## Usage Instructions

### Initial Login
- Default admin credentials:
  - Username: `admin`
  - Password: `admin123`

### Admin Guide

1. **Data View**:
   - Browse all available tables
   - View all data without row-level restrictions

2. **User Management**:
   - Create new users with admin or regular user roles
   - Delete existing users (except the main admin account)
   - View a summary of users' data access

3. **Data Access Control**:
   - Select a user to manage
   - Grant access to specific tables
   - Define row-level filters using SQL WHERE clauses

### User Guide

1. **Login**:
   - Use credentials provided by an admin

2. **Data Access**:
   - Select from tables you have permission to view
   - View data that may be filtered based on admin-defined rules
   - See information about applied filters

## Technical Implementation

### Authentication
- User credentials stored in a local JSON file with hashed passwords
- Session state management using Streamlit's session_state

### BigQuery Integration
- Uses Google Cloud BigQuery client library
- Dynamic querying based on user permissions
- Table existence checking to prevent errors
- Error handling for all BigQuery operations

### Data Access Control
- Table permissions stored as lists in the users.json file
- Row filters stored as SQL WHERE clauses
- Filters applied directly to queries for maximum security

### Error Handling
- Exception handling for various BigQuery errors:
  - NotFound: When tables don't exist
  - BadRequest: For invalid queries (e.g., syntax errors)
  - Forbidden: For permission issues
- Fallback to demo data when errors occur

### Demo Mode
- Automatically activates when:
  - BigQuery connection fails
  - Required tables don't exist
  - Permissions are insufficient
- Provides realistic sample data for different table types
- Clearly indicated to users with informative messages

## Security Considerations

- Passwords are stored as SHA-256 hashes
- Row-level security implemented at the query level
- No direct access to the database for regular users
- Main admin account cannot be deleted

## Future Improvements

- Database-backed user management instead of JSON file
- More sophisticated authentication (OAuth, MFA)
- Enhanced audit logging of user actions
- Custom dashboards based on user roles
- Export capabilities for data

## Troubleshooting

If the dashboard shows "Demo Mode" or error messages about missing tables:
1. Verify your Google Cloud credentials are properly configured
2. Check that the referenced BigQuery dataset and tables exist
3. Ensure you have appropriate permissions for the dataset

The dashboard will continue to function in demo mode even without BigQuery access, allowing you to explore the interface and functionality. 