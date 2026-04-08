import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.connection import DatabaseConnection, get_db
from ui import App


def init_database():
    print("Inicializando base de datos...")
    db = DatabaseConnection()
    print(f"Base de datos lista: {db._connection}")
    return db


def main():
    print("=" * 50)
    print("Sistema de Gestion de Ligas de Futbol")
    print("=" * 50)
    
    db = init_database()
    
    print("\nIniciando aplicacion de escritorio...")
    app = App()
    app.mainloop()
    
    db.close()
    print("Aplicacion cerrada.")


if __name__ == "__main__":
    main()
