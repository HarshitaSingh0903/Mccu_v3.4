import sqlite3
import bcrypt, os

def createUserDb():
    # Create a SQLite database (or connect to an existing one)
    conn = sqlite3.connect("user_credentials.db")
    cursor = conn.cursor()

    # Create a table to store user information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def defalut_db(username, password):
    createUserDb()
    conn = sqlite3.connect("user_credentials.db")
    cursor = conn.cursor()
    # Hash the password using bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        # Insert the user's information into the database
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        # print("User registered successfully.")
        createStatus="User registered successfully."
    except sqlite3.IntegrityError:
        # Handle the case where the username is already taken
        createStatus="Username is already taken. Please choose another username."
        # print("Username is already taken. Please choose another username.")
    conn.close()
    return createStatus

def register_user(username, password):
    # Connect to the database
    conn = sqlite3.connect("user_credentials.db")
    cursor = conn.cursor()
    # Hash the password using bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        # Insert the user's information into the database
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        # print("User registered successfully.")
        createStatus="User registered successfully."
    except sqlite3.IntegrityError:
        # Handle the case where the username is already taken
        createStatus="Username is already taken. Please choose another username."
        # print("Username is already taken. Please choose another username.")
    conn.close()
    return createStatus

# register_user('example', 'secure_password')
def check_password(username, provided_password):
    # Connect to the database
    conn = sqlite3.connect("user_credentials.db")
    cursor = conn.cursor()

    # Retrieve the hashed password for the given username
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    stored_password = cursor.fetchone()

    if stored_password:
        stored_password = stored_password[0]
        
        # Check if the provided password matches the stored hashed password
        if bcrypt.checkpw(provided_password.encode('utf-8'), stored_password):
            status= 'correct'
            # print("Password is correct. User authenticated.")
        else:
            status= 'Incorrect password'
            # print("Incorrect password. Authentication failed.")
    else:
        status= 'Incorrect Username'
        # print("Username not found. Authentication failed.")

    conn.close()
    return status

# Example usage
# check_password('example', 'bjuiklonjui')

def reset_password(username, new_password):
    # Connect to the database
    conn = sqlite3.connect("user_credentials.db")
    cursor = conn.cursor()

    # Check if the provided username exists in the database
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user_id = cursor.fetchone()

    if user_id:
        # Hash the new password using bcrypt
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        try:
            # Update the user's password in the database
            cursor.execute('UPDATE users SET password = ? WHERE username = ?', (hashed_password, username))
            conn.commit()
            # print(f"Password reset successful for user: {username}")
            # print(f"New password: {new_password}")
            newPassStatus= 'Password reset successful'
        except sqlite3.Error:
            # print("An error occurred while resetting the password.")
            newPassStatus= 'An error occurred while resetting the password.'
        return newPassStatus
    else:
        newPassStatus = ' not found in the database. Password reset failed.'
    conn.close()
    return newPassStatus

# Example usage
# reset_password('example', '123')
def delete_user(username):
    # Connect to the database
    conn = sqlite3.connect( "user_credentials.db")
    cursor = conn.cursor()

    try:
        # Delete the user from the database
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        conn.commit()
        print(f"User '{username}' deleted successfully.")
    except sqlite3.Error:
        print(f"An error occurred while deleting user '{username}'.")

    conn.close()

# Example usage
# delete_user('example')
import sqlite3

def empty_database():
    # Connect to the database
    conn = sqlite3.connect( "user_credentials.db")
    cursor = conn.cursor()

    try:
        # Delete all user records in the 'users' table
        cursor.execute('DELETE FROM users')
        conn.commit()
        print("Database emptied successfully.")
    except sqlite3.Error:
        print("An error occurred while emptying the database.")

    conn.close()

# Example usage
# empty_database()


