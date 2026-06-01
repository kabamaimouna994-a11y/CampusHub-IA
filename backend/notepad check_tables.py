import sqlite3
conn = sqlite3.connect('campushub.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = [t[0] for t in cursor.fetchall()]
print('Tables:', tables)
print('Certifications existe:', 'certifications' in tables)
conn.close()