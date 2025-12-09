import csv
import io
import re

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import render


def validar_fila(row, index):
    """
    row: lista con las 5 columnas de la fila
    index: número de fila (para mostrar al usuario, empezamos en 1)
    """
    errores = []

    # Funcion para que pueda asegurar que tiene exactamente 5 columnas (ya lo validamos antes, pero por si acaso)
    if len(row) != 5:
        errores.append({
            "fila": index,
            "columna": "N/A",
            "mensaje": f"La fila tiene {len(row)} columnas, se esperaban 5."
        })
        return errores

    col1, col2, col3, col4, col5 = row

    # Columna 1: enteros entre 3 y 10 caracteres :D
    col1_str = col1.strip()
    if not col1_str.isdigit():
        errores.append({
            "fila": index,
            "columna": 1,
            "mensaje": "La columna 1 debe contener solo números enteros."
        })
    else:
        if not (3 <= len(col1_str) <= 10):
            errores.append({
                "fila": index,
                "columna": 1,
                "mensaje": "La columna 1 debe tener entre 3 y 10 dígitos."
            })

    # Columna 2: correo electrónico @
    col2_str = col2.strip()
    try:
        validate_email(col2_str)
    except ValidationError:
        errores.append({
            "fila": index,
            "columna": 2,
            "mensaje": "La columna 2 debe ser un correo electrónico válido."
        })

    # Columna 3: “CC” o “TI”
    col3_str = col3.strip().upper()
    if col3_str not in ["CC", "TI"]:
        errores.append({
            "fila": index,
            "columna": 3,
            "mensaje": "La columna 3 solo permite los valores 'CC' o 'TI'."
        })

    # Columna 4: valores entre 500000 y 1500000
    col4_str = col4.strip()
    if not col4_str.isdigit():
        errores.append({
            "fila": index,
            "columna": 4,
            "mensaje": "La columna 4 debe ser un número entero."
        })
    else:
        valor = int(col4_str)
        if not (500000 <= valor <= 1500000):
            errores.append({
                "fila": index,
                "columna": 4,
                "mensaje": "La columna 4 debe estar entre 500000 y 1500000."
            })

    # Columna 5: cualquier valor -> sin validación

    return errores


def upload_file(request):
    context = {
        "errores": [],
        "mensaje_exito": "",
        "stats": None,
    }

    if request.method == "POST":
        archivo = request.FILES.get("archivo")

        if not archivo:
            context["errores"].append({
                "fila": "N/A",
                "columna": "N/A",
                "mensaje": "Debe seleccionar un archivo CSV."
            })
            return render(request, "validador/upload.html", context)

        # Comprobar extensión básica
        if not archivo.name.lower().endswith(".csv"):
            context["errores"].append({
                "fila": "N/A",
                "columna": "N/A",
                "mensaje": "El archivo debe ser un CSV."
            })
            return render(request, "validador/upload.html", context)

        # Leer el contenido del archivo y tratar de decodificarlo
        contenido = archivo.read()
        try:
            # Primero intentamos UTF-8
            data = contenido.decode("utf-8")
        except UnicodeDecodeError:
            try:
                # Si falla, intentamos ISO-8859-1 / latin-1 (típico de Excel en Windows)
                data = contenido.decode("latin-1")
            except UnicodeDecodeError:
                context["errores"].append({
                    "fila": "N/A",
                    "columna": "N/A",
                    "mensaje": "No se pudo leer el archivo. Intente guardarlo como CSV en formato UTF-8."
                })
                return render(request, "validador/upload.html", context)


        f = io.StringIO(data)
        reader = csv.reader(f)

        errores_totales = []
        fila_num = 0
        filas_con_error = set()

        for row in reader:
            fila_num += 1

            # Validar que tenga exactamente 5 columnas
            if len(row) != 5:
                errores_totales.append({
                    "fila": fila_num,
                    "columna": "N/A",
                    "mensaje": f"La fila tiene {len(row)} columnas, se esperaban 5."
                })
                filas_con_error.add(fila_num)
                continue

            errores_fila = validar_fila(row, fila_num)
            if errores_fila:
                filas_con_error.add(fila_num)
                errores_totales.extend(errores_fila)

        total_filas = fila_num
        total_filas_error = len(filas_con_error)
        total_filas_ok = total_filas - total_filas_error

        context["stats"] = {
            "total": total_filas,
            "ok": total_filas_ok,
            "con_error": total_filas_error,
        }

        if errores_totales:
            context["errores"] = errores_totales
        else:
            context["mensaje_exito"] = "Archivo validado correctamente."

    return render(request, "validador/upload.html", context)