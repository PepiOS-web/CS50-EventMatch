import sqlite3

def main():
    # Nombre del archivo de base de datos
    db_filename = "eventmatch.db"

    # Conectar (si no existe, lo crea)
    conn = sqlite3.connect(db_filename)

    # Leer el esquema desde schema.sql
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema = f.read()

    # Ejecutar todas las sentencias SQL del schema
    conn.executescript(schema)

    # Guardar cambios y cerrar
    conn.commit()
    conn.close()

    print(f"Base de datos '{db_filename}' creada correctamente a partir de schema.sql.")

if __name__ == "__main__":
    main()
