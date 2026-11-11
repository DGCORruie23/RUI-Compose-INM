import json
import os

def dividir_json(archivo_json, tamano_tramo, directorio_salida):
    # Leer el archivo JSON
    with open(archivo_json, 'r', encoding='utf-8') as f:
        datos = json.load(f)

    # Calcular el número de tramos
    total_elementos = len(datos)
    num_tramos = (total_elementos + tamano_tramo - 1) // tamano_tramo  # Redondeo hacia arriba

    # Crear el directorio de salida si no existe
    os.makedirs(directorio_salida, exist_ok=True)

    # Dividir y guardar cada tramo
    for i in range(num_tramos):
        inicio = i * tamano_tramo
        fin = inicio + tamano_tramo
        tramo = datos[inicio:fin]

        # Guardar el tramo como un nuevo archivo JSON
        nombre_archivo = os.path.join(directorio_salida, f'tramo_{i+1}.json')
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(tramo, f, ensure_ascii=False, indent=4)

        print(f'Tramo {i+1} guardado en {nombre_archivo}')

    print(f'División completada: {num_tramos} tramos creados.')

# Ejemplo de uso
archivo_json = 'dbRUIEexport_rescatepunto.json'  # Cambiar por el nombre de tu archivo
tamano_tramo = 20000
directorio_salida = 'tramos'
dividir_json(archivo_json, tamano_tramo, directorio_salida)