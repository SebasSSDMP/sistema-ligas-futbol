import os
os.environ['DATABASE_URL'] = 'sqlite:///./data/futbol.db'
exec(open('main.py').read())
print('Testing database initialization...')
init_db()
print('Database initialized successfully!')
conn = get_connection()
cursor = conn.cursor()
cursor.execute('SELECT 1')
result = cursor.fetchone()
print('Connection test:', result)
conn.close()
print('All tests passed!')