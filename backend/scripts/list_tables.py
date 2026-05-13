import sqlite3
c = sqlite3.connect('K:/Projects/UNIK/unik.db')
tables = [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Tables:', tables)
c.close()
