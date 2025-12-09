import os
import re
import sqlite3
from PyPDF2 import PdfReader

# Expresión regular entregada en la prueba
PATRON_CUFE = re.compile(r"(\b([0-9a-fA-F]\n*){95,100}\b)")


def crear_tabla(conn):
    """Crea la tabla si no existe."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_archivo TEXT NOT NULL,
            numero_paginas INTEGER NOT NULL,
            cufe TEXT,
            peso_bytes INTEGER NOT NULL
        )
        """
    )
    conn.commit()


def procesar_pdf(ruta_pdf: str, conn: sqlite3.Connection):
    """Lee un PDF, extrae el CUFE y lo guarda en la base de datos."""
    nombre_archivo = os.path.basename(ruta_pdf)
    peso_bytes = os.path.getsize(ruta_pdf)  # tamaño en bytes

    reader = PdfReader(ruta_pdf)
    numero_paginas = len(reader.pages)

    texto_completo = ""
    for page in reader.pages:
        texto_completo += page.extract_text() or ""

    # Buscar el CUFE con la expresión regular
    match = PATRON_CUFE.search(texto_completo)
    if match:
        cufe = match.group(0).replace("\n", "")
    else:
        cufe = None  # o "NO_ENCONTRADO" si quieres texto

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO facturas (nombre_archivo, numero_paginas, cufe, peso_bytes)
        VALUES (?, ?, ?, ?)
        """,
        (nombre_archivo, numero_paginas, cufe, peso_bytes),
    )
    conn.commit()


def main():
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_facturas = os.path.join(ruta_base, "facturas")

    if not os.path.isdir(ruta_facturas):
        print(f"La carpeta 'facturas' no existe en: {ruta_facturas}")
        return

    # Crear / abrir la base de datos SQLite
    ruta_db = os.path.join(ruta_base, "cufes.db")
    conn = sqlite3.connect(ruta_db)

    crear_tabla(conn)

    archivos_pdf = [
        f for f in os.listdir(ruta_facturas)
        if f.lower().endswith(".pdf")
    ]

    if not archivos_pdf:
        print("No se encontraron archivos PDF en la carpeta 'facturas'.")
        conn.close()
        return

    for archivo in archivos_pdf:
        ruta_pdf = os.path.join(ruta_facturas, archivo)
        print(f"Procesando: {ruta_pdf}")
        try:
            procesar_pdf(ruta_pdf, conn)
        except Exception as e:
            print(f"Error procesando '{archivo}': {e}")

    conn.close()
    print(f"Proceso finalizado. Datos almacenados en {ruta_db}")


if __name__ == "__main__":
    main()
