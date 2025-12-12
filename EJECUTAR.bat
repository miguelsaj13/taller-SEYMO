@echo off
chcp 65001 > nul
title TALLER MECÁNICO SEYMO - Sistema de Gestión
color 0F
mode con: cols=70 lines=20
cls

echo ╔═══════════════════════════════════════════════╗
echo ║        TALLER MECÁNICO SEYMO - SISTEMA       ║
echo ╚═══════════════════════════════════════════════╝
echo.
echo Iniciando sistema de gestión del taller...
echo Por favor espera mientras se prepara todo...
echo.
echo -------------------------------------------------
echo 1. VERIFICANDO ESTRUCTURA...
echo -------------------------------------------------

REM Crear carpetas si no existen (por si acaso)
if not exist "database" (
    echo Creando carpeta de base de datos...
    mkdir database
    mkdir database\backups
)

if not exist "reportes" (
    echo Creando carpeta de reportes...
    mkdir reportes
)

if not exist "reportes_historicos" (
    echo Creando carpeta de reportes históricos...
    mkdir reportes_historicos
)

if not exist "graficas" (
    echo Creando carpeta de gráficas...
    mkdir graficas
)

echo ✓ Estructura de carpetas verificada
echo.
echo -------------------------------------------------
echo 2. VERIFICANDO DEPENDENCIAS...
echo -------------------------------------------------

REM Verificar si están instaladas las librerías necesarias
python -c "import matplotlib" 2>nul
if errorlevel 1 (
    echo Error: No se encontró el sistema de gráficas
    echo.
    echo Solución: Ejecuta "INSTALAR.bat" primero
    echo.
    pause
    exit
)

python -c "import numpy" 2>nul
if errorlevel 1 (
    echo Error: No se encontró el sistema de cálculos
    echo.
    echo Solución: Ejecuta "INSTALAR.bat" primero
    echo.
    pause
    exit
)

echo ✓ Todas las dependencias están instaladas
echo.
echo -------------------------------------------------
echo 3. INICIANDO PROGRAMA PRINCIPAL...
echo -------------------------------------------------
echo.
echo El programa se abrirá en unos segundos...
echo Si aparece una ventana negra, es normal.
echo.
timeout /t 3 /nobreak > nul

REM Limpiar pantalla y ejecutar
cls
echo ╔═══════════════════════════════════════════════╗
echo ║        EJECUTANDO TALLER SEYMO...            ║
echo ╚═══════════════════════════════════════════════╝
echo.
echo Por favor espera...
echo.

REM Ejecutar el programa Python
python taller_sey.py

REM Cuando termine el programa Python
cls
echo ╔═══════════════════════════════════════════════╗
echo ║        PROGRAMA CERRADO                      ║
echo ╚═══════════════════════════════════════════════╝
echo.
echo Gracias por usar Taller SEYMO
echo.
echo Los datos se han guardado automáticamente.
echo.
echo Para volver a usar el programa:
echo 1. Ejecuta "EJECUTAR.bat" nuevamente
echo 2. O cierra esta ventana
echo.
pause