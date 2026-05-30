import sqlite3
import os

# Chemin de la base de données
db_path = os.path.join(os.path.dirname(__file__), 'campushub.db')

# Connexion
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Afficher toutes les tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("📋 Tables dans la base de données:")
for table in tables:
    print(f"  - {table[0]}")

print("\n" + "="*50)

# Afficher les utilisateurs
cursor.execute("SELECT id, email, first_name, last_name, year_level, role FROM users;")
users = cursor.fetchall()
print("\n👥 Utilisateurs:")
for user in users:
    print(f"  ID:{user[0]} | {user[1]} | {user[2]} {user[3]} | Niveau:{user[4]} | Rôle:{user[5]}")

print("\n" + "="*50)

# Afficher les mentors (M1 ou M2)
cursor.execute("SELECT id, email, first_name, last_name, year_level FROM users WHERE year_level IN ('M1', 'M2');")
mentors = cursor.fetchall()
print("\n🧑‍🏫 Mentors:")
for mentor in mentors:
    print(f"  ID:{mentor[0]} | {mentor[1]} | {mentor[2]} {mentor[3]} | Niveau:{mentor[4]}")

print("\n" + "="*50)

# Afficher les compétences
cursor.execute("""
    SELECT u.email, u.first_name, u.last_name, s.name, s.level 
    FROM user_skills s 
    JOIN users u ON u.id = s.user_id 
    LIMIT 20;
""")
skills = cursor.fetchall()
print("\n⚡ Compétences:")
for skill in skills:
    print(f"  {skill[1]} {skill[2]} | {skill[3]} | Niveau:{skill[4]}")

conn.close()