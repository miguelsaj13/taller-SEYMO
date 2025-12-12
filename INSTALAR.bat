@echo off
chcp 65001 > nul
title INSTALADOR TALLER SEYMO
color 0A
mode con: cols=70 lines=25
cls

echo ╔═══════════════════════════════════════════════╗
echo ║        INSTALADOR TALLER MECÁNICO SEYMO       ║
echo ╚═══════════════════════════════════════════════╝
echo.
echo Este instalador prepara todo para usar el programa.
echo SOLO se ejecuta LA PRIMERA VEZ en esta computadora.
echo.
echo.
echo 1. VERIFICANDO PYTHON...
echo --------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo NO se encontró Python instalado.
    echo.
    echo Necesitas instalar Python (gratis) para continuar.
    echo.
    echo Voy a abrir el navegador para descargarlo...
    echo.
    echo INSTRUCCIONES IMPORTANTES:
    echo 1. Descarga Python desde la página que se abrirá
    echo 2. Ejecuta el instalador descargado
    echo 3. MARCA la casilla: [✓] "Add Python to PATH"
    echo 4. Haz clic en "Install Now"
    echo 5. Cuando termine, REINICIA la computadora
    echo 6. Vuelve a ejecutar este instalador
    echo.
    pause
    start https://www.python.org/downloads/
    exit
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYVERSION=%%i"
echo ✓ Python %PYVERSION% encontrado
echo.
echo.
echo 2. INSTALANDO PROGRAMAS NECESARIOS...
echo --------------------------
echo Por favor espera, esto puede tomar unos minutos...
echo.

REM Instalar desde requirements.txt si existe
if exist requirements.txt (
    echo Usando lista de programas...
    pip install -r requirements.txt --quiet
) else (
    echo Instalando programas individualmente...
    pip install matplotlib --quiet
    pip install numpy --quiet
    pip install python-dateutil --quiet
)

echo ✓ Programas instalados correctamente
echo.
echo.
echo 3. CREANDO CARPETAS DEL SISTEMA...
echo --------------------------
if not exist "database" (
    mkdir database
    echo ✓ Carpeta para base de datos creada
)
if not exist "database\backups" mkdir database\backups

if not exist "reportes" (
    mkdir reportes
    echo ✓ Carpeta para reportes creada
)

if not exist "reportes_historicos" (
    mkdir reportes_historicos
    echo ✓ Carpeta para reportes históricos creada
)

if not exist "graficas" (
    mkdir graficas
    echo ✓ Carpeta para gráficas creada
)

echo.
echo ╔═══════════════════════════════════════════════╗
echo ║            ¡INSTALACIÓN COMPLETADA!          ║
echo ╚═══════════════════════════════════════════════╝
echo.
echo El sistema está listo para usar.
echo.
echo AHORA PUEDES:
echo 1. Cerrar esta ventana
echo 2. Ejecutar "EJECUTAR.bat" para usar el taller
echo.
echo NOTA: No necesitas ejecutar este instalador nunca más,
echo        solo si cambias de computadora.
echo.
pause