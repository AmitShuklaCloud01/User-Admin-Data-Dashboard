# Technical Documentation: User-Admin Data Dashboard

## Architecture Overview

The User-Admin Data Dashboard is built on a Streamlit frontend with BigQuery integration. It uses a simple file-based user authentication and permission system.

```
                                ┌─────────────────┐
                                │                 │
                                │   Streamlit     │
                                │   Dashboard     │
                                │                 │
                                └────────┬────────┘
                                         │
                                         │
                 ┌─────────────────────┬─┴───┬─────────────────────┐
                 │                     │     │                     │
        ┌────────▼────────┐   ┌────────▼─────┴───┐       ┌─────────▼─────────┐
        │                 │   │                  │       │                   │
        │  Authentication │   │  BigQuery Data   │       │  Data Access      │
        │  System         │   │  Integration     │       │  Control System   │
        │                 │   │                  │       │                   │
        └────────┬────────┘   └────────┬─────────┘       └─────────┬─────────┘
                 │                     │                           │
                 │                     │                           │
        ┌────────▼────────┐   ┌────────▼─────────┐       ┌─────────▼─────────┐
        │                 │   │                  │       │                   │
        │  users.json     │   │  Google BigQuery │       │  Permissions      │
        │  (User Store)   │   │  (Data Store)    │       │  Management       │
        │                 │   │                  │       │                   │
        └─────────────────┘   └──────────────────┘       └───────────────────┘
```

## Implementation Details

### File Structure

- `dashboard.py`: Main application file containing all functionality
- `users.json`: Database of users and their permissions
- `requirements.txt`: Project dependencies

### Core Components

#### 1. Authentication System

The authentication system is implemented with the following functions:

- `initialize_users_file()`: Creates initial users.json with admin account
- `load_users()`: Loads user data from the JSON file
- `save_users()`: Persists changes to the users.json file
- `authenticate(username, password)`: Validates credentials using SHA-256 hashing
- `logout()`: Clears session state

#### 2. Session Management

Uses Streamlit's session_state to track:
- `st.session_state.authenticated`: Login status
- `st.session_state.username`: Current user's username
- `st.session_state.role`: User role (admin/user)

#### 3. BigQuery Integration

- Functions for data access:
  - `get_available_tables()`: Retrieves available tables from BigQuery
  - `table_exists()`: Checks if a specific table exists
  - `get_data()`: Fetches data based on user permissions
  - `get_table_data(table_name)`: Retrieves data from a specific table

- Error handling:
  - Graceful error handling for NotFound, BadRequest, and Forbidden exceptions
  - Automatic fallback to demo data when errors occur

#### 4. Data Access Control

Implemented with:
- Table-level permissions: Lists of accessible tables per user
- Row-level filtering: SQL WHERE clauses stored with user data
- Admin interface for permission management

#### 5. Demo Mode

Handles failure scenarios with:
- `get_demo_data(table_name)`: Generates realistic sample data
- Error notifications with detailed context
- Clear indication of demo mode operation

### Database Schema

The users.json file follows this structure:

```json
{
  "username": {
    "password": "hashed_password",
    "role": "admin|user",
    "data_access": {
      "tables": ["table1", "table2"],
      "row_filters": {
        "table1": "column = 'value'",
        "table2": "id IN (1, 2, 3)"
      }
    }
  }
}
```

### Security Implementation

1. **Password Security**:
   - Passwords are never stored in plain text
   - SHA-256 hashing is used for all password storage
   - Authentication compares hash values, not raw passwords

2. **Row-Level Security**:
   - Implemented directly in SQL queries with WHERE clauses
   - Filters applied server-side in BigQuery
   - Users unable to bypass or modify filters

3. **Access Control**:
   - Table access verified before any data is returned
   - Role-based permissions (admin vs. user)
   - Admin-only sections for user and permission management

## Error Handling Strategy

The application implements a comprehensive error handling strategy:

1. **Graceful Degradation**:
   - When BigQuery is unavailable, falls back to demo mode
   - When queries fail, attempts to simplify and retry

2. **User Feedback**:
   - Appropriate error messages with context
   - Warning banners for demo mode operation
   - Status indicators for connection health

3. **Recovery Mechanisms**:
   - When filters cause query failures, retries without filters
   - Non-blocking approach to allow continued app usage
   - Clear paths to resolve issues (e.g., contact admin)

## Code Patterns

### State Management

```python
# Initialize state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Update state
st.session_state.authenticated = True
st.session_state.username = username
```

### Error Handling Pattern

```python
try:
    # Attempt BigQuery operation
    return client.query(query).to_dataframe()
except NotFound:
    # Handle table not found
    return get_demo_data(table_name)
except Exception as e:
    # Generic error handling with fallback
    st.error(f"Error: {str(e)}")
    return get_demo_data(table_name)
```

### Permission Checking Pattern

```python
# Check if user has access to this table
if table_name not in data_access["tables"] and user_data["role"] != "admin":
    return pd.DataFrame({"message": [f"You don't have access to {table_name}."]})
```

## Development Guidelines

### Adding New Features

1. **New Table Support**:
   - No code changes needed; tables are dynamically discovered
   - Just add the table in BigQuery

2. **Adding New User Roles**:
   - Modify the role selection in `user_management()`
   - Add role-specific view functions
   - Update the main routing in `main()`

3. **Authentication Enhancements**:
   - Modify the `authenticate()` function
   - Update user schema in `initialize_users_file()`
   - Ensure backward compatibility for existing users

### Testing

Best practices for testing:
- Test with valid and invalid credentials
- Test with missing tables and invalid queries
- Test row-level filters with various conditions
- Verify demo data generation for all scenarios

## Deployment Considerations

### Production Readiness

For production deployment, consider:
1. Replacing file-based auth with a proper database
2. Adding HTTPS for secure credential transmission
3. Implementing audit logging for actions
4. Setting up proper IAM roles for BigQuery

### Scaling

The current design may have limitations:
- File-based user management doesn't scale to many users
- In-memory caching has limited capacity
- Consider database-backed solutions for larger deployments 