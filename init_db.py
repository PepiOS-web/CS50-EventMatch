import sqlite3

def main():
     # Database file name
    db_filename = "eventmatch.db"

    # Connect (if it does not exist, create it)
    conn = sqlite3.connect(db_filename)

    # Read the schema from schema.sql
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema = f.read()

    # Ejecutar todas las sentencias SQL del schemar el esquema desde schema.sql
    conn.executescript(schema)

    # Save changes and close
    conn.commit()
    conn.close()

    print(f"Base de datos '{db_filename}' creada correctamente a partir de schema.sql.")

if __name__ == "__main__":
    main()
