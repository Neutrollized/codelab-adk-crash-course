import sqlite3

conn = sqlite3.connect("adk_sessions.db")
cur = conn.cursor()

# list tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cur.fetchall())

# peek at sessions
cur.execute("SELECT * FROM sessions;")
for row in cur.fetchall():
    print(row)

conn.close()
