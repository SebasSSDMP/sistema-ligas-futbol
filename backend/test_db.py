import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import init_db, get_connection

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
