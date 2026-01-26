import os
import PyInstaller.__main__

# Nombre de tu archivo principal
nombre_archivo = "app.py"  # Cambia esto al nombre de tu archivo principal

# Rutas importantes
carpeta_actual = os.path.dirname(os.path.abspath(__file__))
archivo_principal = os.path.join(carpeta_actual, nombre_archivo)

# Opciones de PyInstaller
opciones = [
    archivo_principal,            # Archivo principal
    '--name=TallerSEYMO',         # Nombre del ejecutable
    '--onefile',                  # Un solo archivo .exe
    '--windowed',                 # Sin consola (para aplicaciones GUI)
    '--icon=icono.ico',           # Icono (opcional, crea o consigue uno)
    '--add-data=database;database',      # Incluir carpeta database
    '--add-data=reportes_historicos;reportes_historicos',  # Incluir carpeta reportes
    '--add-data=graficas;graficas',      # Incluir carpeta graficas
    '--clean',                    # Limpiar caché
    '--noconsole',                # Ocultar consola al ejecutar
]

try:
    PyInstaller.__main__.run(opciones)
    print("¡Ejecutable creado exitosamente!")
    print("Busca el archivo 'TallerSEYMO.exe' en la carpeta 'dist'")
except Exception as e:
    print(f"Error al crear el ejecutable: {e}")