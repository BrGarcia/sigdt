import sqlite3

def check_db():
    try:
        conn = sqlite3.connect('sigdt.db')
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        
        for table_tuple in tables:
            table = table_tuple[0]
            cursor.execute(f"PRAGMA table_info({table});")
            info = cursor.fetchall()
            print(f"\nTable info for {table}:")
            for col in info:
                print(f"  {col}")
        
        # Check alembic version
        try:
            cursor.execute("SELECT version_num FROM alembic_version;")
            version = cursor.fetchone()
            print(f"\nAlembic Version: {version}")
        except sqlite3.OperationalError:
            print("\nAlembic version table not found.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
