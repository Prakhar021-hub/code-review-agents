import sqlite3

def average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)

def get_user(username):
    conn = sqlite3.connect("app.db")
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return conn.execute(query).fetchone()

def save_password(password):
    with open("passwords.txt", "a") as f:
        f.write(password + "\n")