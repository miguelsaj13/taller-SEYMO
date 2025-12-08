# ============================================================================
# TALLER SEYMO - SISTEMA DE GESTIÓN PARA TALLER MECÁNICO
# VERSIÓN CON RECORDATORIOS INTELIGENTES MEJORADOS
# ============================================================================

# Primero importo todas las librerías que voy a necesitar
import sqlite3
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import warnings
import sys
import numpy as np
from typing import Optional, Dict, List, Tuple

# Apago las advertencias que no me interesan
warnings.filterwarnings('ignore')

# ============================================================================
# FUNCIÓN PARA CREAR CARPETAS
# ============================================================================
def crear_estructura_carpetas():
    """Esta función crea las carpetas que necesita el programa para funcionar"""
    try:
        # Defino las carpetas que necesito
        carpetas = ['database', 'database/backups', 'reportes', 'graficas']
        
        # Recorro cada carpeta y si no existe, la creo
        for carpeta in carpetas:
            if not os.path.exists(carpeta):
                os.makedirs(carpeta)
        
        return True
    except Exception as e:
        print(f"Error creando carpetas: {e}")
        return False

# ============================================================================
# INICIO DEL PROGRAMA
# ============================================================================
# Primero creo las carpetas necesarias
if not crear_estructura_carpetas():
    print("No se pudieron crear las carpetas. Saliendo...")
    sys.exit(1)

print("✅ Estructura de carpetas lista")

# ============================================================================
# CLASE PARA MANEJAR LA BASE DE DATOS
# ============================================================================
class DatabaseManager:
    """Esta clase se encarga de todo lo relacionado con la base de datos"""
    
    def __init__(self, db_path: str = 'database/taller.db'):
        # Defino la ruta de la base de datos
        self.db_path = db_path
        self.conn = None
        # Inicializo la base de datos
        self._initialize_database()
    
    def _initialize_database(self):
        """Inicializa la base de datos y crea las tablas si no existen"""
        try:
            # Creo la conexión a la base de datos
            self.conn = self._create_connection()
            if self.conn is not None:
                # Creo las tablas necesarias
                self.create_tables()
                print("✅ Base de datos lista")
            else:
                raise sqlite3.Error("No se pudo conectar a la base de datos")
        except sqlite3.Error as e:
            print(f"❌ Error: {e}")
            raise
    
    def _create_connection(self):
        """Crea la conexión con la base de datos"""
        try:
            # Conecto a la base de datos SQLite
            conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            # Activo las claves foráneas
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as e:
            print(f"❌ Error conectando: {e}")
            return None
    
    def create_tables(self):
        """Crea todas las tablas necesarias en la base de datos"""
        if self.conn is None:
            raise sqlite3.Error("No hay conexión a la base de datos")
        
        cursor = self.conn.cursor()
        
        try:
            # Tabla de clientes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    telefono TEXT UNIQUE,
                    nit TEXT UNIQUE
                )
            ''')
            
            # Tabla de vehículos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehiculos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    marca TEXT NOT NULL,
                    modelo TEXT NOT NULL,
                    año INTEGER,
                    placa TEXT UNIQUE,
                    color TEXT,
                    proximo_mantenimiento DATE,
                    kilometraje_ultimo_mantenimiento REAL,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                )
            ''')
            
            # Tabla de empleados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS empleados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    telefono TEXT UNIQUE
                )
            ''')
            
            # Tabla de órdenes de trabajo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ordenes_trabajo (
                    id INTEGER PRIMARY KEY,
                    vehiculo_id INTEGER,
                    empleado_id INTEGER,
                    fecha_fin DATE,
                    descripcion_trabajo TEXT,
                    tipo_servicio TEXT,
                    horas_trabajadas REAL,
                    costo_repuestos REAL,
                    costo_mano_obra REAL,
                    precio_final REAL,
                    kilometraje REAL,
                    unidad_kilometraje TEXT DEFAULT 'km',
                    FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                    FOREIGN KEY (empleado_id) REFERENCES empleados(id)
                )
            ''')
            
            # Verifico y actualizo las tablas si es necesario
            self._verificar_y_actualizar_tablas()
            self.conn.commit()
            print("✅ Tablas creadas correctamente")
            
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"❌ Error creando tablas: {e}")
            raise
    
    def _verificar_y_actualizar_tablas(self):
        """Verifica si las tablas tienen todas las columnas necesarias"""
        cursor = self.conn.cursor()
        
        try:
            print("🔄 Verificando tablas...")
            
            # Verifico la tabla de clientes
            cursor.execute("PRAGMA table_info(clientes)")
            columnas_clientes = [col[1] for col in cursor.fetchall()]
            
            # Si falta la columna NIT, la agrego
            if 'nit' not in columnas_clientes:
                print("🔄 Agregando columna 'nit' a clientes...")
                cursor.execute('ALTER TABLE clientes ADD COLUMN nit TEXT UNIQUE')
                print("✅ Columna 'nit' agregada")
            
            self.conn.commit()
            print("✅ Tablas actualizadas")
            
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"❌ Error al actualizar tablas: {e}")
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Ejecuta una consulta SQL y devuelve el cursor"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor
    
    def commit(self):
        """Guarda los cambios en la base de datos"""
        self.conn.commit()

# ============================================================================
# CLASE PARA VALIDAR DATOS
# ============================================================================
class Validator:
    """Esta clase valida que los datos ingresados sean correctos"""
    
    @staticmethod
    def validar_numero(valor: str, tipo: str = "entero") -> Optional[float]:
        """Valida que un valor sea un número"""
        try:
            if not valor.strip():
                return None
            if tipo == "entero":
                return int(valor)
            elif tipo == "decimal":
                return float(valor)
            else:
                return valor
        except ValueError:
            return None
    
    @staticmethod
    def validar_telefono(telefono: str) -> Optional[str]:
        """Valida que un teléfono tenga solo números y longitud correcta"""
        if telefono is None or telefono.strip() == "":
            return None
        
        # Quito todo lo que no sea número
        telefono_limpio = ''.join(filter(str.isdigit, telefono))
        
        # El teléfono debe tener entre 7 y 15 dígitos
        if len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
            return None
        
        return telefono_limpio
    
    @staticmethod
    def validar_nit(nit: str) -> Optional[str]:
        """Valida que el NIT tenga formato correcto"""
        if nit is None or nit.strip() == "":
            return None
        
        # Permito números, letras, guiones y espacios
        nit_limpio = ''.join(filter(lambda c: c.isalnum() or c in '- ', nit))
        
        # El NIT debe tener entre 3 y 20 caracteres
        if len(nit_limpio) < 3 or len(nit_limpio) > 20:
            return None
        
        return nit_limpio
    
    @staticmethod
    def validar_fecha(fecha_str: str, permitir_futuro: bool = True, permitir_pasado: bool = True) -> Optional[datetime.date]:
        """Valida que una fecha sea correcta"""
        try:
            if not fecha_str.strip():
                return None
                
            # Si es un número, lo interpreto como días desde hoy
            if fecha_str.isdigit():
                dias = int(fecha_str)
                fecha = datetime.now() + timedelta(days=dias)
            else:
                # Si es texto, lo convierto a fecha
                # Intentar diferentes formatos
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y'):
                    try:
                        fecha = datetime.strptime(fecha_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return None
            
            hoy = datetime.now().date()
            fecha_date = fecha.date()
            
            # La fecha debe ser razonable (después del año 2000)
            if fecha_date < datetime(2000, 1, 1).date():
                return None
            
            # No permito fechas muy futuras (más de 1 año)
            if fecha_date > hoy + timedelta(days=365):
                return None
                
            # Validaciones adicionales según parámetros
            if not permitir_futuro and fecha_date > hoy:
                return None
                
            if not permitir_pasado and fecha_date < hoy:
                return None
            
            return fecha_date
            
        except ValueError:
            return None
    
    @staticmethod
    def validar_año_vehiculo(año: int) -> bool:
        """Valida que el año del vehículo sea razonable"""
        año_actual = datetime.now().year
        # El año debe estar entre 1900 y el año actual + 2
        return 1900 <= año <= año_actual + 2

# ============================================================================
# CLASE PARA MANEJAR CLIENTES
# ============================================================================
class ClienteManager:
    """Gestiona todo lo relacionado con clientes"""
    
    def __init__(self, db_manager: DatabaseManager, validator: Validator):
        self.db = db_manager
        self.validator = validator
    
    def agregar_cliente(self, nombre: str, telefono: Optional[str] = None, nit: Optional[str] = None) -> Optional[int]:
        """Agrega un nuevo cliente a la base de datos"""
        try:
            cursor = self.db.execute_query(
                'INSERT INTO clientes (nombre, telefono, nit) VALUES (?, ?, ?)', 
                (nombre, telefono, nit)
            )
            self.db.commit()
            print(f"✅ Cliente '{nombre}' agregado con ID: {cursor.lastrowid}")
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            # Manejo errores de datos duplicados
            if "telefono" in str(e):
                raise Exception("Ya existe un cliente con ese teléfono")
            elif "nit" in str(e):
                raise Exception("Ya existe un cliente con ese NIT")
            else:
                raise Exception("Error en la base de datos")
    
    def cliente_existe(self, cliente_id: int) -> bool:
        """Verifica si un cliente existe"""
        cursor = self.db.execute_query('SELECT id FROM clientes WHERE id = ?', (cliente_id,))
        return cursor.fetchone() is not None
    
    def buscar_cliente_por_nombre(self, nombre_buscar: str) -> List[Tuple]:
        """Busca clientes por nombre"""
        cursor = self.db.execute_query(
            'SELECT id, nombre, telefono, nit FROM clientes WHERE nombre LIKE ? ORDER BY nombre',
            (f'%{nombre_buscar}%',)
        )
        return cursor.fetchall()
    
    def obtener_todos_clientes(self) -> List[Tuple]:
        """Obtiene todos los clientes"""
        cursor = self.db.execute_query(
            'SELECT id, nombre, telefono, nit FROM clientes ORDER BY nombre'
        )
        return cursor.fetchall()
    
    def editar_cliente(self, cliente_id: int, nuevo_nombre: str, nuevo_telefono: Optional[str], nuevo_nit: Optional[str]) -> str:
        """Edita la información de un cliente"""
        try:
            self.db.execute_query(
                'UPDATE clientes SET nombre = ?, telefono = ?, nit = ? WHERE id = ?',
                (nuevo_nombre, nuevo_telefono, nuevo_nit, cliente_id)
            )
            self.db.commit()
            return f"✅ Cliente ID {cliente_id} actualizado"
        except sqlite3.IntegrityError as e:
            if "telefono" in str(e):
                return "❌ Error: Ya existe un cliente con ese teléfono"
            elif "nit" in str(e):
                return "❌ Error: Ya existe un cliente con ese NIT"
            else:
                return "❌ Error en la base de datos"
    
    def detalles_cliente(self, cliente_id: int) -> Optional[Dict]:
        """Obtiene todos los detalles de un cliente"""
        if not self.cliente_existe(cliente_id):
            return None
        
        # Obtengo información del cliente
        cursor = self.db.execute_query(
            'SELECT nombre, telefono, nit FROM clientes WHERE id = ?', 
            (cliente_id,)
        )
        cliente_info = cursor.fetchone()
        
        # Obtengo los vehículos del cliente
        cursor = self.db.execute_query(
            'SELECT id, marca, modelo, año, placa, color FROM vehiculos WHERE cliente_id = ?',
            (cliente_id,)
        )
        vehiculos = cursor.fetchall()
        
        return {
            'cliente': cliente_info,
            'vehiculos': vehiculos
        }
    
    def nit_existe(self, nit: str) -> bool:
        """Verifica si un NIT ya existe"""
        if not nit:
            return False
        cursor = self.db.execute_query('SELECT id FROM clientes WHERE nit = ?', (nit,))
        return cursor.fetchone() is not None

# ============================================================================
# CLASE PARA MANEJAR VEHÍCULOS
# ============================================================================
class VehiculoManager:
    """Gestiona todo lo relacionado con vehículos"""
    
    def __init__(self, db_manager: DatabaseManager, validator: Validator):
        self.db = db_manager
        self.validator = validator
    
    def placa_existe(self, placa: str) -> bool:
        """Verifica si una placa ya existe"""
        cursor = self.db.execute_query('SELECT id FROM vehiculos WHERE placa = ?', (placa,))
        return cursor.fetchone() is not None
    
    def agregar_vehiculo(self, cliente_id: int, marca: str, modelo: str, año: int, 
                        placa: str, color: Optional[str] = None) -> str:
        """Agrega un vehículo a un cliente"""
        try:
            cursor = self.db.execute_query('''
                INSERT INTO vehiculos (cliente_id, marca, modelo, año, placa, color)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (cliente_id, marca, modelo, año, placa, color))
            self.db.commit()
            return f"✅ Vehículo {marca} {modelo} agregado (ID: {cursor.lastrowid})"
        except sqlite3.IntegrityError:
            raise Exception("Ya existe un vehículo con esa placa")
    
    def obtener_vehiculos_cliente(self, cliente_id: int) -> List[Tuple]:
        """Obtiene todos los vehículos de un cliente"""
        cursor = self.db.execute_query(
            'SELECT id, marca, modelo, año, placa, color FROM vehiculos WHERE cliente_id = ?',
            (cliente_id,)
        )
        return cursor.fetchall()
    
    def vehiculo_existe(self, vehiculo_id: int) -> bool:
        """Verifica si un vehículo existe"""
        cursor = self.db.execute_query('SELECT id FROM vehiculos WHERE id = ?', (vehiculo_id,))
        return cursor.fetchone() is not None
    
    def detalles_vehiculo(self, vehiculo_id: int) -> Optional[Dict]:
        """Obtiene todos los detalles de un vehículo"""
        if not self.vehiculo_existe(vehiculo_id):
            return None
        
        # Obtengo información del vehículo y su dueño
        cursor = self.db.execute_query('''
            SELECT v.marca, v.modelo, v.año, v.placa, v.color, c.nombre, c.telefono, c.nit
            FROM vehiculos v
            JOIN clientes c ON v.cliente_id = c.id
            WHERE v.id = ?
        ''', (vehiculo_id,))
        vehiculo_info = cursor.fetchone()
        
        # Obtengo el historial de órdenes del vehículo
        cursor = self.db.execute_query('''
            SELECT o.id, o.fecha_fin, o.descripcion_trabajo, 
                   o.tipo_servicio, o.precio_final, o.kilometraje, o.unidad_kilometraje,
                   e.nombre as empleado
            FROM ordenes_trabajo o
            LEFT JOIN empleados e ON o.empleado_id = e.id
            WHERE o.vehiculo_id = ?
            ORDER BY o.fecha_fin DESC
        ''', (vehiculo_id,))
        ordenes = cursor.fetchall()
        
        return {
            'vehiculo': vehiculo_info,
            'ordenes': ordenes
        }
    
    def editar_vehiculo(self, vehiculo_id: int, marca: str, modelo: str, año: int, 
                       placa: str, color: Optional[str] = None) -> str:
        """Edita la información de un vehículo"""
        try:
            self.db.execute_query('''
                UPDATE vehiculos 
                SET marca = ?, modelo = ?, año = ?, placa = ?, color = ?
                WHERE id = ?
            ''', (marca, modelo, año, placa, color, vehiculo_id))
            self.db.commit()
            return f"✅ Vehículo ID {vehiculo_id} actualizado"
        except sqlite3.IntegrityError:
            raise Exception("Ya existe un vehículo con esa placa")

# ============================================================================
# CLASE PARA MANEJAR EMPLEADOS
# ============================================================================
class EmpleadoManager:
    """Gestiona todo lo relacionado con empleados"""
    
    def __init__(self, db_manager: DatabaseManager, validator: Validator):
        self.db = db_manager
        self.validator = validator
    
    def agregar_empleado(self, nombre: str, telefono: str) -> str:
        """Agrega un nuevo empleado"""
        try:
            cursor = self.db.execute_query(
                'INSERT INTO empleados (nombre, telefono) VALUES (?, ?)', 
                (nombre, telefono)
            )
            self.db.commit()
            return f"✅ Empleado '{nombre}' agregado (ID: {cursor.lastrowid})"
        except sqlite3.IntegrityError:
            raise Exception("Ya existe un empleado con ese teléfono")
    
    def empleado_existe(self, empleado_id: int) -> bool:
        """Verifica si un empleado existe"""
        cursor = self.db.execute_query('SELECT id FROM empleados WHERE id = ?', (empleado_id,))
        return cursor.fetchone() is not None
    
    def listar_empleados(self) -> List[Tuple]:
        """Lista todos los empleados"""
        cursor = self.db.execute_query('SELECT id, nombre, telefono FROM empleados ORDER BY nombre')
        return cursor.fetchall()
    
    def editar_empleado(self, empleado_id: int, nuevo_nombre: str, nuevo_telefono: str) -> str:
        """Edita la información de un empleado"""
        try:
            self.db.execute_query(
                'UPDATE empleados SET nombre = ?, telefono = ? WHERE id = ?',
                (nuevo_nombre, nuevo_telefono, empleado_id)
            )
            self.db.commit()
            return f"✅ Empleado ID {empleado_id} actualizado"
        except sqlite3.IntegrityError:
            return "❌ Error: Ya existe un empleado con ese teléfono"

# ============================================================================
# CLASE PARA MANEJAR ÓRDENES DE TRABAJO
# ============================================================================
class OrdenManager:
    """Gestiona todo lo relacionado con órdenes de trabajo"""
    
    def __init__(self, db_manager: DatabaseManager, validator: Validator):
        self.db = db_manager
        self.validator = validator
    
    def orden_existe(self, orden_id: int) -> bool:
        """Verifica si una orden existe"""
        cursor = self.db.execute_query('SELECT id FROM ordenes_trabajo WHERE id = ?', (orden_id,))
        return cursor.fetchone() is not None
    
    def obtener_detalles_orden(self, orden_id: int) -> Optional[Dict]:
        """Obtiene todos los detalles de una orden"""
        if not self.orden_existe(orden_id):
            return None
        
        cursor = self.db.execute_query('''
            SELECT 
                o.id, o.fecha_fin, o.descripcion_trabajo, 
                o.tipo_servicio, o.horas_trabajadas, o.costo_repuestos, 
                o.costo_mano_obra, o.precio_final, o.kilometraje, o.unidad_kilometraje,
                v.marca, v.modelo, v.placa, v.año,
                c.nombre as cliente_nombre, c.telefono as cliente_telefono, c.nit as cliente_nit,
                e.nombre as empleado_nombre
            FROM ordenes_trabajo o
            JOIN vehiculos v ON o.vehiculo_id = v.id
            JOIN clientes c ON v.cliente_id = c.id
            LEFT JOIN empleados e ON o.empleado_id = e.id
            WHERE o.id = ?
        ''', (orden_id,))
        
        orden_info = cursor.fetchone()
        
        if not orden_info:
            return None
        
        # Organizo la información en un diccionario
        return {
            'id': orden_info[0],
            'fecha_fin': orden_info[1],
            'descripcion_trabajo': orden_info[2],
            'tipo_servicio': orden_info[3],
            'horas_trabajadas': orden_info[4],
            'costo_repuestos': orden_info[5],
            'costo_mano_obra': orden_info[6],
            'precio_final': orden_info[7],
            'kilometraje': orden_info[8],
            'unidad_kilometraje': orden_info[9],
            'vehiculo_marca': orden_info[10],
            'vehiculo_modelo': orden_info[11],
            'vehiculo_placa': orden_info[12],
            'vehiculo_año': orden_info[13],
            'cliente_nombre': orden_info[14],
            'cliente_telefono': orden_info[15],
            'cliente_nit': orden_info[16],
            'empleado_nombre': orden_info[17]
        }
    
    def agregar_orden(self, numero_orden: int, vehiculo_id: int, empleado_id: int, 
                     descripcion_trabajo: str, tipo_servicio: str, horas_trabajadas: float,
                     costo_repuestos: float, costo_mano_obra: float, kilometraje: float,
                     unidad_kilometraje: str = 'km', fecha_fin: Optional[str] = None) -> str:
        """Agrega una nueva orden de trabajo"""
        
        # Valido la fecha de finalización - SIEMPRE ES OBLIGATORIA
        if not fecha_fin:
            return "❌ Error: La fecha de finalización es obligatoria."
        
        fecha_fin_validada = self.validator.validar_fecha(fecha_fin, permitir_futuro=False, permitir_pasado=True)
        if fecha_fin_validada is None:
            return "❌ Error: Fecha de finalización inválida. Debe ser una fecha pasada o presente válida."
        
        # Calculo el precio total
        precio_final = costo_repuestos + costo_mano_obra
        
        try:
            # Inserto la orden en la base de datos
            self.db.execute_query('''
                INSERT INTO ordenes_trabajo 
                (id, vehiculo_id, empleado_id, descripcion_trabajo, tipo_servicio,
                 horas_trabajadas, costo_repuestos, costo_mano_obra, precio_final,
                 kilometraje, unidad_kilometraje, fecha_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (numero_orden, vehiculo_id, empleado_id, descripcion_trabajo, tipo_servicio,
                  horas_trabajadas, costo_repuestos, costo_mano_obra, precio_final,
                  kilometraje, unidad_kilometraje, fecha_fin_validada))
            
            self.db.commit()
            return f"✅ Orden #{numero_orden} agregada - Total: Q{precio_final:.2f} - Fecha: {fecha_fin_validada}"
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                return f"❌ Error: La orden #{numero_orden} ya existe."
            return f"❌ Error al agregar orden: {e}"
    
    def editar_orden(self, orden_id: int, descripcion_trabajo: str, tipo_servicio: str, 
                    horas_trabajadas: float, costo_repuestos: float, costo_mano_obra: float,
                    precio_final: float, kilometraje: float, unidad_kilometraje: str,
                    fecha_fin: str) -> str:
        """Edita una orden de trabajo existente"""
        try:
            # Valido la fecha de finalización
            fecha_fin_validada = self.validator.validar_fecha(fecha_fin, permitir_futuro=False, permitir_pasado=True)
            if fecha_fin_validada is None:
                return "❌ Error: Fecha de finalización inválida. Debe ser una fecha pasada o presente válida."
            
            self.db.execute_query('''
                UPDATE ordenes_trabajo 
                SET descripcion_trabajo = ?, tipo_servicio = ?, horas_trabajadas = ?,
                    costo_repuestos = ?, costo_mano_obra = ?, precio_final = ?,
                    kilometraje = ?, unidad_kilometraje = ?, fecha_fin = ?
                WHERE id = ?
            ''', (descripcion_trabajo, tipo_servicio, horas_trabajadas,
                  costo_repuestos, costo_mano_obra, precio_final,
                  kilometraje, unidad_kilometraje, fecha_fin_validada, orden_id))
            
            self.db.commit()
            return f"✅ Orden #{orden_id} actualizada correctamente"
        except Exception as e:
            return f"❌ Error al editar orden: {e}"

# ============================================================================
# CLASE PARA GENERAR REPORTES Y GRÁFICAS
# ============================================================================
class ReportManager:
    """Genera reportes y gráficas del taller"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def reporte_periodo(self, periodo: str = 'semana') -> Dict:
        """Genera reportes del período especificado"""
        # Defino la fecha de inicio según el período
        if periodo == 'semana':
            fecha_inicio = datetime.now() - timedelta(days=datetime.now().weekday())
        elif periodo == 'mes':
            fecha_inicio = datetime.now().replace(day=1)
        else:
            fecha_inicio = datetime.now().replace(month=1, day=1)
        
        # Obtengo las ganancias totales
        cursor = self.db.execute_query('''
            SELECT SUM(precio_final), SUM(horas_trabajadas), COUNT(*)
            FROM ordenes_trabajo 
            WHERE fecha_fin >= ?
        ''', (fecha_inicio.date(),))
        
        ganancias, horas, trabajos = cursor.fetchone()
        
        # Obtengo los servicios más populares
        cursor = self.db.execute_query('''
            SELECT tipo_servicio, COUNT(*), SUM(precio_final)
            FROM ordenes_trabajo 
            WHERE fecha_fin >= ?
            GROUP BY tipo_servicio
            ORDER BY COUNT(*) DESC
            LIMIT 5
        ''', (fecha_inicio.date(),))
        
        servicios_populares = cursor.fetchall()
        
        # Obtengo ganancias por día
        cursor = self.db.execute_query('''
            SELECT fecha_fin, SUM(precio_final)
            FROM ordenes_trabajo 
            WHERE fecha_fin >= ?
            GROUP BY fecha_fin
            ORDER BY fecha_fin
        ''', (fecha_inicio.date(),))
        
        ganancias_por_dia = cursor.fetchall()
        
        # Obtengo vehículos más frecuentes
        cursor = self.db.execute_query('''
            SELECT v.marca, COUNT(*) as frecuencia
            FROM ordenes_trabajo o
            JOIN vehiculos v ON o.vehiculo_id = v.id
            WHERE fecha_fin >= ?
            GROUP BY v.marca
            ORDER BY frecuencia DESC
            LIMIT 5
        ''', (fecha_inicio.date(),))
        
        vehiculos_frecuentes = cursor.fetchall()
        
        # Obtengo empleados más productivos
        cursor = self.db.execute_query('''
            SELECT e.nombre, COUNT(*) as trabajos, SUM(o.precio_final) as ingresos
            FROM ordenes_trabajo o
            JOIN empleados e ON o.empleado_id = e.id
            WHERE fecha_fin >= ?
            GROUP BY e.id
            ORDER BY ingresos DESC
            LIMIT 5
        ''', (fecha_inicio.date(),))
        
        empleados_productivos = cursor.fetchall()
        
        # Devuelvo todos los datos organizados
        return {
            'ganancias': ganancias or 0,
            'horas_trabajadas': horas or 0,
            'trabajos_completados': trabajos or 0,
            'periodo': periodo,
            'fecha_inicio': fecha_inicio.date(),
            'servicios_populares': servicios_populares,
            'ganancias_por_dia': ganancias_por_dia,
            'vehiculos_frecuentes': vehiculos_frecuentes,
            'empleados_productivos': empleados_productivos
        }
    
    def crear_grafica_servicios_populares(self, reporte: Dict):
        """Crea una gráfica de los servicios más populares"""
        import matplotlib.pyplot as plt
        
        if not reporte['servicios_populares']:
            return None
        
        servicios = [s[0] for s in reporte['servicios_populares']]
        cantidades = [s[1] for s in reporte['servicios_populares']]
        
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        colors = plt.cm.Set3(np.arange(len(servicios)))
        bars = ax.barh(servicios, cantidades, color=colors, alpha=0.7)
        
        # Añadir etiquetas de valor en las barras
        for bar in bars:
            width = bar.get_width()
            ax.text(width + max(cantidades)*0.01, bar.get_y() + bar.get_height()/2,
                   f'{int(width)}', ha='left', va='center')
        
        ax.set_title('Servicios Más Solicitados', fontsize=14, fontweight='bold')
        ax.set_xlabel('Cantidad de Trabajos', fontsize=12)
        ax.set_ylabel('Tipo de Servicio', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        fig.tight_layout()
        return fig
    
    def crear_grafica_ganancias_diarias(self, reporte: Dict):
        """Crea una gráfica de líneas de ganancias diarias"""
        if not reporte['ganancias_por_dia']:
            return None
        
        fechas = [datetime.strptime(str(fecha[0]), '%Y-%m-%d').strftime('%d/%m') 
                 for fecha in reporte['ganancias_por_dia']]
        ganancias = [float(fecha[1]) for fecha in reporte['ganancias_por_dia']]
        
        fig = Figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
        
        ax.plot(fechas, ganancias, marker='o', linewidth=2, markersize=8, 
                color='#2E8B57', alpha=0.8)
        
        # Añadir puntos de datos
        for i, (fecha, ganancia) in enumerate(zip(fechas, ganancias)):
            ax.annotate(f'Q{ganancia:.0f}', 
                       xy=(i, ganancia),
                       xytext=(0, 10),
                       textcoords='offset points',
                       ha='center',
                       fontsize=9)
        
        ax.set_title('Evolución de Ganancias Diarias', fontsize=14, fontweight='bold')
        ax.set_xlabel('Fecha', fontsize=12)
        ax.set_ylabel('Ganancias (Q)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
        
        fig.tight_layout()
        return fig
    
    def crear_grafica_vehiculos_frecuentes(self, reporte: Dict):
        """Crea una gráfica de vehículos más frecuentes"""
        import matplotlib.pyplot as plt
        
        if not reporte['vehiculos_frecuentes']:
            return None
        
        marcas = [v[0] for v in reporte['vehiculos_frecuentes']]
        frecuencias = [v[1] for v in reporte['vehiculos_frecuentes']]
        
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        colors = plt.cm.Paired(np.arange(len(marcas)))
        bars = ax.bar(marcas, frecuencias, color=colors, alpha=0.7)
        
        # Añadir etiquetas de valor
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{int(height)}', ha='center', va='bottom')
        
        ax.set_title('Marcas de Vehículos Más Frecuentes', fontsize=14, fontweight='bold')
        ax.set_xlabel('Marca del Vehículo', fontsize=12)
        ax.set_ylabel('Cantidad de Visitas', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        ax.tick_params(axis='x', rotation=45)
        
        fig.tight_layout()
        return fig
    
    def crear_grafica_empleados_productivos(self, reporte: Dict):
        """Crea una gráfica de empleados más productivos"""
        import matplotlib.pyplot as plt
        
        if not reporte['empleados_productivos']:
            return None
        
        empleados = [e[0] for e in reporte['empleados_productivos']]
        ingresos = [float(e[2]) for e in reporte['empleados_productivos']]
        
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        colors = plt.cm.Accent(np.arange(len(empleados)))
        bars = ax.bar(empleados, ingresos, color=colors, alpha=0.7)
        
        # Añadir etiquetas de valor
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(ingresos)*0.01,
                   f'Q{height:.0f}', ha='center', va='bottom', fontsize=9)
        
        ax.set_title('Empleados Más Productivos', fontsize=14, fontweight='bold')
        ax.set_xlabel('Empleado', fontsize=12)
        ax.set_ylabel('Ingresos Generados (Q)', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        ax.tick_params(axis='x', rotation=45)
        
        fig.tight_layout()
        return fig
    
    def crear_grafica_estadisticas_generales(self, reporte: Dict):
        """Crea una gráfica con estadísticas generales"""
        import matplotlib.pyplot as plt
        
        fig = Figure(figsize=(12, 8))
        
        # Gráfica 1: Métricas principales
        ax1 = fig.add_subplot(221)
        metricas = ['Ganancias', 'Trabajos', 'Horas']
        valores = [reporte['ganancias'], reporte['trabajos_completados'], reporte['horas_trabajadas']]
        colors = ['#4CAF50', '#2196F3', '#FF9800']
        
        bars = ax1.bar(metricas, valores, color=colors, alpha=0.7)
        for bar, val in zip(bars, valores):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + max(valores)*0.02,
                    f'{val:.0f}' if val >= 10 else f'{val:.1f}', 
                    ha='center', va='bottom')
        
        ax1.set_title('Métricas Principales', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Gráfica 2: Distribución de servicios (si existen)
        if reporte['servicios_populares']:
            ax2 = fig.add_subplot(222)
            servicios = [s[0] for s in reporte['servicios_populares']]
            cantidades = [s[1] for s in reporte['servicios_populares']]
            
            wedges, texts, autotexts = ax2.pie(cantidades, labels=servicios, autopct='%1.1f%%',
                                              colors=plt.cm.Set3(np.arange(len(servicios))),
                                              startangle=90)
            ax2.set_title('Distribución de Servicios', fontsize=12, fontweight='bold')
        
        # Gráfica 3: Comparativa vehículos vs ingresos
        if reporte['vehiculos_frecuentes'] and len(reporte['vehiculos_frecuentes']) > 0:
            ax3 = fig.add_subplot(223)
            marcas = [v[0] for v in reporte['vehiculos_frecuentes']]
            frecuencias = [v[1] for v in reporte['vehiculos_frecuentes']]
            ax3.plot(marcas, frecuencias, 'o-', color='#9C27B0', alpha=0.7)
            ax3.set_title('Frecuencia por Marca', fontsize=12, fontweight='bold')
            ax3.set_ylabel('Visitas', fontsize=10)
            ax3.grid(True, alpha=0.3)
            ax3.tick_params(axis='x', rotation=45)
        
        # Gráfica 4: Resumen visual
        ax4 = fig.add_subplot(224)
        ax4.text(0.5, 0.5, 
                f"Periodo: {reporte['periodo'].capitalize()}\n"
                f"Desde: {reporte['fecha_inicio']}\n"
                f"Ganancias: Q{reporte['ganancias']:.2f}\n"
                f"Trabajos: {reporte['trabajos_completados']}\n"
                f"Horas: {reporte['horas_trabajadas']:.1f}",
                ha='center', va='center', fontsize=11,
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#E3F2FD", edgecolor="black"))
        ax4.set_title('Resumen del Reporte', fontsize=12, fontweight='bold')
        ax4.axis('off')
        
        fig.suptitle(f'Reporte {reporte["periodo"].capitalize()} - Taller SEYMO', 
                    fontsize=16, fontweight='bold', y=0.98)
        fig.tight_layout()
        
        return fig
    
    def reporte_clientes(self) -> Dict:
        """Genera reporte de clientes"""
        # Obtener todos los clientes
        cursor = self.db.execute_query('''
            SELECT c.id, c.nombre, c.telefono, c.nit, COUNT(v.id) as num_vehiculos
            FROM clientes c
            LEFT JOIN vehiculos v ON c.id = v.cliente_id
            GROUP BY c.id
            ORDER BY num_vehiculos DESC
        ''')
        
        clientes = cursor.fetchall()
        
        # Obtener clientes más frecuentes
        cursor = self.db.execute_query('''
            SELECT c.nombre, COUNT(o.id) as ordenes, SUM(o.precio_final) as gasto_total
            FROM clientes c
            JOIN vehiculos v ON c.id = v.cliente_id
            JOIN ordenes_trabajo o ON v.id = o.vehiculo_id
            GROUP BY c.id
            ORDER BY ordenes DESC
            LIMIT 10
        ''')
        
        clientes_frecuentes = cursor.fetchall()
        
        # Obtener distribución de vehículos por cliente
        cursor = self.db.execute_query('''
            SELECT 
                CASE 
                    WHEN vehiculos_por_cliente = 1 THEN '1 vehículo'
                    WHEN vehiculos_por_cliente = 2 THEN '2 vehículos'
                    WHEN vehiculos_por_cliente = 3 THEN '3 vehículos'
                    ELSE '4+ vehículos'
                END as categoria,
                COUNT(*) as cantidad_clientes
            FROM (
                SELECT c.id, COUNT(v.id) as vehiculos_por_cliente
                FROM clientes c
                LEFT JOIN vehiculos v ON c.id = v.cliente_id
                GROUP BY c.id
            )
            GROUP BY categoria
            ORDER BY cantidad_clientes DESC
        ''')
        
        distribucion_vehiculos = cursor.fetchall()
        
        return {
            'total_clientes': len(clientes),
            'clientes': clientes,
            'clientes_frecuentes': clientes_frecuentes,
            'distribucion_vehiculos': distribucion_vehiculos
        }
    
    def crear_grafica_clientes_frecuentes(self, reporte_clientes: Dict):
        """Crea gráfica de clientes más frecuentes"""
        import matplotlib.pyplot as plt
        
        if not reporte_clientes['clientes_frecuentes']:
            return None
        
        clientes = [c[0][:15] for c in reporte_clientes['clientes_frecuentes']]  # Limitar longitud del nombre
        ordenes = [c[1] for c in reporte_clientes['clientes_frecuentes']]
        
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        colors = plt.cm.viridis(np.arange(len(clientes)) / len(clientes))
        bars = ax.barh(clientes, ordenes, color=colors, alpha=0.7)
        
        # Añadir etiquetas de valor
        for bar in bars:
            width = bar.get_width()
            ax.text(width + max(ordenes)*0.01, bar.get_y() + bar.get_height()/2,
                   f'{int(width)}', ha='left', va='center')
        
        ax.set_title('Clientes Más Frecuentes', fontsize=14, fontweight='bold')
        ax.set_xlabel('Número de Órdenes', fontsize=12)
        ax.set_ylabel('Cliente', fontsize=12)
        ax.grid(True, alpha=0.3, axis='x')
        
        fig.tight_layout()
        return fig
    
    def crear_grafica_distribucion_vehiculos(self, reporte_clientes: Dict):
        """Crea gráfica de distribución de vehículos por cliente"""
        import matplotlib.pyplot as plt
        
        if not reporte_clientes['distribucion_vehiculos']:
            return None
        
        categorias = [c[0] for c in reporte_clientes['distribucion_vehiculos']]
        cantidades = [c[1] for c in reporte_clientes['distribucion_vehiculos']]
        
        fig = Figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
        
        colors = plt.cm.Pastel1(np.arange(len(categorias)))
        wedges, texts, autotexts = ax.pie(cantidades, labels=categorias, autopct='%1.1f%%',
                                         colors=colors, startangle=90,
                                         explode=[0.05]*len(categorias))
        
        # Mejorar etiquetas
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontweight('bold')
        
        ax.set_title('Distribución de Vehículos por Cliente', fontsize=14, fontweight='bold')
        
        return fig
    
    def reporte_empleados(self) -> Dict:
        """Genera reporte de empleados"""
        # Obtener estadísticas de empleados
        cursor = self.db.execute_query('''
            SELECT e.nombre, 
                   COUNT(o.id) as total_ordenes,
                   SUM(o.horas_trabajadas) as total_horas,
                   SUM(o.precio_final) as total_ingresos,
                   AVG(o.precio_final) as promedio_por_orden,
                   MAX(o.fecha_fin) as ultimo_trabajo
            FROM empleados e
            LEFT JOIN ordenes_trabajo o ON e.id = o.empleado_id
            GROUP BY e.id
            ORDER BY total_ingresos DESC
        ''')
        
        empleados = cursor.fetchall()
        
        # Obtener tipos de servicio por empleado
        cursor = self.db.execute_query('''
            SELECT e.nombre, o.tipo_servicio, COUNT(*) as cantidad
            FROM empleados e
            JOIN ordenes_trabajo o ON e.id = o.empleado_id
            GROUP BY e.id, o.tipo_servicio
            ORDER BY e.nombre, cantidad DESC
        ''')
        
        servicios_por_empleado = cursor.fetchall()
        
        # Calcular productividad mensual
        cursor = self.db.execute_query('''
            SELECT e.nombre, 
                   strftime('%Y-%m', o.fecha_fin) as mes,
                   COUNT(*) as ordenes_mes
            FROM empleados e
            JOIN ordenes_trabajo o ON e.id = o.empleado_id
            WHERE o.fecha_fin >= date('now', '-6 months')
            GROUP BY e.id, strftime('%Y-%m', o.fecha_fin)
            ORDER BY e.nombre, mes
        ''')
        
        productividad_mensual = cursor.fetchall()
        
        return {
            'total_empleados': len(empleados),
            'empleados': empleados,
            'servicios_por_empleado': servicios_por_empleado,
            'productividad_mensual': productividad_mensual
        }
    
    def crear_grafica_productividad_empleados(self, reporte_empleados: Dict):
        """Crea gráfica de productividad de empleados"""
        import matplotlib.pyplot as plt
        
        if not reporte_empleados['empleados']:
            return None
        
        empleados = [e[0] for e in reporte_empleados['empleados']]
        ingresos = [float(e[3] or 0) for e in reporte_empleados['empleados']]
        
        fig = Figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
        
        # Crear gráfico de barras agrupadas
        x = np.arange(len(empleados))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, ingresos, width, label='Ingresos (Q)', color='#4CAF50', alpha=0.7)
        
        # Añadir etiquetas de valor
        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + max(ingresos)*0.01,
                       f'Q{height:.0f}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('Empleados', fontsize=12)
        ax.set_ylabel('Ingresos Generados (Q)', fontsize=12)
        ax.set_title('Productividad de Empleados - Ingresos Generados', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(empleados, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        fig.tight_layout()
        return fig
    
    def proyeccion_crecimiento(self) -> Optional[Dict]:
        """Genera proyecciones de crecimiento basadas en datos históricos"""
        try:
            # Obtengo datos de los últimos 6 meses
            seis_meses_atras = (datetime.now() - timedelta(days=180)).date()
            
            cursor = self.db.execute_query('''
                SELECT 
                    strftime('%Y-%m', fecha_fin) as mes,
                    SUM(precio_final) as total
                FROM ordenes_trabajo 
                WHERE fecha_fin >= ?
                GROUP BY strftime('%Y-%m', fecha_fin)
                ORDER BY fecha_fin DESC
                LIMIT 6
            ''', (seis_meses_atras,))
            
            datos = cursor.fetchall()
            
            # Necesito al menos 2 meses de datos
            if len(datos) < 2:
                return None
            
            # Calculo el crecimiento promedio
            totales = [d[1] for d in datos]
            crecimientos = []
            
            for i in range(1, len(totales)):
                if totales[i-1] > 0:
                    crecimiento = (totales[i] - totales[i-1]) / totales[i-1]
                    crecimientos.append(crecimiento)
            
            if not crecimientos:
                return None
            
            crecimiento_promedio = sum(crecimientos) / len(crecimientos)
            
            # Genero proyecciones para los próximos 6 meses
            proyecciones = []
            ultimo_total = totales[-1] if totales else 0
            
            for i in range(1, 7):
                mes_proyectado = (datetime.now() + timedelta(days=30*i)).strftime('%Y-%m')
                ingreso_proyectado = ultimo_total * (1 + crecimiento_promedio) ** i
                proyecciones.append((mes_proyectado, ingreso_proyectado))
            
            return {
                'crecimiento_promedio': crecimiento_promedio,
                'proyecciones': proyecciones,
                'datos_historicos': datos
            }
            
        except Exception as e:
            print(f"❌ Error generando proyección: {e}")
            return None
    
    def crear_grafica_proyeccion(self, proyeccion: Dict):
        """Crea gráfica de proyección de crecimiento"""
        import matplotlib.pyplot as plt
        
        if not proyeccion or not proyeccion['datos_historicos']:
            return None
        
        # Preparar datos históricos
        historicos_meses = [d[0] for d in proyeccion['datos_historicos']]
        historicos_valores = [float(d[1]) for d in proyeccion['datos_historicos']]
        
        # Preparar datos proyectados
        proyectados_meses = [d[0] for d in proyeccion['proyecciones']]
        proyectados_valores = [float(d[1]) for d in proyeccion['proyecciones']]
        
        fig = Figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
        
        # Graficar datos históricos
        ax.plot(historicos_meses, historicos_valores, 'o-', linewidth=2, markersize=8,
                color='#2196F3', label='Datos Históricos', alpha=0.8)
        
        # Graficar proyecciones
        ax.plot(proyectados_meses, proyectados_valores, 's--', linewidth=2, markersize=8,
                color='#FF5722', label='Proyección', alpha=0.8)
        
        # Añadir área de confianza para proyecciones
        ax.fill_between(proyectados_meses, 
                       [v * 0.8 for v in proyectados_valores],  # Límite inferior
                       [v * 1.2 for v in proyectados_valores],  # Límite superior
                       alpha=0.2, color='#FF5722')
        
        ax.set_title('Proyección de Crecimiento - Próximos 6 Meses', fontsize=14, fontweight='bold')
        ax.set_xlabel('Mes', fontsize=12)
        ax.set_ylabel('Ingresos Proyectados (Q)', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
        
        # Añadir texto con crecimiento promedio
        ax.text(0.02, 0.98, 
               f"Crecimiento promedio: {proyeccion['crecimiento_promedio']*100:.1f}% mensual",
               transform=ax.transAxes, fontsize=11,
               verticalalignment='top',
               bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        fig.tight_layout()
        return fig

# ============================================================================
# CLASE PARA RECORDATORIOS INTELIGENTES MEJORADOS
# ============================================================================
class RecordatoriosInteligentesMejorados:
    """Predice cuándo los vehículos necesitarán mantenimiento con IA básica"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        # Períodos recomendados por tipo de servicio (en días)
        self.periodos_recomendados = {
            'Cambio de aceite': {'tiempo': 180, 'km': 8000},
            'Frenos': {'tiempo': 365, 'km': 25000},
            'Alineación': {'tiempo': 180, 'km': 15000},
            'Suspensión': {'tiempo': 540, 'km': 40000},
            'Transmisión': {'tiempo': 730, 'km': 60000},
            'Correa distribución': {'tiempo': 1095, 'km': 100000},
            'Batería': {'tiempo': 730, 'km': 0},
            'Filtro aire': {'tiempo': 365, 'km': 15000},
            'Filtro combustible': {'tiempo': 730, 'km': 30000},
            'Liquido frenos': {'tiempo': 365, 'km': 20000},
            'Refrigerante': {'tiempo': 730, 'km': 40000},
        }
        # Factores por tipo de vehículo
        self.factores_vehiculo = {
            'Toyota': 1.0, 'Honda': 1.0, 'Nissan': 1.0,  # Japoneses: estándar
            'BMW': 0.8, 'Mercedes': 0.8, 'Audi': 0.8,    # Alemanes: más frecuente
            'Ford': 1.1, 'Chevrolet': 1.1, 'Dodge': 1.1, # Americanos: menos frecuente
            'Hyundai': 1.0, 'Kia': 1.0, 'Mazda': 1.0,    # Coreanos: estándar
        }
    
    def obtener_tipos_servicio_disponibles(self) -> List[str]:
        """Obtiene todos los tipos de servicio que existen"""
        cursor = self.db.execute_query('''
            SELECT DISTINCT tipo_servicio FROM ordenes_trabajo 
            WHERE tipo_servicio IS NOT NULL AND tipo_servicio != ''
            ORDER BY tipo_servicio
        ''')
        return [servicio[0] for servicio in cursor.fetchall()]
    
    def calcular_promedio_km_mensual(self, vehiculo_id: int) -> float:
        """Calcula el promedio de kilómetros mensuales del vehículo"""
        try:
            cursor = self.db.execute_query('''
                SELECT kilometraje, fecha_fin
                FROM ordenes_trabajo 
                WHERE vehiculo_id = ? 
                AND kilometraje > 0
                ORDER BY fecha_fin
            ''', (vehiculo_id,))
            
            registros = cursor.fetchall()
            
            if len(registros) < 2:
                return 1000  # Valor por defecto: 1000 km/mes
            
            # Calcular diferencia entre primer y último registro
            primer_km, primer_fecha = registros[0]
            ultimo_km, ultimo_fecha = registros[-1]
            
            # Convertir fechas a datetime si son strings
            if isinstance(primer_fecha, str):
                primer_fecha_dt = datetime.strptime(primer_fecha, '%Y-%m-%d')
            else:
                primer_fecha_dt = datetime.combine(primer_fecha, datetime.now().time())
            
            if isinstance(ultimo_fecha, str):
                ultimo_fecha_dt = datetime.strptime(ultimo_fecha, '%Y-%m-%d')
            else:
                ultimo_fecha_dt = datetime.combine(ultimo_fecha, datetime.now().time())
            
            # Calcular diferencia en meses
            meses = (ultimo_fecha_dt - primer_fecha_dt).days / 30.44
            
            if meses <= 0:
                return 1000
            
            # Calcular km/mes
            km_total = ultimo_km - primer_km
            km_mensual = km_total / meses
            
            return max(500, min(3000, km_mensual))  # Limitar entre 500 y 3000 km/mes
            
        except Exception as e:
            print(f"⚠️ Error calculando km mensual: {e}")
            return 1000
    
    def analizar_historial_servicios(self, vehiculo_id: int, tipo_servicio: str) -> Dict:
        """Analiza el historial de un tipo de servicio específico para un vehículo"""
        cursor = self.db.execute_query('''
            SELECT fecha_fin, kilometraje, precio_final
            FROM ordenes_trabajo 
            WHERE vehiculo_id = ? 
            AND tipo_servicio = ?
            ORDER BY fecha_fin
        ''', (vehiculo_id, tipo_servicio))
        
        servicios = cursor.fetchall()
        
        if len(servicios) < 2:
            return {'intervalo_promedio_dias': 180, 'intervalo_promedio_km': 8000, 'num_registros': len(servicios)}
        
        # Calcular intervalos entre servicios
        intervalos_dias = []
        intervalos_km = []
        
        for i in range(1, len(servicios)):
            fecha_actual_str, km_actual, _ = servicios[i]
            fecha_anterior_str, km_anterior, _ = servicios[i-1]
            
            # Convertir fechas
            try:
                if isinstance(fecha_actual_str, str):
                    fecha_actual = datetime.strptime(fecha_actual_str, '%Y-%m-%d')
                else:
                    fecha_actual = datetime.combine(fecha_actual_str, datetime.now().time())
                
                if isinstance(fecha_anterior_str, str):
                    fecha_anterior = datetime.strptime(fecha_anterior_str, '%Y-%m-%d')
                else:
                    fecha_anterior = datetime.combine(fecha_anterior_str, datetime.now().time())
                
                # Calcular diferencias
                dias = (fecha_actual - fecha_anterior).days
                km = km_actual - km_anterior
                
                if dias > 30 and dias < 730:  # Filtro razonable: entre 1 mes y 2 años
                    intervalos_dias.append(dias)
                    intervalos_km.append(km)
                    
            except Exception as e:
                print(f"⚠️ Error procesando intervalo: {e}")
                continue
        
        if not intervalos_dias:
            return {'intervalo_promedio_dias': 180, 'intervalo_promedio_km': 8000, 'num_registros': len(servicios)}
        
        # Calcular promedios
        avg_dias = sum(intervalos_dias) / len(intervalos_dias)
        avg_km = sum(intervalos_km) / len(intervalos_km)
        
        return {
            'intervalo_promedio_dias': avg_dias,
            'intervalo_promedio_km': avg_km,
            'num_registros': len(servicios),
            'variabilidad': np.std(intervalos_dias) if len(intervalos_dias) > 1 else 0
        }
    
    def predecir_proximo_servicio_mejorado(self, tipo_servicio: str, margen_dias: int = 30) -> List[Dict]:
        """Predicción mejorada usando múltiples variables"""
        
        # Obtener vehículos con este tipo de servicio
        cursor = self.db.execute_query('''
            SELECT DISTINCT v.id, v.marca, v.modelo, v.placa, c.nombre, c.telefono, c.nit,
                   MAX(o.fecha_fin) as ultima_fecha, MAX(o.kilometraje) as ultimo_km
            FROM vehiculos v
            JOIN ordenes_trabajo o ON v.id = o.vehiculo_id
            JOIN clientes c ON v.cliente_id = c.id
            WHERE o.tipo_servicio = ?
            GROUP BY v.id
        ''', (tipo_servicio,))
        
        vehiculos = cursor.fetchall()
        resultados = []
        
        for vehiculo in vehiculos:
            vehiculo_id, marca, modelo, placa, cliente, telefono, nit, ultima_fecha, ultimo_km = vehiculo
            
            if not ultima_fecha or not ultimo_km:
                continue
            
            try:
                # 1. CONVERTIR FECHAS
                if isinstance(ultima_fecha, str):
                    fecha_ultimo_dt = datetime.strptime(ultima_fecha, '%Y-%m-%d')
                else:
                    fecha_ultimo_dt = datetime.combine(ultima_fecha, datetime.now().time())
                
                # 2. ANALIZAR HISTORIAL DEL VEHÍCULO
                historial = self.analizar_historial_servicios(vehiculo_id, tipo_servicio)
                
                # 3. CALCULAR PROMEDIO DE KM MENSUALES
                km_mensual = self.calcular_promedio_km_mensual(vehiculo_id)
                
                # 4. CALCULAR PRÓXIMO SERVICIO POR TIEMPO
                # Usar historial si hay datos suficientes, si no usar valores por defecto
                if historial['num_registros'] >= 3:
                    intervalo_dias = historial['intervalo_promedio_dias']
                else:
                    # Valor por defecto ajustado por marca
                    intervalo_default = self.periodos_recomendados.get(tipo_servicio, {'tiempo': 180})['tiempo']
                    factor_marca = self.factores_vehiculo.get(marca, 1.0)
                    intervalo_dias = intervalo_default * factor_marca
                
                # 5. CALCULAR PRÓXIMO SERVICIO POR KILOMETRAJE
                if historial['intervalo_promedio_km'] > 0:
                    proximo_km = ultimo_km + historial['intervalo_promedio_km']
                else:
                    km_default = self.periodos_recomendados.get(tipo_servicio, {'km': 8000})['km']
                    proximo_km = ultimo_km + km_default
                
                # 6. CALCULAR FECHAS ESTIMADAS
                fecha_estimada_tiempo = fecha_ultimo_dt + timedelta(days=intervalo_dias)
                
                # Calcular fecha por kilometraje (basado en km/mes)
                if km_mensual > 0:
                    km_faltantes = proximo_km - ultimo_km
                    dias_por_km = (km_faltantes / km_mensual) * 30.44
                    fecha_estimada_km = fecha_ultimo_dt + timedelta(days=dias_por_km)
                    
                    # 7. COMBINAR AMBAS PREDICCIONES (PROMEDIO PONDERADO)
                    # Dar más peso al método con más datos históricos
                    if historial['num_registros'] >= 3:
                        peso_tiempo = 0.7
                        peso_km = 0.3
                    else:
                        peso_tiempo = 0.5
                        peso_km = 0.5
                    
                    # Calcular fecha combinada
                    dias_tiempo = (fecha_estimada_tiempo - datetime.now()).days
                    dias_km = (fecha_estimada_km - datetime.now()).days
                    dias_combinados = (dias_tiempo * peso_tiempo) + (dias_km * peso_km)
                    
                    fecha_estimada = datetime.now() + timedelta(days=dias_combinados)
                    dias_restantes = dias_combinados
                    
                else:
                    # Solo usar predicción por tiempo
                    fecha_estimada = fecha_estimada_tiempo
                    dias_restantes = (fecha_estimada - datetime.now()).days
                
                # 8. CALCULAR CONFIABILIDAD DE LA PREDICCIÓN
                confiabilidad = self.calcular_confiabilidad_prediccion(historial, km_mensual)
                
                # 9. FILTRAR POR MARGEN Y CONFIABILIDAD
                if dias_restantes <= margen_dias and dias_restantes >= -7:  # Permitir 7 días de retraso
                    # Calcular próximo servicio por kilometraje también
                    proximo_por_km = f"{proximo_km:.0f} km" if proximo_km > ultimo_km else "N/A"
                    
                    resultados.append({
                        'vehiculo_id': vehiculo_id,
                        'marca': marca,
                        'modelo': modelo,
                        'placa': placa,
                        'cliente': cliente,
                        'telefono': telefono,
                        'nit': nit,
                        'ultimo_servicio': ultima_fecha if isinstance(ultima_fecha, str) else ultima_fecha.strftime('%Y-%m-%d'),
                        'km_ultimo': ultimo_km or 0,
                        'proximo_estimado': fecha_estimada.strftime('%Y-%m-%d'),
                        'proximo_km': proximo_por_km,
                        'dias_restantes': int(dias_restantes),
                        'confiabilidad': confiabilidad,  # 0-100%
                        'km_mensual_promedio': km_mensual,
                        'metodo_prediccion': 'Combinado' if km_mensual > 0 else 'Tiempo',
                        'prioridad': self.calcular_prioridad(dias_restantes, confiabilidad),
                        'tipo_servicio': tipo_servicio
                    })
                    
            except Exception as e:
                print(f"⚠️ Error procesando vehículo {placa}: {e}")
                continue
        
        # Ordenar por prioridad (más urgente y confiable primero)
        resultados.sort(key=lambda x: (-x['prioridad'], x['dias_restantes']))
        return resultados
    
    def calcular_confiabilidad_prediccion(self, historial: Dict, km_mensual: float) -> float:
        """Calcula qué tan confiable es la predicción (0-100%)"""
        confiabilidad = 50.0  # Base
        
        # Factor 1: Cantidad de datos históricos
        if historial['num_registros'] >= 5:
            confiabilidad += 30
        elif historial['num_registros'] >= 3:
            confiabilidad += 20
        elif historial['num_registros'] >= 2:
            confiabilidad += 10
        
        # Factor 2: Consistencia en intervalos (baja variabilidad)
        if 'variabilidad' in historial and historial['variabilidad'] > 0:
            if historial['variabilidad'] < 30:  # Baja variabilidad (menos de 30 días)
                confiabilidad += 15
            elif historial['variabilidad'] < 60:  # Variabilidad media
                confiabilidad += 5
        
        # Factor 3: Kilometraje mensual conocido
        if km_mensual > 0 and km_mensual < 3000:  # Rango razonable
            confiabilidad += 10
        
        # Limitar entre 0 y 100
        return max(10, min(95, confiabilidad))
    
    def calcular_prioridad(self, dias_restantes: int, confiabilidad: float) -> float:
        """Calcula prioridad de contacto (más alto = más urgente)"""
        if dias_restantes < 0:  # Vencido
            urgencia = 100 - dias_restantes  # Más negativo = más urgente
        elif dias_restantes <= 7:  # Esta semana
            urgencia = 90
        elif dias_restantes <= 14:  # Próximas 2 semanas
            urgencia = 70
        elif dias_restantes <= 30:  # Este mes
            urgencia = 50
        else:
            urgencia = 30
        
        # Ajustar por confiabilidad
        prioridad = urgencia * (confiabilidad / 100)
        return prioridad
    
    def generar_reporte_predicciones(self, tipo_servicio: str) -> Dict:
        """Genera un reporte estadístico de las predicciones"""
        predicciones = self.predecir_proximo_servicio_mejorado(tipo_servicio, margen_dias=365)
        
        if not predicciones:
            return {'total_vehiculos': 0}
        
        # Estadísticas
        dias_restantes_list = [p['dias_restantes'] for p in predicciones]
        confiabilidades = [p['confiabilidad'] for p in predicciones]
        
        # Categorizar por urgencia
        categorias = {
            'vencidos': sum(1 for d in dias_restantes_list if d < 0),
            'esta_semana': sum(1 for d in dias_restantes_list if 0 <= d <= 7),
            'proximas_2_semanas': sum(1 for d in dias_restantes_list if 8 <= d <= 14),
            'este_mes': sum(1 for d in dias_restantes_list if 15 <= d <= 30),
            'proximo_mes': sum(1 for d in dias_restantes_list if 31 <= d <= 60),
            'mas_2_meses': sum(1 for d in dias_restantes_list if d > 60),
        }
        
        return {
            'total_vehiculos': len(predicciones),
            'promedio_dias_restantes': np.mean(dias_restantes_list) if dias_restantes_list else 0,
            'promedio_confiabilidad': np.mean(confiabilidades) if confiabilidades else 0,
            'categorias_urgencia': categorias,
            'prediccion_mas_confiable': max(predicciones, key=lambda x: x['confiabilidad']) if predicciones else None,
            'prediccion_mas_urgente': min(predicciones, key=lambda x: x['dias_restantes']) if predicciones else None,
        }
    
    def obtener_todos_recordatorios(self, margen_dias: int = 30) -> List[Dict]:
        """Obtiene todos los recordatorios para todos los tipos de servicio"""
        tipos_servicio = self.obtener_tipos_servicio_disponibles()
        todos_recordatorios = []
        
        for tipo_servicio in tipos_servicio:
            recordatorios = self.predecir_proximo_servicio_mejorado(tipo_servicio, margen_dias)
            todos_recordatorios.extend(recordatorios)
        
        # Ordenar por prioridad (más urgente primero)
        todos_recordatorios.sort(key=lambda x: (-x['prioridad'], x['dias_restantes']))
        return todos_recordatorios

# ============================================================================
# CLASE PRINCIPAL DEL TALLER
# ============================================================================
class TallerSEYMO:
    """Esta clase coordina todas las funcionalidades del taller"""
    
    def __init__(self):
        try:
            # Inicializo todos los componentes
            self.db = DatabaseManager()
            self.validator = Validator()
            self.clientes = ClienteManager(self.db, self.validator)
            self.vehiculos = VehiculoManager(self.db, self.validator)
            self.empleados = EmpleadoManager(self.db, self.validator)
            self.ordenes = OrdenManager(self.db, self.validator)
            self.reportes = ReportManager(self.db)
            self.recordatorios = RecordatoriosInteligentesMejorados(self.db)  # ¡VERSIÓN MEJORADA!
            
            print("✅ Sistema Taller SEYMO listo")
            
        except Exception as e:
            print(f"❌ Error iniciando el sistema: {e}")
            raise

# ============================================================================
# INTERFAZ GRÁFICA - VENTANA PRINCIPAL
# ============================================================================
class TallerSEYMOGUI:
    """Esta clase maneja la ventana principal del programa"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Taller SEYMO - Sistema de Gestión")
        self.root.geometry("1200x800")  # Tamaño de la ventana
        
        # Inicializo el sistema
        try:
            self.taller = TallerSEYMO()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el sistema: {e}")
            self.root.destroy()
            return
        
        # Variables para recordar lo que selecciono
        self.cliente_seleccionado = None
        self.vehiculo_seleccionado = None
        self.empleado_seleccionado = None
        
        # Configuro los colores y estilos
        self.setup_styles()
        
        # Creo todos los elementos de la ventana
        self.create_widgets()
        
        # Inicio la actualización de estadísticas
        self.actualizar_estadisticas()
        
    def setup_styles(self):
        """Configuro los colores y estilos de la interfaz"""
        style = ttk.Style()
        style.theme_use('clam')  # Uso un tema moderno
        
        # Defino mis colores
        self.primary_color = "#2c3e50"      # Azul oscuro
        self.secondary_color = "#3498db"    # Azul claro
        self.success_color = "#27ae60"      # Verde
        self.warning_color = "#e67e22"      # Naranja
        self.danger_color = "#e74c3c"       # Rojo
        
        # Configuro el color de fondo de la ventana
        self.root.configure(bg=self.primary_color)
        
    def create_widgets(self):
        """Creo todos los botones y elementos de la ventana"""
        # Frame principal (contenedor de todo)
        main_frame = tk.Frame(self.root, bg=self.primary_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título del programa
        title_frame = tk.Frame(main_frame, bg=self.primary_color)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            title_frame,
            text="🔧 TALLER SEYMO - SISTEMA DE GESTIÓN",
            font=("Arial", 20, "bold"),
            bg=self.primary_color,
            fg="white"
        ).pack()
        
        tk.Label(
            title_frame,
            text="Gestión Integral para Taller Mecánico",
            font=("Arial", 12),
            bg=self.primary_color,
            fg="#ecf0f1"
        ).pack()
        
        # Frame para los botones principales
        buttons_frame = tk.Frame(main_frame, bg=self.primary_color)
        buttons_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Creo los botones del menú
        self.create_main_buttons(buttons_frame)
        
        # Frame para mostrar resultados
        self.result_frame = tk.Frame(main_frame, bg="white", relief=tk.SUNKEN, borderwidth=2)
        self.result_frame.pack(fill=tk.BOTH, expand=True)
        
        # Área de texto donde muestro los resultados
        self.result_text = scrolledtext.ScrolledText(
            self.result_frame,
            font=("Consolas", 10),
            wrap=tk.WORD,
            bg="#f8f9fa",
            relief=tk.FLAT
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Barra de estado (abajo de la ventana)
        self.status_bar = tk.Label(
            self.root,
            text="🔄 Cargando estadísticas...",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#2c3e50",
            fg="white",
            font=("Arial", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_main_buttons(self, parent):
        """Creo los botones principales del menú"""
        # Primera fila de botones
        row1_frame = tk.Frame(parent, bg=self.primary_color)
        row1_frame.pack(fill=tk.X, pady=5)
        
        # Defino los botones de la primera fila
        buttons_row1 = [
            ("📝 Nuevo Cliente", self.registrar_cliente),
            ("🚗 Nuevo Vehículo", self.registrar_vehiculo),
            ("👷 Nuevo Empleado", self.registrar_empleado),
            ("📋 Nueva Orden", self.nueva_orden),
            ("🔍 Buscar Cliente", self.buscar_cliente)
        ]
        
        # Creo cada botón de la primera fila
        for i, (text, command) in enumerate(buttons_row1):
            btn = tk.Button(
                row1_frame,
                text=text,
                command=command,
                font=("Arial", 10, "bold"),
                bg=self.secondary_color,
                fg="white",
                relief=tk.RAISED,
                borderwidth=2,
                cursor="hand2",
                padx=15,
                pady=10,
                width=15
            )
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            row1_frame.grid_columnconfigure(i, weight=1)
        
        # Segunda fila de botones
        row2_frame = tk.Frame(parent, bg=self.primary_color)
        row2_frame.pack(fill=tk.X, pady=5)
        
        # Defino los botones de la segunda fila
        buttons_row2 = [
            ("🔧 Historial Vehículo", self.historial_vehiculo),
            ("✏️ Editar Cliente", self.editar_cliente),
            ("✏️ Editar Empleado", self.editar_empleado),
            ("✏️ Editar Orden", self.editar_orden),
            ("📊 Reportes", self.menu_reportes),
            ("🧠 Recordatorios", self.recordatorios_inteligentes_mejorados),  # ¡VERSIÓN MEJORADA!
            ("❌ Salir", self.salir)
        ]
        
        # Creo cada botón de la segunda fila
        for i, (text, command) in enumerate(buttons_row2):
            btn = tk.Button(
                row2_frame,
                text=text,
                command=command,
                font=("Arial", 10, "bold"),
                bg=self.warning_color if "Editar" in text else self.secondary_color,
                fg="white",
                relief=tk.RAISED,
                borderwidth=2,
                cursor="hand2",
                padx=15,
                pady=10,
                width=15
            )
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            row2_frame.grid_columnconfigure(i, weight=1)
        
    def clear_results(self):
        """Limpio el área de resultados"""
        self.result_text.delete(1.0, tk.END)
        
    def show_message(self, message, success=True):
        """Muestro un mensaje en el área de resultados"""
        self.clear_results()
        color = self.success_color if success else self.danger_color
        self.result_text.insert(tk.END, message)
        self.result_text.tag_configure("center", justify='center', foreground=color)
        self.result_text.tag_add("center", "1.0", "end")
    
    def mostrar_grafica(self, figura, titulo=""):
        """Muestra una gráfica en una ventana nueva"""
        graph_dialog = tk.Toplevel(self.root)
        graph_dialog.title(f"Gráfica - {titulo}")
        graph_dialog.geometry("800x600")
        
        # Crear el lienzo para la gráfica
        canvas = FigureCanvasTkAgg(figura, master=graph_dialog)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Botón para guardar la gráfica
        def guardar_grafica():
            nombre_archivo = f"graficas/{titulo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            figura.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Gráfica guardada", f"Gráfica guardada como:\n{nombre_archivo}")
        
        tk.Button(graph_dialog, text="💾 Guardar Gráfica", command=guardar_grafica,
                 bg="#4CAF50", fg="white", padx=10, pady=5).pack(pady=10)
    
    def obtener_color_confiabilidad(self, confiabilidad: float) -> str:
        """Obtiene color según nivel de confiabilidad"""
        if confiabilidad >= 80:
            return "#27ae60"  # Verde - Alta confiabilidad
        elif confiabilidad >= 60:
            return "#f39c12"  # Naranja - Confiabilidad media
        elif confiabilidad >= 40:
            return "#e67e22"  # Naranja oscuro - Baja confiabilidad
        else:
            return "#e74c3c"  # Rojo - Muy baja confiabilidad
    
    def actualizar_estadisticas(self):
        """Esta función actualiza las estadísticas en la barra de estado"""
        try:
            # Obtengo el total de clientes
            cursor = self.taller.db.execute_query('SELECT COUNT(*) FROM clientes')
            total_clientes = cursor.fetchone()[0] or 0
            
            # Obtengo el total de vehículos
            cursor = self.taller.db.execute_query('SELECT COUNT(*) FROM vehiculos')
            total_vehiculos = cursor.fetchone()[0] or 0
            
            # Obtengo el total de órdenes
            cursor = self.taller.db.execute_query('SELECT COUNT(*) FROM ordenes_trabajo')
            total_ordenes = cursor.fetchone()[0] or 0
            
            # Obtengo las órdenes del último mes
            fecha_hace_30_dias = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            cursor = self.taller.db.execute_query(
                'SELECT COUNT(*) FROM ordenes_trabajo WHERE fecha_fin >= ?',
                (fecha_hace_30_dias,)
            )
            ordenes_ultimo_mes = cursor.fetchone()[0] or 0
            
            # Creo el texto para la barra de estado con emojis y datos
            texto_estadisticas = (
                f"📊 Clientes: {total_clientes} | "
                f"🚗 Vehículos: {total_vehiculos} | "
                f"📋 Órdenes: {total_ordenes} | "
                f"📅 Último mes: {ordenes_ultimo_mes} | "
                f"✅ Sistema activo"
            )
            
            # Actualizo la barra de estado
            self.status_bar.config(text=texto_estadisticas)
            
            # Programo la próxima actualización en 30 segundos
            self.root.after(30000, self.actualizar_estadisticas)
            
        except Exception as e:
            # Si hay algún error, muestro un mensaje simple
            self.status_bar.config(text="✅ Sistema Taller SEYMO | © 2025")
            # Reintento en 60 segundos
            self.root.after(60000, self.actualizar_estadisticas)
        
    # ==========================================================================
    # FUNCIONES PRINCIPALES DEL PROGRAMA
    # ==========================================================================
    
    def registrar_cliente(self):
        """Muestra una ventana para registrar un nuevo cliente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar Nuevo Cliente")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()  # Hago que esta ventana sea la principal
        
        # Variables para guardar lo que escriba el usuario
        nombre_var = tk.StringVar()
        telefono_var = tk.StringVar()
        nit_var = tk.StringVar()
        
        def guardar():
            """Esta función se ejecuta cuando el usuario hace clic en Guardar"""
            try:
                # Valido que haya escrito un nombre
                if not nombre_var.get().strip():
                    messagebox.showerror("Error", "El nombre del cliente es obligatorio")
                    return
                
                # Valido el teléfono si lo escribió
                telefono = None
                if telefono_var.get().strip():
                    telefono = self.taller.validator.validar_telefono(telefono_var.get())
                    if not telefono:
                        messagebox.showerror("Error", "Teléfono inválido")
                        return
                
                # Valido el NIT si lo escribió
                nit = None
                if nit_var.get().strip():
                    nit = self.taller.validator.validar_nit(nit_var.get())
                    if not nit:
                        messagebox.showerror("Error", "NIT inválido")
                        return
                
                # Agrego el cliente a la base de datos
                cliente_id = self.taller.clientes.agregar_cliente(
                    nombre_var.get().strip(),
                    telefono,
                    nit
                )
                
                # Muestro un mensaje de éxito
                self.show_message(f"✅ Cliente registrado exitosamente\nID: {cliente_id}")
                dialog.destroy()  # Cierro la ventana
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Creo los elementos de la ventana
        ttk.Label(dialog, text="👤 REGISTRAR NUEVO CLIENTE", font=("Arial", 12, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Nombre completo:").pack(pady=5)
        ttk.Entry(dialog, textvariable=nombre_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="Teléfono (opcional):").pack(pady=5)
        ttk.Entry(dialog, textvariable=telefono_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="NIT (opcional):").pack(pady=5)
        ttk.Entry(dialog, textvariable=nit_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Guardar", command=guardar).pack(pady=20)
    
    def registrar_vehiculo(self):
        """Muestra una ventana para registrar un nuevo vehículo"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar Nuevo Vehículo")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables para los datos del vehículo
        cliente_id_var = tk.StringVar()
        marca_var = tk.StringVar()
        modelo_var = tk.StringVar()
        año_var = tk.StringVar()
        placa_var = tk.StringVar()
        color_var = tk.StringVar()
        
        def buscar_cliente():
            """Muestra una ventana para buscar el cliente dueño del vehículo"""
            search_dialog = tk.Toplevel(dialog)
            search_dialog.title("Buscar Cliente")
            search_dialog.geometry("500x400")
            
            ttk.Label(search_dialog, text="Buscar cliente por nombre:").pack(pady=10)
            search_var = tk.StringVar()
            ttk.Entry(search_dialog, textvariable=search_var, width=40).pack(pady=5)
            
            # Lista para mostrar los resultados
            listbox = tk.Listbox(search_dialog, width=60, height=15)
            scrollbar = ttk.Scrollbar(search_dialog)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            
            def perform_search():
                """Busca clientes cuando el usuario escribe"""
                listbox.delete(0, tk.END)
                clientes = self.taller.clientes.buscar_cliente_por_nombre(search_var.get())
                for cliente in clientes:
                    listbox.insert(tk.END, f"ID: {cliente[0]} | Nombre: {cliente[1]} | Tel: {cliente[2] or 'N/A'} | NIT: {cliente[3] or 'N/A'}")
            
            def seleccionar():
                """Selecciona el cliente cuando el usuario hace clic"""
                seleccion = listbox.curselection()
                if seleccion:
                    texto = listbox.get(seleccion[0])
                    cliente_id = int(texto.split("ID: ")[1].split(" |")[0])
                    cliente_id_var.set(str(cliente_id))
                    search_dialog.destroy()
            
            ttk.Button(search_dialog, text="Buscar", command=perform_search).pack(pady=5)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            ttk.Button(search_dialog, text="Seleccionar", command=seleccionar).pack(pady=10)
        
        def guardar():
            """Guarda el vehículo en la base de datos"""
            try:
                # Valido que haya seleccionado un cliente
                if not cliente_id_var.get().strip():
                    messagebox.showerror("Error", "Debe seleccionar un cliente")
                    return
                
                # Valido los datos obligatorios
                if not marca_var.get().strip():
                    messagebox.showerror("Error", "La marca es obligatoria")
                    return
                
                if not modelo_var.get().strip():
                    messagebox.showerror("Error", "El modelo es obligatorio")
                    return
                
                if not año_var.get().strip():
                    messagebox.showerror("Error", "El año es obligatorio")
                    return
                
                # Valido que el año sea un número válido
                año = int(año_var.get())
                if not self.taller.validator.validar_año_vehiculo(año):
                    messagebox.showerror("Error", "Año del vehículo inválido")
                    return
                
                if not placa_var.get().strip():
                    messagebox.showerror("Error", "La placa es obligatoria")
                    return
                
                # Valido que la placa no exista ya
                placa = placa_var.get().strip().upper()
                if self.taller.vehiculos.placa_existe(placa):
                    messagebox.showerror("Error", "Ya existe un vehículo con esa placa")
                    return
                
                # Agrego el vehículo a la base de datos
                resultado = self.taller.vehiculos.agregar_vehiculo(
                    int(cliente_id_var.get()),
                    marca_var.get().strip(),
                    modelo_var.get().strip(),
                    año,
                    placa,
                    color_var.get().strip() or None
                )
                
                self.show_message(resultado)
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "El año debe ser un número válido")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Creo el formulario para registrar el vehículo
        ttk.Label(dialog, text="🚗 REGISTRAR NUEVO VEHÍCULO", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Sección para seleccionar cliente
        frame_cliente = ttk.LabelFrame(dialog, text="Cliente")
        frame_cliente.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(frame_cliente, text="ID Cliente:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(frame_cliente, textvariable=cliente_id_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_cliente, text="Buscar Cliente", command=buscar_cliente).pack(side=tk.LEFT, padx=5)
        
        # Campos para los datos del vehículo
        ttk.Label(dialog, text="Marca:").pack(pady=5)
        ttk.Entry(dialog, textvariable=marca_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="Modelo:").pack(pady=5)
        ttk.Entry(dialog, textvariable=modelo_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="Año:").pack(pady=5)
        ttk.Entry(dialog, textvariable=año_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="Placa:").pack(pady=5)
        ttk.Entry(dialog, textvariable=placa_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="Color (opcional):").pack(pady=5)
        ttk.Entry(dialog, textvariable=color_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Guardar Vehículo", command=guardar).pack(pady=20)
    
    def registrar_empleado(self):
        """Muestra una ventana para registrar un nuevo empleado"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar Nuevo Empleado")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables para los datos del empleado
        nombre_var = tk.StringVar()
        telefono_var = tk.StringVar()
        
        def guardar():
            """Guarda el empleado en la base de datos"""
            try:
                if not nombre_var.get().strip():
                    messagebox.showerror("Error", "El nombre del empleado es obligatorio")
                    return
                
                # Valido el teléfono
                telefono = self.taller.validator.validar_telefono(telefono_var.get())
                if not telefono:
                    messagebox.showerror("Error", "Teléfono inválido (7-15 dígitos)")
                    return
                
                # Agrego el empleado a la base de datos
                resultado = self.taller.empleados.agregar_empleado(
                    nombre_var.get().strip(),
                    telefono
                )
                
                self.show_message(resultado)
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Creo el formulario
        ttk.Label(dialog, text="👷 REGISTRAR NUEVO EMPLEADO", font=("Arial", 12, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Nombre completo:").pack(pady=5)
        ttk.Entry(dialog, textvariable=nombre_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="Teléfono:").pack(pady=5)
        ttk.Entry(dialog, textvariable=telefono_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Guardar", command=guardar).pack(pady=20)
    
    def nueva_orden(self):
        """Muestra una ventana para crear una nueva orden de trabajo"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Nueva Orden de Trabajo")
        dialog.geometry("700x750")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables para los datos de la orden
        orden_var = tk.StringVar()
        descripcion_var = tk.StringVar()
        tipo_servicio_var = tk.StringVar()
        horas_var = tk.StringVar()
        repuestos_var = tk.StringVar()
        mano_obra_var = tk.StringVar()
        kilometraje_var = tk.StringVar()
        unidad_km_var = tk.StringVar(value="km")
        fecha_fin_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        
        # Variables para recordar lo que seleccioné
        cliente_id = None
        vehiculo_id = None
        empleado_id = None
        
        # Frame principal
        main_content = tk.Frame(dialog)
        main_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Título
        tk.Label(main_content, text="📋 NUEVA ORDEN DE TRABAJO", 
                font=("Arial", 12, "bold")).pack(pady=10)
        
        # Frame para las selecciones (cliente, vehículo, empleado)
        frame_selecciones = tk.LabelFrame(main_content, text="Selecciones")
        frame_selecciones.pack(fill=tk.X, pady=10, padx=5)
        
        # Labels para mostrar lo que seleccioné
        cliente_label = tk.Label(frame_selecciones, text="Cliente: No seleccionado", anchor="w")
        vehiculo_label = tk.Label(frame_selecciones, text="Vehículo: No seleccionado", anchor="w")
        empleado_label = tk.Label(frame_selecciones, text="Empleado: No seleccionado", anchor="w")
        
        def buscar_cliente():
            """Muestra una ventana para buscar cliente"""
            nonlocal cliente_id
            search_dialog = tk.Toplevel(dialog)
            search_dialog.title("Buscar Cliente")
            search_dialog.geometry("500x400")
            
            ttk.Label(search_dialog, text="Buscar cliente por nombre:").pack(pady=10)
            search_var = tk.StringVar()
            ttk.Entry(search_dialog, textvariable=search_var, width=40).pack(pady=5)
            
            listbox = tk.Listbox(search_dialog, width=60, height=15)
            scrollbar = ttk.Scrollbar(search_dialog)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            
            def perform_search():
                """Busca clientes cuando el usuario escribe"""
                listbox.delete(0, tk.END)
                clientes = self.taller.clientes.buscar_cliente_por_nombre(search_var.get())
                for cliente in clientes:
                    listbox.insert(tk.END, f"ID: {cliente[0]} | Nombre: {cliente[1]} | Tel: {cliente[2] or 'N/A'}")
            
            def seleccionar():
                """Selecciona el cliente"""
                nonlocal cliente_id, vehiculo_id
                seleccion = listbox.curselection()
                if seleccion:
                    texto = listbox.get(seleccion[0])
                    cliente_id = int(texto.split("ID: ")[1].split(" |")[0])
                    cliente_label.config(text=f"Cliente: ID {cliente_id} seleccionado")
                    # Reseteo el vehículo cuando cambio de cliente
                    vehiculo_id = None
                    vehiculo_label.config(text="Vehículo: No seleccionado")
                    search_dialog.destroy()
            
            ttk.Button(search_dialog, text="Buscar", command=perform_search).pack(pady=5)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            ttk.Button(search_dialog, text="Seleccionar", command=seleccionar).pack(pady=10)
        
        def seleccionar_vehiculo():
            """Muestra una ventana para seleccionar vehículo del cliente"""
            nonlocal vehiculo_id
            if not cliente_id:
                messagebox.showwarning("Advertencia", "Primero seleccione un cliente")
                return
            
            # Obtengo los vehículos del cliente seleccionado
            vehiculos = self.taller.vehiculos.obtener_vehiculos_cliente(cliente_id)
            
            if not vehiculos:
                messagebox.showinfo("Información", "Este cliente no tiene vehículos registrados")
                return
            
            search_dialog = tk.Toplevel(dialog)
            search_dialog.title("Seleccionar Vehículo")
            search_dialog.geometry("500x400")
            
            listbox = tk.Listbox(search_dialog, width=60, height=15)
            scrollbar = tk.Scrollbar(search_dialog)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            
            # Muestro los vehículos del cliente
            for vehiculo in vehiculos:
                listbox.insert(tk.END, f"ID: {vehiculo[0]} | {vehiculo[1]} {vehiculo[2]} {vehiculo[3]} | Placa: {vehiculo[4]}")
            
            def seleccionar():
                """Selecciona el vehículo"""
                nonlocal vehiculo_id
                seleccion = listbox.curselection()
                if seleccion:
                    texto = listbox.get(seleccion[0])
                    vehiculo_id = int(texto.split("ID: ")[1].split(" |")[0])
                    vehiculo_label.config(text=f"Vehículo: ID {vehiculo_id} seleccionado")
                    search_dialog.destroy()
            
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            ttk.Button(search_dialog, text="Seleccionar", command=seleccionar).pack(pady=10)
        
        def seleccionar_empleado():
            """Muestra una ventana para seleccionar empleado"""
            nonlocal empleado_id
            empleados = self.taller.empleados.listar_empleados()
            
            if not empleados:
                messagebox.showinfo("Información", "No hay empleados registrados")
                return
            
            search_dialog = tk.Toplevel(dialog)
            search_dialog.title("Seleccionar Empleado")
            search_dialog.geometry("500x400")
            
            listbox = tk.Listbox(search_dialog, width=60, height=15)
            scrollbar = tk.Scrollbar(search_dialog)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            
            # Muestro todos los empleados
            for empleado in empleados:
                listbox.insert(tk.END, f"ID: {empleado[0]} | {empleado[1]} | Tel: {empleado[2]}")
            
            def seleccionar():
                """Selecciona el empleado"""
                nonlocal empleado_id
                seleccion = listbox.curselection()
                if seleccion:
                    texto = listbox.get(seleccion[0])
                    empleado_id = int(texto.split("ID: ")[1].split(" |")[0])
                    empleado_label.config(text=f"Empleado: ID {empleado_id} seleccionado")
                    search_dialog.destroy()
            
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            ttk.Button(search_dialog, text="Seleccionar", command=seleccionar).pack(pady=10)
        
        def guardar():
            """Guarda la orden en la base de datos"""
            try:
                # Valido que haya seleccionado todo
                if not cliente_id:
                    messagebox.showerror("Error", "Debe seleccionar un cliente")
                    return
                
                if not vehiculo_id:
                    messagebox.showerror("Error", "Debe seleccionar un vehículo")
                    return
                
                if not empleado_id:
                    messagebox.showerror("Error", "Debe seleccionar un empleado")
                    return
                
                if not orden_var.get().strip():
                    messagebox.showerror("Error", "El número de orden es obligatorio")
                    return
                
                # Valido que el número de orden sea un número
                try:
                    numero_orden = int(orden_var.get())
                except ValueError:
                    messagebox.showerror("Error", "El número de orden debe ser un número")
                    return
                
                # Valido que el número de orden no exista ya
                if self.taller.ordenes.orden_existe(numero_orden):
                    respuesta = messagebox.askyesno(
                        "Orden existente", 
                        f"La orden #{numero_orden} ya existe. ¿Desea usar un número diferente?"
                    )
                    if not respuesta:
                        return
                    messagebox.showinfo("Información", "Por favor use un número de orden diferente")
                    return
                
                # Valido los campos obligatorios
                descripcion = descripcion_var.get().strip()
                if not descripcion:
                    messagebox.showerror("Error", "La descripción es obligatoria")
                    return
                
                tipo_servicio = tipo_servicio_var.get().strip()
                if not tipo_servicio:
                    messagebox.showerror("Error", "El tipo de servicio es obligatorio")
                    return
                
                # Valido la fecha de finalización
                fecha_fin = fecha_fin_var.get().strip()
                if not fecha_fin:
                    messagebox.showerror("Error", "La fecha de finalización es obligatoria")
                    return
                
                # Valido que los números sean correctos
                try:
                    horas = float(horas_var.get() or 0)
                    repuestos = float(repuestos_var.get() or 0)
                    mano_obra = float(mano_obra_var.get() or 0)
                    kilometraje = float(kilometraje_var.get() or 0)
                except ValueError:
                    messagebox.showerror("Error", "Los valores numéricos deben ser válidos")
                    return
                
                unidad_km = unidad_km_var.get().strip() or "km"
                
                # Agrego la orden a la base de datos
                resultado = self.taller.ordenes.agregar_orden(
                    numero_orden,
                    vehiculo_id,
                    empleado_id,
                    descripcion,
                    tipo_servicio,
                    horas,
                    repuestos,
                    mano_obra,
                    kilometraje,
                    unidad_km,
                    fecha_fin
                )
                
                self.show_message(resultado)
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Botones para seleccionar cliente, vehículo y empleado
        tk.Button(frame_selecciones, text="1. Seleccionar Cliente", 
                  command=buscar_cliente).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        cliente_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        tk.Button(frame_selecciones, text="2. Seleccionar Vehículo", 
                  command=seleccionar_vehiculo).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        vehiculo_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        tk.Button(frame_selecciones, text="3. Seleccionar Empleado", 
                  command=seleccionar_empleado).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        empleado_label.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Frame para los campos de la orden
        fields_frame = tk.Frame(main_content)
        fields_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Defino todos los campos que necesita la orden
        fields = [
            ("Número de orden:", orden_var),
            ("Fecha de finalización (YYYY-MM-DD):", fecha_fin_var),
            ("Descripción del trabajo:", descripcion_var),
            ("Tipo de servicio:", tipo_servicio_var),
            ("Horas trabajadas:", horas_var),
            ("Costo repuestos (Q):", repuestos_var),
            ("Costo mano de obra (Q):", mano_obra_var),
            ("Kilometraje:", kilometraje_var),
            ("Unidad kilometraje:", unidad_km_var)
        ]
        
        # Creo cada campo del formulario
        for label_text, var in fields:
            frame = tk.Frame(fields_frame)
            frame.pack(fill=tk.X, pady=5)
            tk.Label(frame, text=label_text, width=30, anchor="w").pack(side=tk.LEFT, padx=5)
            tk.Entry(frame, textvariable=var, width=30).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Botón para guardar la orden
        tk.Button(main_content, text="Guardar Orden", command=guardar, 
                  bg="#4CAF50", fg="white", padx=20, pady=10, font=("Arial", 10, "bold")).pack(pady=20)
    
    def buscar_cliente(self):
        """Muestra una ventana para buscar clientes"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Buscar Cliente")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variable para lo que escriba el usuario
        search_var = tk.StringVar()
        resultados_text = scrolledtext.ScrolledText(dialog, height=25, width=70)
        
        def buscar():
            """Busca clientes cuando el usuario hace clic en Buscar"""
            resultados_text.delete(1.0, tk.END)
            clientes = self.taller.clientes.buscar_cliente_por_nombre(search_var.get())
            
            if not clientes:
                resultados_text.insert(tk.END, "❌ No se encontraron clientes")
                return
            
            # Muestro cada cliente encontrado
            for cliente in clientes:
                resultados_text.insert(tk.END, f"\n{'═'*60}\n")
                resultados_text.insert(tk.END, f"📋 ID: {cliente[0]}\n")
                resultados_text.insert(tk.END, f"👤 Nombre: {cliente[1]}\n")
                resultados_text.insert(tk.END, f"📞 Teléfono: {cliente[2] or 'No tiene'}\n")
                resultados_text.insert(tk.END, f"🏢 NIT: {cliente[3] or 'No tiene'}\n")
                
                # Muestro los vehículos del cliente
                vehiculos = self.taller.vehiculos.obtener_vehiculos_cliente(cliente[0])
                if vehiculos:
                    resultados_text.insert(tk.END, f"\n🚗 VEHÍCULOS ({len(vehiculos)}):\n")
                    for vehiculo in vehiculos:
                        resultados_text.insert(tk.END, f"   • {vehiculo[1]} {vehiculo[2]} {vehiculo[3]} - Placa: {vehiculo[4]}\n")
                else:
                    resultados_text.insert(tk.END, "\n❌ Este cliente no tiene vehículos registrados.\n")
            
            resultados_text.insert(tk.END, f"\n{'═'*60}\n")
        
        # Creo los elementos de la ventana
        ttk.Label(dialog, text="🔍 BUSCAR CLIENTE", font=("Arial", 12, "bold")).pack(pady=10)
        
        ttk.Label(dialog, text="Nombre del cliente:").pack(pady=5)
        ttk.Entry(dialog, textvariable=search_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Buscar", command=buscar).pack(pady=10)
        
        resultados_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
    
    def historial_vehiculo(self):
        """Muestra el historial de un vehículo"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Historial de Vehículo")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variable para la placa
        placa_var = tk.StringVar()
        resultados_text = scrolledtext.ScrolledText(dialog, height=30, width=80)
        
        def buscar_por_placa():
            """Busca un vehículo por su placa"""
            resultados_text.delete(1.0, tk.END)
            placa = placa_var.get().strip().upper()
            
            if not placa:
                resultados_text.insert(tk.END, "❌ Ingrese una placa para buscar")
                return
            
            # Busco el vehículo por placa
            cursor = self.taller.db.execute_query(
                'SELECT id FROM vehiculos WHERE placa = ?', 
                (placa,)
            )
            resultado = cursor.fetchone()
            
            if not resultado:
                resultados_text.insert(tk.END, f"❌ No se encontró vehículo con placa: {placa}")
                return
            
            vehiculo_id = resultado[0]
            
            # Obtengo los detalles del vehículo
            detalles = self.taller.vehiculos.detalles_vehiculo(vehiculo_id)
            
            if not detalles:
                resultados_text.insert(tk.END, f"❌ Error al obtener detalles del vehículo")
                return
            
            vehiculo_info, ordenes = detalles['vehiculo'], detalles['ordenes']
            
            # Muestro la información del vehículo
            resultados_text.insert(tk.END, f"\n{'═'*60}\n")
            resultados_text.insert(tk.END, f"🚗 DETALLES DEL VEHÍCULO\n")
            resultados_text.insert(tk.END, f"{'═'*60}\n\n")
            resultados_text.insert(tk.END, f"📋 Marca: {vehiculo_info[0]}\n")
            resultados_text.insert(tk.END, f"📋 Modelo: {vehiculo_info[1]}\n")
            resultados_text.insert(tk.END, f"📅 Año: {vehiculo_info[2]}\n")
            resultados_text.insert(tk.END, f"🏷️  Placa: {vehiculo_info[3]}\n")
            resultados_text.insert(tk.END, f"🎨 Color: {vehiculo_info[4] or 'No especificado'}\n")
            resultados_text.insert(tk.END, f"👤 Cliente: {vehiculo_info[5]}\n")
            resultados_text.insert(tk.END, f"📞 Teléfono: {vehiculo_info[6] or 'No tiene'}\n")
            resultados_text.insert(tk.END, f"🏢 NIT: {vehiculo_info[7] or 'No tiene'}\n")
            
            # Muestro el historial de órdenes
            if ordenes:
                resultados_text.insert(tk.END, f"\n{'═'*60}\n")
                resultados_text.insert(tk.END, f"🔧 HISTORIAL DE ÓRDENES ({len(ordenes)})\n")
                resultados_text.insert(tk.END, f"{'═'*60}\n\n")
                
                for orden in ordenes:
                    resultados_text.insert(tk.END, f"📋 ORDEN #{orden[0]}\n")
                    resultados_text.insert(tk.END, f"   📅 Fecha: {orden[1] or 'Sin fecha'}\n")
                    resultados_text.insert(tk.END, f"   🔧 Servicio: {orden[3]}\n")
                    resultados_text.insert(tk.END, f"   💰 Precio: Q{orden[4]:.2f}\n")
                    resultados_text.insert(tk.END, f"   🛣️  Kilometraje: {orden[5]} {orden[6]}\n")
                    resultados_text.insert(tk.END, f"   👷 Empleado: {orden[7] or 'No asignado'}\n")
                    resultados_text.insert(tk.END, f"   📝 Descripción: {orden[2][:100]}...\n")
                    resultados_text.insert(tk.END, f"{'─'*50}\n")
            else:
                resultados_text.insert(tk.END, f"\n❌ Este vehículo no tiene órdenes de trabajo registradas.\n")
        
        def buscar_interactivo():
            """Busca primero un cliente y luego sus vehículos"""
            # Diálogo para buscar cliente
            search_dialog = tk.Toplevel(dialog)
            search_dialog.title("Buscar Cliente")
            search_dialog.geometry("500x400")
            
            ttk.Label(search_dialog, text="Buscar cliente por nombre:").pack(pady=10)
            search_var = tk.StringVar()
            ttk.Entry(search_dialog, textvariable=search_var, width=40).pack(pady=5)
            
            listbox = tk.Listbox(search_dialog, width=60, height=15)
            scrollbar = ttk.Scrollbar(search_dialog)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            
            def perform_search():
                """Busca clientes"""
                listbox.delete(0, tk.END)
                clientes = self.taller.clientes.buscar_cliente_por_nombre(search_var.get())
                for cliente in clientes:
                    listbox.insert(tk.END, f"ID: {cliente[0]} | Nombre: {cliente[1]}")
            
            def seleccionar_cliente():
                """Selecciona un cliente"""
                seleccion = listbox.curselection()
                if not seleccion:
                    return
                
                texto = listbox.get(seleccion[0])
                cliente_id = int(texto.split("ID: ")[1].split(" |")[0])
                search_dialog.destroy()
                
                # Ahora muestro los vehículos del cliente
                mostrar_vehiculos_cliente(cliente_id)
            
            def mostrar_vehiculos_cliente(cliente_id):
                """Muestra los vehículos de un cliente"""
                vehiculos = self.taller.vehiculos.obtener_vehiculos_cliente(cliente_id)
                
                if not vehiculos:
                    messagebox.showinfo("Información", "Este cliente no tiene vehículos")
                    return
                
                vehiculo_dialog = tk.Toplevel(dialog)
                vehiculo_dialog.title("Seleccionar Vehículo")
                vehiculo_dialog.geometry("500x400")
                
                listbox2 = tk.Listbox(vehiculo_dialog, width=60, height=15)
                scrollbar2 = ttk.Scrollbar(vehiculo_dialog)
                listbox2.config(yscrollcommand=scrollbar2.set)
                scrollbar2.config(command=listbox2.yview)
                
                for vehiculo in vehiculos:
                    listbox2.insert(tk.END, f"ID: {vehiculo[0]} | {vehiculo[1]} {vehiculo[2]} | Placa: {vehiculo[4]}")
                
                def seleccionar_vehiculo():
                    """Selecciona un vehículo"""
                    seleccion = listbox2.curselection()
                    if seleccion:
                        texto = listbox2.get(seleccion[0])
                        vehiculo_id = int(texto.split("ID: ")[1].split(" |")[0])
                        placa = texto.split("Placa: ")[1]
                        placa_var.set(placa)
                        vehiculo_dialog.destroy()
                        buscar_por_placa()
                
                listbox2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
                scrollbar2.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
                ttk.Button(vehiculo_dialog, text="Seleccionar", command=seleccionar_vehiculo).pack(pady=10)
            
            ttk.Button(search_dialog, text="Buscar", command=perform_search).pack(pady=5)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            ttk.Button(search_dialog, text="Seleccionar Cliente", command=seleccionar_cliente).pack(pady=10)
        
        # Creo los elementos de la ventana
        ttk.Label(dialog, text="🔍 HISTORIAL DE VEHÍCULO", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Opción 1: Buscar por placa directamente
        frame_placa = ttk.Frame(dialog)
        frame_placa.pack(pady=10)
        ttk.Label(frame_placa, text="Placa del vehículo:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(frame_placa, textvariable=placa_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_placa, text="Buscar por Placa", command=buscar_por_placa).pack(side=tk.LEFT, padx=5)
        
        # Opción 2: Buscar primero el cliente
        ttk.Label(dialog, text="O buscar por cliente:").pack(pady=5)
        ttk.Button(dialog, text="Buscar Cliente Primero", command=buscar_interactivo).pack(pady=10)
        
        resultados_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
    
    def editar_cliente(self):
        """Muestra una ventana para editar un cliente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Cliente")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables para los datos del cliente
        cliente_id_var = tk.StringVar()
        nombre_var = tk.StringVar()
        telefono_var = tk.StringVar()
        nit_var = tk.StringVar()
        
        def buscar_cliente():
            """Muestra una ventana para buscar el cliente a editar"""
            search_dialog = tk.Toplevel(dialog)
            search_dialog.title("Buscar Cliente para Editar")
            search_dialog.geometry("500x400")
            
            ttk.Label(search_dialog, text="Buscar cliente por nombre:").pack(pady=10)
            search_var = tk.StringVar()
            ttk.Entry(search_dialog, textvariable=search_var, width=40).pack(pady=5)
            
            listbox = tk.Listbox(search_dialog, width=60, height=15)
            scrollbar = ttk.Scrollbar(search_dialog)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            
            def perform_search():
                """Busca clientes"""
                listbox.delete(0, tk.END)
                clientes = self.taller.clientes.buscar_cliente_por_nombre(search_var.get())
                for cliente in clientes:
                    listbox.insert(tk.END, f"ID: {cliente[0]} | Nombre: {cliente[1]} | Tel: {cliente[2] or 'N/A'}")
            
            def seleccionar():
                """Selecciona un cliente y carga sus datos"""
                seleccion = listbox.curselection()
                if seleccion:
                    texto = listbox.get(seleccion[0])
                    cliente_id = int(texto.split("ID: ")[1].split(" |")[0])
                    cliente_id_var.set(str(cliente_id))
                    
                    # Cargo los datos del cliente en los campos
                    detalles = self.taller.clientes.detalles_cliente(cliente_id)
                    if detalles:
                        cliente_info = detalles['cliente']
                        nombre_var.set(cliente_info[0])
                        telefono_var.set(cliente_info[1] or "")
                        nit_var.set(cliente_info[2] or "")
                    
                    search_dialog.destroy()
            
            ttk.Button(search_dialog, text="Buscar", command=perform_search).pack(pady=5)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            ttk.Button(search_dialog, text="Seleccionar", command=seleccionar).pack(pady=10)
        
        def guardar():
            """Guarda los cambios del cliente"""
            try:
                if not cliente_id_var.get().strip():
                    messagebox.showerror("Error", "Debe seleccionar un cliente")
                    return
                
                cliente_id = int(cliente_id_var.get())
                
                if not nombre_var.get().strip():
                    messagebox.showerror("Error", "El nombre del cliente es obligatorio")
                    return
                
                # Valido el teléfono
                telefono = None
                if telefono_var.get().strip():
                    telefono = self.taller.validator.validar_telefono(telefono_var.get())
                    if not telefono:
                        messagebox.showerror("Error", "Teléfono inválido")
                        return
                
                # Valido el NIT
                nit = None
                if nit_var.get().strip():
                    nit = self.taller.validator.validar_nit(nit_var.get())
                    if not nit:
                        messagebox.showerror("Error", "NIT inválido")
                        return
                
                # Actualizo el cliente en la base de datos
                resultado = self.taller.clientes.editar_cliente(
                    cliente_id,
                    nombre_var.get().strip(),
                    telefono,
                    nit
                )
                
                self.show_message(resultado)
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Creo los elementos de la ventana
        ttk.Label(dialog, text="✏️ EDITAR CLIENTE", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Botón para buscar cliente
        ttk.Button(dialog, text="Buscar Cliente", command=buscar_cliente).pack(pady=10)
        
        ttk.Label(dialog, text="ID Cliente:").pack(pady=5)
        ttk.Entry(dialog, textvariable=cliente_id_var, width=40, state='readonly').pack(pady=5)
        
        ttk.Label(dialog, text="Nombre completo:").pack(pady=5)
        ttk.Entry(dialog, textvariable=nombre_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="Teléfono:").pack(pady=5)
        ttk.Entry(dialog, textvariable=telefono_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="NIT:").pack(pady=5)
        ttk.Entry(dialog, textvariable=nit_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Guardar Cambios", command=guardar).pack(pady=20)
    
    def editar_empleado(self):
        """Muestra una ventana para editar un empleado"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Empleado")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables para los datos del empleado
        empleado_id_var = tk.StringVar()
        nombre_var = tk.StringVar()
        telefono_var = tk.StringVar()
        
        def cargar_empleados():
            """Muestra una lista de empleados para seleccionar"""
            empleados = self.taller.empleados.listar_empleados()
            
            if not empleados:
                messagebox.showinfo("Información", "No hay empleados registrados")
                return
            
            search_dialog = tk.Toplevel(dialog)
            search_dialog.title("Seleccionar Empleado")
            search_dialog.geometry("500x400")
            
            listbox = tk.Listbox(search_dialog, width=60, height=15)
            scrollbar = ttk.Scrollbar(search_dialog)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            
            # Muestro todos los empleados
            for empleado in empleados:
                listbox.insert(tk.END, f"ID: {empleado[0]} | {empleado[1]} | Tel: {empleado[2]}")
            
            def seleccionar():
                """Selecciona un empleado y carga sus datos"""
                seleccion = listbox.curselection()
                if seleccion:
                    texto = listbox.get(seleccion[0])
                    empleado_id = int(texto.split("ID: ")[1].split(" |")[0])
                    empleado_id_var.set(str(empleado_id))
                    
                    # Extraigo el nombre y teléfono del texto
                    nombre = texto.split("| ")[1].split(" |")[0]
                    telefono = texto.split("Tel: ")[1]
                    nombre_var.set(nombre)
                    telefono_var.set(telefono)
                    
                    search_dialog.destroy()
            
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            ttk.Button(search_dialog, text="Seleccionar", command=seleccionar).pack(pady=10)
        
        def guardar():
            """Guarda los cambios del empleado"""
            try:
                if not empleado_id_var.get().strip():
                    messagebox.showerror("Error", "Debe seleccionar un empleado")
                    return
                
                empleado_id = int(empleado_id_var.get())
                
                if not nombre_var.get().strip():
                    messagebox.showerror("Error", "El nombre del empleado es obligatorio")
                    return
                
                # Valido el teléfono
                telefono = self.taller.validator.validar_telefono(telefono_var.get())
                if not telefono:
                    messagebox.showerror("Error", "Teléfono inválido")
                    return
                
                # Actualizo el empleado en la base de datos
                resultado = self.taller.empleados.editar_empleado(
                    empleado_id,
                    nombre_var.get().strip(),
                    telefono
                )
                
                self.show_message(resultado)
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Creo los elementos de la ventana
        ttk.Label(dialog, text="✏️ EDITAR EMPLEADO", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Botón para seleccionar empleado
        ttk.Button(dialog, text="Seleccionar Empleado", command=cargar_empleados).pack(pady=10)
        
        ttk.Label(dialog, text="ID Empleado:").pack(pady=5)
        ttk.Entry(dialog, textvariable=empleado_id_var, width=40, state='readonly').pack(pady=5)
        
        ttk.Label(dialog, text="Nombre completo:").pack(pady=5)
        ttk.Entry(dialog, textvariable=nombre_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="Teléfono:").pack(pady=5)
        ttk.Entry(dialog, textvariable=telefono_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Guardar Cambios", command=guardar).pack(pady=20)
    
    def editar_orden(self):
        """Muestra una ventana para editar una orden de trabajo"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Orden de Trabajo")
        dialog.geometry("700x750")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables para los datos de la orden
        orden_id_var = tk.StringVar()
        fecha_fin_var = tk.StringVar()
        descripcion_var = tk.StringVar()
        tipo_servicio_var = tk.StringVar()
        horas_var = tk.StringVar()
        repuestos_var = tk.StringVar()
        mano_obra_var = tk.StringVar()
        precio_final_var = tk.StringVar()
        kilometraje_var = tk.StringVar()
        unidad_km_var = tk.StringVar(value="km")
        
        def buscar_orden():
            """Busca una orden por su número"""
            try:
                orden_id_str = simpledialog.askstring("Buscar Orden", "Ingrese el número de la orden a editar:")
                if not orden_id_str:
                    return
                
                orden_id = int(orden_id_str)
                
                # Verifico si la orden existe
                if not self.taller.ordenes.orden_existe(orden_id):
                    messagebox.showerror("Error", f"La orden #{orden_id} no existe")
                    return
                
                # Obtengo los detalles de la orden
                detalles = self.taller.ordenes.obtener_detalles_orden(orden_id)
                if not detalles:
                    messagebox.showerror("Error", "No se pudieron obtener los detalles de la orden")
                    return
                
                # Cargo los datos en los campos
                orden_id_var.set(str(detalles['id']))
                fecha_fin_var.set(detalles['fecha_fin'] or datetime.now().strftime("%Y-%m-%d"))
                descripcion_var.set(detalles['descripcion_trabajo'])
                tipo_servicio_var.set(detalles['tipo_servicio'])
                horas_var.set(str(detalles['horas_trabajadas']))
                repuestos_var.set(str(detalles['costo_repuestos']))
                mano_obra_var.set(str(detalles['costo_mano_obra']))
                precio_final_var.set(str(detalles['precio_final']))
                kilometraje_var.set(str(detalles['kilometraje']))
                unidad_km_var.set(detalles['unidad_kilometraje'])
                
                # Muestro información del vehículo y cliente
                info_text = f"Vehículo: {detalles['vehiculo_marca']} {detalles['vehiculo_modelo']} - Placa: {detalles['vehiculo_placa']}\n"
                info_text += f"Cliente: {detalles['cliente_nombre']}\n"
                info_text += f"Empleado: {detalles['empleado_nombre'] or 'No asignado'}"
                messagebox.showinfo("Orden encontrada", info_text)
                
            except ValueError:
                messagebox.showerror("Error", "El número de orden debe ser un número válido")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        def calcular_precio():
            """Calcula el precio final automáticamente"""
            try:
                repuestos = float(repuestos_var.get() or 0)
                mano_obra = float(mano_obra_var.get() or 0)
                precio_final = repuestos + mano_obra
                precio_final_var.set(f"{precio_final:.2f}")
            except:
                pass
        
        def guardar():
            """Guarda los cambios en la orden"""
            try:
                if not orden_id_var.get().strip():
                    messagebox.showerror("Error", "Primero debe buscar una orden")
                    return
                
                orden_id = int(orden_id_var.get())
                
                # Valido los campos obligatorios
                descripcion = descripcion_var.get().strip()
                if not descripcion:
                    messagebox.showerror("Error", "La descripción es obligatoria")
                    return
                
                tipo_servicio = tipo_servicio_var.get().strip()
                if not tipo_servicio:
                    messagebox.showerror("Error", "El tipo de servicio es obligatorio")
                    return
                
                fecha_fin = fecha_fin_var.get().strip()
                if not fecha_fin:
                    messagebox.showerror("Error", "La fecha de finalización es obligatoria")
                    return
                
                # Valido que los números sean correctos
                try:
                    horas_trabajadas = float(horas_var.get() or 0)
                    costo_repuestos = float(repuestos_var.get() or 0)
                    costo_mano_obra = float(mano_obra_var.get() or 0)
                    precio_final = float(precio_final_var.get() or 0)
                    kilometraje = float(kilometraje_var.get() or 0)
                except ValueError:
                    messagebox.showerror("Error", "Los valores numéricos deben ser válidos")
                    return
                
                unidad_km = unidad_km_var.get().strip() or "km"
                
                # Actualizo la orden en la base de datos
                resultado = self.taller.ordenes.editar_orden(
                    orden_id,
                    descripcion,
                    tipo_servicio,
                    horas_trabajadas,
                    costo_repuestos,
                    costo_mano_obra,
                    precio_final,
                    kilometraje,
                    unidad_km,
                    fecha_fin
                )
                
                self.show_message(resultado)
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Creo los elementos de la ventana
        ttk.Label(dialog, text="✏️ EDITAR ORDEN DE TRABAJO", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Botón para buscar orden
        tk.Button(dialog, text="Buscar Orden por Número", command=buscar_orden,
                  bg="#3498db", fg="white", padx=10, pady=5).pack(pady=10)
        
        ttk.Label(dialog, text="Número de orden:").pack(pady=5)
        ttk.Entry(dialog, textvariable=orden_id_var, width=40, state='readonly').pack(pady=5)
        
        # Frame para los campos de la orden
        fields_frame = tk.Frame(dialog)
        fields_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=20)
        
        # Defino todos los campos que necesita la orden
        fields = [
            ("Fecha de finalización (YYYY-MM-DD):", fecha_fin_var),
            ("Descripción del trabajo:", descripcion_var),
            ("Tipo de servicio:", tipo_servicio_var),
            ("Horas trabajadas:", horas_var),
            ("Costo repuestos (Q):", repuestos_var),
            ("Costo mano de obra (Q):", mano_obra_var),
            ("Precio final (Q):", precio_final_var),
            ("Kilometraje:", kilometraje_var),
            ("Unidad kilometraje:", unidad_km_var)
        ]
        
        # Creo cada campo del formulario
        for label_text, var in fields:
            frame = tk.Frame(fields_frame)
            frame.pack(fill=tk.X, pady=5)
            tk.Label(frame, text=label_text, width=30, anchor="w").pack(side=tk.LEFT, padx=5)
            entry = tk.Entry(frame, textvariable=var, width=30)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            # Conecto el cálculo automático del precio
            if label_text in ["Costo repuestos (Q):", "Costo mano de obra (Q):"]:
                entry.bind("<KeyRelease>", lambda e: calcular_precio())
        
        # Botón para guardar la orden
        tk.Button(dialog, text="Guardar Cambios", command=guardar, 
                  bg="#4CAF50", fg="white", padx=20, pady=10, font=("Arial", 10, "bold")).pack(pady=20)
    
    def menu_reportes(self):
        """Muestra el menú de reportes con gráficas"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Reportes Avanzados")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        def generar_reporte_con_graficas(periodo):
            """Genera un reporte completo con todas las gráficas"""
            reporte = self.taller.reportes.reporte_periodo(periodo)
            
            # Muestro el reporte en el área de resultados
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*60}\n")
            self.result_text.insert(tk.END, f"📊 REPORTE {periodo.upper()}\n")
            self.result_text.insert(tk.END, f"{'='*60}\n\n")
            self.result_text.insert(tk.END, f"📅 Período: {reporte['fecha_inicio']} al {datetime.now().date()}\n\n")
            self.result_text.insert(tk.END, f"💰 Ganancias totales: Q{reporte['ganancias']:.2f}\n")
            self.result_text.insert(tk.END, f"⏱️  Horas trabajadas: {reporte['horas_trabajadas']:.1f}\n")
            self.result_text.insert(tk.END, f"🔧 Trabajos completados: {reporte['trabajos_completados']}\n")
            
            # Muestro los servicios más populares
            if reporte['servicios_populares']:
                self.result_text.insert(tk.END, f"\n🏆 SERVICIOS MÁS POPULARES:\n")
                for servicio, cantidad, total in reporte['servicios_populares']:
                    self.result_text.insert(tk.END, f"   • {servicio}: {cantidad} trabajos (Q{total:.2f})\n")
            
            # Cierro el diálogo
            dialog.destroy()
            
            # Pregunto si quiere generar gráficas
            respuesta = messagebox.askyesno("Generar Gráficas", 
                f"¿Desea generar gráficas para el reporte {periodo}?")
            
            if respuesta:
                try:
                    # 1. Gráfica de servicios populares
                    fig1 = self.taller.reportes.crear_grafica_servicios_populares(reporte)
                    if fig1:
                        self.mostrar_grafica(fig1, f"Servicios Populares - {periodo.capitalize()}")
                    
                    # 2. Gráfica de ganancias diarias
                    fig2 = self.taller.reportes.crear_grafica_ganancias_diarias(reporte)
                    if fig2:
                        self.mostrar_grafica(fig2, f"Ganancias Diarias - {periodo.capitalize()}")
                    
                    # 3. Gráfica de vehículos frecuentes
                    fig3 = self.taller.reportes.crear_grafica_vehiculos_frecuentes(reporte)
                    if fig3:
                        self.mostrar_grafica(fig3, f"Vehículos Frecuentes - {periodo.capitalize()}")
                    
                    # 4. Gráfica de empleados productivos
                    fig4 = self.taller.reportes.crear_grafica_empleados_productivos(reporte)
                    if fig4:
                        self.mostrar_grafica(fig4, f"Empleados Productivos - {periodo.capitalize()}")
                    
                    # 5. Gráfica de estadísticas generales
                    fig5 = self.taller.reportes.crear_grafica_estadisticas_generales(reporte)
                    if fig5:
                        self.mostrar_grafica(fig5, f"Estadísticas Generales - {periodo.capitalize()}")
                    
                    messagebox.showinfo("Gráficas generadas", 
                                      "Todas las gráficas han sido generadas exitosamente.")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudieron generar todas las gráficas: {e}")
        
        def generar_reporte_clientes():
            """Genera reporte de clientes con gráficas"""
            reporte_clientes = self.taller.reportes.reporte_clientes()
            
            # Muestro el reporte
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*60}\n")
            self.result_text.insert(tk.END, "👥 REPORTE DE CLIENTES\n")
            self.result_text.insert(tk.END, f"{'='*60}\n\n")
            self.result_text.insert(tk.END, f"📊 Total de clientes: {reporte_clientes['total_clientes']}\n\n")
            
            if reporte_clientes['clientes_frecuentes']:
                self.result_text.insert(tk.END, "🏆 CLIENTES MÁS FRECUENTES:\n")
                for cliente, ordenes, gasto_total in reporte_clientes['clientes_frecuentes']:
                    self.result_text.insert(tk.END, f"   • {cliente}: {ordenes} órdenes (Gasto total: Q{gasto_total:.2f})\n")
            
            dialog.destroy()
            
            # Preguntar por gráficas
            respuesta = messagebox.askyesno("Gráficas de Clientes", 
                "¿Desea generar gráficas del reporte de clientes?")
            
            if respuesta:
                try:
                    # 1. Gráfica de clientes frecuentes
                    fig1 = self.taller.reportes.crear_grafica_clientes_frecuentes(reporte_clientes)
                    if fig1:
                        self.mostrar_grafica(fig1, "Clientes Más Frecuentes")
                    
                    # 2. Gráfica de distribución de vehículos
                    fig2 = self.taller.reportes.crear_grafica_distribucion_vehiculos(reporte_clientes)
                    if fig2:
                        self.mostrar_grafica(fig2, "Distribución de Vehículos por Cliente")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudieron generar las gráficas: {e}")
        
        def generar_reporte_empleados():
            """Genera reporte de empleados con gráficas"""
            reporte_empleados = self.taller.reportes.reporte_empleados()
            
            # Muestro el reporte
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*60}\n")
            self.result_text.insert(tk.END, "👷 REPORTE DE EMPLEADOS\n")
            self.result_text.insert(tk.END, f"{'='*60}\n\n")
            self.result_text.insert(tk.END, f"📊 Total de empleados: {reporte_empleados['total_empleados']}\n\n")
            
            if reporte_empleados['empleados']:
                self.result_text.insert(tk.END, "📈 PRODUCTIVIDAD DE EMPLEADOS:\n")
                for empleado in reporte_empleados['empleados']:
                    nombre, ordenes, horas, ingresos, promedio, ultimo = empleado
                    self.result_text.insert(tk.END, f"\n   👤 {nombre}:\n")
                    self.result_text.insert(tk.END, f"      • Órdenes: {ordenes or 0}\n")
                    self.result_text.insert(tk.END, f"      • Horas trabajadas: {horas or 0:.1f}\n")
                    self.result_text.insert(tk.END, f"      • Ingresos generados: Q{ingresos or 0:.2f}\n")
                    if promedio:
                        self.result_text.insert(tk.END, f"      • Promedio por orden: Q{promedio:.2f}\n")
                    if ultimo:
                        self.result_text.insert(tk.END, f"      • Último trabajo: {ultimo}\n")
            
            dialog.destroy()
            
            # Preguntar por gráficas
            respuesta = messagebox.askyesno("Gráficas de Empleados", 
                "¿Desea generar gráficas del reporte de empleados?")
            
            if respuesta:
                try:
                    # Gráfica de productividad de empleados
                    fig = self.taller.reportes.crear_grafica_productividad_empleados(reporte_empleados)
                    if fig:
                        self.mostrar_grafica(fig, "Productividad de Empleados")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo generar la gráfica: {e}")
        
        def mostrar_proyeccion():
            """Muestra proyecciones de crecimiento con gráfica"""
            proyeccion = self.taller.reportes.proyeccion_crecimiento()
            
            if not proyeccion:
                messagebox.showinfo("Información", "No hay suficientes datos históricos (se necesitan al menos 2 meses) para generar proyecciones")
                return
            
            # Muestro las proyecciones
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*60}\n")
            self.result_text.insert(tk.END, "📈 PROYECCIÓN DE CRECIMIENTO\n")
            self.result_text.insert(tk.END, f"{'='*60}\n\n")
            
            # Muestro datos históricos si los hay
            if 'datos_historicos' in proyeccion and proyeccion['datos_historicos']:
                self.result_text.insert(tk.END, "📊 DATOS HISTÓRICOS (últimos 6 meses):\n")
                for mes, total in proyeccion['datos_historicos']:
                    self.result_text.insert(tk.END, f"   {mes}: Q{total:.2f}\n")
                self.result_text.insert(tk.END, "\n")
            
            # Muestro el crecimiento promedio
            self.result_text.insert(tk.END, f"📈 Crecimiento promedio: {proyeccion['crecimiento_promedio']*100:.1f}% mensual\n")
            
            # Muestro las proyecciones futuras
            self.result_text.insert(tk.END, f"\n🔮 PROYECCIONES PRÓXIMOS 6 MESES:\n")
            for mes, ingreso in proyeccion['proyecciones']:
                self.result_text.insert(tk.END, f"   {mes}: Q{ingreso:.2f}\n")
            
            dialog.destroy()
            
            # Preguntar por gráfica
            respuesta = messagebox.askyesno("Gráfica de Proyección", 
                "¿Desea generar una gráfica de la proyección de crecimiento?")
            
            if respuesta:
                try:
                    fig = self.taller.reportes.crear_grafica_proyeccion(proyeccion)
                    if fig:
                        self.mostrar_grafica(fig, "Proyección de Crecimiento")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo generar la gráfica: {e}")
        
        # Creo los elementos del menú de reportes
        ttk.Label(dialog, text="📊 REPORTES AVANZADOS", font=("Arial", 14, "bold")).pack(pady=20)
        
        # Sección de reportes por período
        ttk.Label(dialog, text="📅 Reportes por Período:", font=("Arial", 11, "bold")).pack(pady=10, anchor="w")
        
        frame_periodo = tk.Frame(dialog)
        frame_periodo.pack(pady=10, padx=20, fill=tk.X)
        
        ttk.Button(frame_periodo, text="📅 Reporte Semanal", 
                  command=lambda: generar_reporte_con_graficas('semana')).pack(pady=5, fill=tk.X)
        ttk.Button(frame_periodo, text="📅 Reporte Mensual", 
                  command=lambda: generar_reporte_con_graficas('mes')).pack(pady=5, fill=tk.X)
        ttk.Button(frame_periodo, text="📅 Reporte Anual", 
                  command=lambda: generar_reporte_con_graficas('año')).pack(pady=5, fill=tk.X)
        
        # Línea divisoria
        tk.Frame(dialog, height=2, bg="gray").pack(fill=tk.X, padx=20, pady=10)
        
        # Sección de reportes específicos
        ttk.Label(dialog, text="📈 Reportes Específicos:", font=("Arial", 11, "bold")).pack(pady=10, anchor="w")
        
        frame_especificos = tk.Frame(dialog)
        frame_especificos.pack(pady=10, padx=20, fill=tk.X)
        
        ttk.Button(frame_especificos, text="👥 Reporte de Clientes", 
                  command=generar_reporte_clientes).pack(pady=5, fill=tk.X)
        ttk.Button(frame_especificos, text="👷 Reporte de Empleados", 
                  command=generar_reporte_empleados).pack(pady=5, fill=tk.X)
        
        # Línea divisoria
        tk.Frame(dialog, height=2, bg="gray").pack(fill=tk.X, padx=20, pady=10)
        
        # Sección de proyecciones
        ttk.Label(dialog, text="🔮 Análisis Predictivo:", font=("Arial", 11, "bold")).pack(pady=10, anchor="w")
        
        frame_proyecciones = tk.Frame(dialog)
        frame_proyecciones.pack(pady=10, padx=20, fill=tk.X)
        
        ttk.Button(frame_proyecciones, text="📈 Proyección de Crecimiento", 
                  command=mostrar_proyeccion).pack(pady=5, fill=tk.X)
    
    # ==========================================================================
    # NUEVA FUNCIÓN: RECORDATORIOS INTELIGENTES MEJORADOS
    # ==========================================================================
    def recordatorios_inteligentes_mejorados(self):
        """Muestra recordatorios inteligentes mejorados con predicción multivariable"""
        
        # Obtengo los tipos de servicio disponibles
        tipos_servicio = self.taller.recordatorios.obtener_tipos_servicio_disponibles()
        
        if not tipos_servicio:
            messagebox.showinfo("Información", "No hay tipos de servicio registrados")
            return
        
        # Creo el diálogo principal para recordatorios
        dialog = tk.Toplevel(self.root)
        dialog.title("Recordatorios Inteligentes - Versión Mejorada")
        dialog.geometry("800x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables
        tipo_servicio_seleccionado = tk.StringVar()
        margen_var = tk.StringVar(value="30")
        
        # Título
        ttk.Label(dialog, text="🧠 RECORDATORIOS INTELIGENTES MEJORADOS", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Predicción basada en historial, kilometraje y tipo de vehículo", 
                 font=("Arial", 10)).pack(pady=5)
        
        # Frame para selección de servicio
        frame_servicio = ttk.LabelFrame(dialog, text="1. Seleccione el tipo de servicio")
        frame_servicio.pack(pady=15, padx=20, fill=tk.X)
        
        # Lista de servicios
        listbox_servicios = tk.Listbox(frame_servicio, height=8, font=("Arial", 10))
        scrollbar_servicios = ttk.Scrollbar(frame_servicio)
        listbox_servicios.config(yscrollcommand=scrollbar_servicios.set)
        scrollbar_servicios.config(command=listbox_servicios.yview)
        
        # Agregar servicios a la lista
        for servicio in tipos_servicio:
            listbox_servicios.insert(tk.END, f"🔧 {servicio}")
        
        listbox_servicios.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar_servicios.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Frame para configuración
        frame_config = ttk.LabelFrame(dialog, text="2. Configuración de predicción")
        frame_config.pack(pady=15, padx=20, fill=tk.X)
        
        ttk.Label(frame_config, text="Margen de predicción (días):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ttk.Entry(frame_config, textvariable=margen_var, width=10).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ttk.Label(frame_config, text="Ej: 30 (próximo mes), 90 (próximo trimestre)").grid(row=0, column=2, padx=10, pady=10, sticky="w")
        
        # Botones de acción
        frame_botones = tk.Frame(dialog)
        frame_botones.pack(pady=20)
        
        def analizar_servicio():
            """Analiza qué vehículos necesitan pronto un servicio"""
            seleccion = listbox_servicios.curselection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Seleccione un tipo de servicio")
                return
            
            # Obtengo el tipo de servicio seleccionado
            tipo_servicio = tipos_servicio[seleccion[0]]
            
            # Valido el margen
            try:
                margen_dias = int(margen_var.get())
                if margen_dias <= 0 or margen_dias > 365:
                    messagebox.showerror("Error", "El margen debe estar entre 1 y 365 días")
                    return
            except ValueError:
                messagebox.showerror("Error", "El margen debe ser un número válido")
                return
            
            # Cierro el diálogo de selección
            dialog.destroy()
            
            # Obtengo los recordatorios mejorados
            recordatorios = self.taller.recordatorios.predecir_proximo_servicio_mejorado(tipo_servicio, margen_dias)
            
            # Muestro los resultados en el área principal
            self.mostrar_resultados_recordatorios_mejorados(recordatorios, tipo_servicio, margen_dias)
        
        def mostrar_todos_recordatorios():
            """Muestra todos los recordatorios para todos los servicios"""
            try:
                margen_dias = int(margen_var.get())
                if margen_dias <= 0 or margen_dias > 365:
                    messagebox.showerror("Error", "El margen debe estar entre 1 y 365 días")
                    return
            except ValueError:
                messagebox.showerror("Error", "El margen debe ser un número válido")
                return
            
            # Cierro el diálogo
            dialog.destroy()
            
            # Obtengo TODOS los recordatorios
            todos_recordatorios = self.taller.recordatorios.obtener_todos_recordatorios(margen_dias)
            
            # Muestro resultados generales
            self.mostrar_todos_recordatorios_resultados(todos_recordatorios, margen_dias)
        
        def generar_reporte_analitico():
            """Genera un reporte analítico del servicio seleccionado"""
            seleccion = listbox_servicios.curselection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Seleccione un tipo de servicio")
                return
            
            tipo_servicio = tipos_servicio[seleccion[0]]
            
            # Genero el reporte
            reporte = self.taller.recordatorios.generar_reporte_predicciones(tipo_servicio)
            
            # Muestro el reporte analítico
            self.mostrar_reporte_analitico(reporte, tipo_servicio)
        
        # Creo los botones
        tk.Button(frame_botones, text="🔍 Analizar Servicio", command=analizar_servicio,
                 bg="#3498db", fg="white", padx=15, pady=10, font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10)
        
        tk.Button(frame_botones, text="📊 Todos los Recordatorios", command=mostrar_todos_recordatorios,
                 bg="#9b59b6", fg="white", padx=15, pady=10, font=("Arial", 10, "bold")).grid(row=0, column=1, padx=10)
        
        tk.Button(frame_botones, text="📈 Reporte Analítico", command=generar_reporte_analitico,
                 bg="#2ecc71", fg="white", padx=15, pady=10, font=("Arial", 10, "bold")).grid(row=0, column=2, padx=10)
        
        # Información adicional
        ttk.Label(dialog, 
                 text="💡 La predicción considera: historial del vehículo, kilometraje mensual, marca y tipo de servicio",
                 font=("Arial", 9)).pack(pady=10)
    
    def mostrar_resultados_recordatorios_mejorados(self, recordatorios, tipo_servicio, margen_dias):
        """Muestra los resultados de los recordatorios mejorados"""
        self.clear_results()
        
        self.result_text.insert(tk.END, f"\n{'='*80}\n")
        self.result_text.insert(tk.END, f"🧠 RECORDATORIOS INTELIGENTES - {tipo_servicio.upper()}\n")
        self.result_text.insert(tk.END, f"📅 Margen de predicción: {margen_dias} días\n")
        self.result_text.insert(tk.END, f"📊 Método: Predicción multivariable (historial + kilometraje + marca)\n")
        self.result_text.insert(tk.END, f"{'='*80}\n\n")
        
        if not recordatorios:
            self.result_text.insert(tk.END, f"✅ No hay vehículos que necesiten '{tipo_servicio}' en los próximos {margen_dias} días\n")
            self.result_text.insert(tk.END, f"💡 ¡Excelente! Los mantenimientos están al día.\n")
            return
        
        # Mostrar estadísticas generales
        total_vehiculos = len(recordatorios)
        vencidos = sum(1 for r in recordatorios if r['dias_restantes'] < 0)
        esta_semana = sum(1 for r in recordatorios if 0 <= r['dias_restantes'] <= 7)
        este_mes = sum(1 for r in recordatorios if 8 <= r['dias_restantes'] <= 30)
        
        self.result_text.insert(tk.END, f"📈 ESTADÍSTICAS:\n")
        self.result_text.insert(tk.END, f"   • Total de vehículos: {total_vehiculos}\n")
        self.result_text.insert(tk.END, f"   • Vencidos: {vencidos}\n")
        self.result_text.insert(tk.END, f"   • Esta semana: {esta_semana}\n")
        self.result_text.insert(tk.END, f"   • Este mes: {este_mes}\n")
        self.result_text.insert(tk.END, f"   • Confiabilidad promedio: {np.mean([r['confiabilidad'] for r in recordatorios]):.1f}%\n")
        self.result_text.insert(tk.END, "\n")
        
        # Mostrar cada recordatorio con formato mejorado
        self.result_text.insert(tk.END, f"🚗 VEHÍCULOS PRÓXIMOS A '{tipo_servicio.upper()}':\n\n")
        
        for i, recordatorio in enumerate(recordatorios, 1):
            # Determinar color según confiabilidad
            color_tag = "high_conf" if recordatorio['confiabilidad'] >= 80 else \
                       "medium_conf" if recordatorio['confiabilidad'] >= 60 else \
                       "low_conf"
            
            # Determinar ícono de urgencia
            if recordatorio['dias_restantes'] < 0:
                icono = "🚨"  # Vencido - ALTA URGENCIA
            elif recordatorio['dias_restantes'] <= 7:
                icono = "⚠️"   # Esta semana - Urgencia media
            elif recordatorio['dias_restantes'] <= 14:
                icono = "📅"   # Próximas 2 semanas
            else:
                icono = "📋"   # Este mes
            
            # Configurar etiquetas de color
            self.result_text.tag_configure("high_conf", foreground="#27ae60")  # Verde
            self.result_text.tag_configure("medium_conf", foreground="#f39c12")  # Naranja
            self.result_text.tag_configure("low_conf", foreground="#e74c3c")  # Rojo
            
            # Insertar información del vehículo
            self.result_text.insert(tk.END, f"{icono} {i}. {recordatorio['marca']} {recordatorio['modelo']} - {recordatorio['placa']}\n")
            
            # Información del cliente
            self.result_text.insert(tk.END, f"   👤 Cliente: {recordatorio['cliente']}\n")
            if recordatorio['telefono']:
                self.result_text.insert(tk.END, f"   📞 Teléfono: {recordatorio['telefono']}\n")
            
            # Historial
            self.result_text.insert(tk.END, f"   📅 Último servicio: {recordatorio['ultimo_servicio']}\n")
            self.result_text.insert(tk.END, f"   🛣️  Kilometraje actual: {recordatorio['km_ultimo']:.0f} km\n")
            
            # Predicción
            self.result_text.insert(tk.END, f"   🎯 Próximo estimado: {recordatorio['proximo_estimado']}\n")
            self.result_text.insert(tk.END, f"   📏 Próximo por km: {recordatorio['proximo_km']}\n")
            
            # Estadísticas y métricas
            self.result_text.insert(tk.END, f"   ⏰ Días restantes: {recordatorio['dias_restantes']}\n")
            self.result_text.insert(tk.END, f"   📊 Km/mes promedio: {recordatorio['km_mensual_promedio']:.0f} km\n")
            self.result_text.insert(tk.END, f"   🧮 Método: {recordatorio['metodo_prediccion']}\n")
            
            # Confiabilidad con color
            confiabilidad_text = f"   ✅ Confiabilidad: {recordatorio['confiabilidad']:.1f}%\n"
            start_pos = self.result_text.index(tk.END)
            self.result_text.insert(tk.END, confiabilidad_text)
            end_pos = self.result_text.index(tk.END)
            self.result_text.tag_add(color_tag, f"{start_pos} linestart", f"{end_pos} linestart - 1 line")
            
            # Prioridad
            self.result_text.insert(tk.END, f"   🏆 Prioridad: {recordatorio['prioridad']:.1f}/100\n")
            
            # Recomendación según urgencia
            if recordatorio['dias_restantes'] < 0:
                recomendacion = "🚨 CONTACTO INMEDIATO - Servicio vencido"
            elif recordatorio['dias_restantes'] <= 7:
                recomendacion = "📞 Contactar esta semana"
            elif recordatorio['dias_restantes'] <= 14:
                recomendacion = "📅 Contactar en 2 semanas"
            elif recordatorio['dias_restantes'] <= 30:
                recomendacion = "🗓️  Contactar este mes"
            else:
                recomendacion = "💾 Programar para más adelante"
            
            self.result_text.insert(tk.END, f"   💡 Recomendación: {recomendacion}\n")
            self.result_text.insert(tk.END, "   " + "─" * 60 + "\n\n")
        
        # Recomendaciones generales
        self.result_text.insert(tk.END, f"\n🎯 RECOMENDACIONES GENERALES:\n")
        if vencidos > 0:
            self.result_text.insert(tk.END, f"   • Contactar inmediatamente a los {vencidos} cliente(s) con servicios vencidos\n")
        if esta_semana > 0:
            self.result_text.insert(tk.END, f"   • Programar citas para los {esta_semana} cliente(s) de esta semana\n")
        if este_mes > 0:
            self.result_text.insert(tk.END, f"   • Enviar recordatorios a los {este_mes} cliente(s) de este mes\n")
        
        self.result_text.insert(tk.END, f"\n💡 La confiabilidad indica qué tan precisa es la predicción:\n")
        self.result_text.insert(tk.END, f"   • 🔴 <60%: Basada en pocos datos históricos\n")
        self.result_text.insert(tk.END, f"   • 🟠 60-79%: Basada en datos moderados\n")
        self.result_text.insert(tk.END, f"   • 🟢 80-100%: Basada en historial extenso y consistente\n")
    
    def mostrar_todos_recordatorios_resultados(self, todos_recordatorios, margen_dias):
        """Muestra todos los recordatorios agrupados por tipo de servicio"""
        self.clear_results()
        
        self.result_text.insert(tk.END, f"\n{'='*80}\n")
        self.result_text.insert(tk.END, "📋 TODOS LOS RECORDATORIOS - VISTA GENERAL\n")
        self.result_text.insert(tk.END, f"📅 Margen: {margen_dias} días\n")
        self.result_text.insert(tk.END, f"{'='*80}\n\n")
        
        if not todos_recordatorios:
            self.result_text.insert(tk.END, "✅ No hay recordatorios pendientes en el período seleccionado\n")
            return
        
        # Agrupar por tipo de servicio
        recordatorios_por_servicio = {}
        for recordatorio in todos_recordatorios:
            servicio = recordatorio['tipo_servicio']
            if servicio not in recordatorios_por_servicio:
                recordatorios_por_servicio[servicio] = []
            recordatorios_por_servicio[servicio].append(recordatorio)
        
        # Mostrar resumen por servicio
        self.result_text.insert(tk.END, "📊 RESUMEN POR TIPO DE SERVICIO:\n\n")
        
        for servicio, recordatorios in recordatorios_por_servicio.items():
            total = len(recordatorios)
            vencidos = sum(1 for r in recordatorios if r['dias_restantes'] < 0)
            conf_promedio = np.mean([r['confiabilidad'] for r in recordatorios])
            
            self.result_text.insert(tk.END, f"🔧 {servicio}:\n")
            self.result_text.insert(tk.END, f"   • Total: {total} vehículos\n")
            self.result_text.insert(tk.END, f"   • Vencidos: {vencidos}\n")
            self.result_text.insert(tk.END, f"   • Confiabilidad promedio: {conf_promedio:.1f}%\n")
            
            # Mostrar los 3 más urgentes
            mas_urgentes = sorted(recordatorios, key=lambda x: x['dias_restantes'])[:3]
            if mas_urgentes:
                self.result_text.insert(tk.END, f"   • Más urgentes:\n")
                for urgente in mas_urgentes:
                    self.result_text.insert(tk.END, f"     - {urgente['placa']}: {urgente['dias_restantes']} días restantes\n")
            
            self.result_text.insert(tk.END, "\n")
        
        # Mostrar los 10 más urgentes en general
        self.result_text.insert(tk.END, f"\n🚨 TOP 10 MÁS URGENTES:\n\n")
        
        top_10_urgentes = sorted(todos_recordatorios, key=lambda x: x['dias_restantes'])[:10]
        
        for i, recordatorio in enumerate(top_10_urgentes, 1):
            icono = "🚨" if recordatorio['dias_restantes'] < 0 else "⚠️"
            self.result_text.insert(tk.END, f"{icono} {i}. {recordatorio['placa']} - {recordatorio['marca']} {recordatorio['modelo']}\n")
            self.result_text.insert(tk.END, f"   👤 {recordatorio['cliente']}\n")
            self.result_text.insert(tk.END, f"   🔧 {recordatorio['tipo_servicio']}\n")
            self.result_text.insert(tk.END, f"   📅 {recordatorio['proximo_estimado']} ({recordatorio['dias_restantes']} días)\n")
            self.result_text.insert(tk.END, f"   ✅ Conf: {recordatorio['confiabilidad']:.1f}%\n")
            self.result_text.insert(tk.END, "   " + "─" * 50 + "\n")
        
        # Estadísticas generales
        total_vehiculos = len(todos_recordatorios)
        total_vencidos = sum(1 for r in todos_recordatorios if r['dias_restantes'] < 0)
        conf_general = np.mean([r['confiabilidad'] for r in todos_recordatorios])
        
        self.result_text.insert(tk.END, f"\n📈 ESTADÍSTICAS GLOBALES:\n")
        self.result_text.insert(tk.END, f"   • Total de recordatorios: {total_vehiculos}\n")
        self.result_text.insert(tk.END, f"   • Servicios vencidos: {total_vencidos}\n")
        self.result_text.insert(tk.END, f"   • Confiabilidad general: {conf_general:.1f}%\n")
        self.result_text.insert(tk.END, f"   • Tipos de servicio: {len(recordatorios_por_servicio)}\n")
        
        # Recomendaciones de acción
        self.result_text.insert(tk.END, f"\n🎯 PLAN DE ACCIÓN RECOMENDADO:\n")
        
        if total_vencidos > 0:
            self.result_text.insert(tk.END, f"   1. 📞 Contactar inmediatamente a los {total_vencidos} clientes con servicios vencidos\n")
        
        servicios_con_vencidos = [s for s, r in recordatorios_por_servicio.items() 
                                 if any(rec['dias_restantes'] < 0 for rec in r)]
        
        if servicios_con_vencidos:
            self.result_text.insert(tk.END, f"   2. 🔧 Priorizar servicios: {', '.join(servicios_con_vencidos)}\n")
        
        self.result_text.insert(tk.END, f"   3. 🗓️  Programar citas con al menos 7 días de anticipación\n")
        self.result_text.insert(tk.END, f"   4. 📊 Revisar confiabilidad antes de contactar\n")
    
    def mostrar_reporte_analitico(self, reporte, tipo_servicio):
        """Muestra un reporte analítico detallado"""
        self.clear_results()
        
        self.result_text.insert(tk.END, f"\n{'='*80}\n")
        self.result_text.insert(tk.END, f"📈 REPORTE ANALÍTICO - {tipo_servicio.upper()}\n")
        self.result_text.insert(tk.END, f"{'='*80}\n\n")
        
        if reporte['total_vehiculos'] == 0:
            self.result_text.insert(tk.END, f"📊 No hay vehículos con historial de '{tipo_servicio}'\n")
            self.result_text.insert(tk.END, f"💡 El sistema no puede generar predicciones sin datos históricos\n")
            return
        
        # Información general
        self.result_text.insert(tk.END, "📊 INFORMACIÓN GENERAL:\n")
        self.result_text.insert(tk.END, f"   • Total de vehículos analizados: {reporte['total_vehiculos']}\n")
        self.result_text.insert(tk.END, f"   • Días promedio para próximo servicio: {reporte['promedio_dias_restantes']:.1f}\n")
        self.result_text.insert(tk.END, f"   • Confiabilidad promedio: {reporte['promedio_confiabilidad']:.1f}%\n")
        self.result_text.insert(tk.END, "\n")
        
        # Distribución por urgencia
        self.result_text.insert(tk.END, "🚨 DISTRIBUCIÓN POR URGENCIA:\n")
        categorias = reporte['categorias_urgencia']
        self.result_text.insert(tk.END, f"   • Vencidos: {categorias['vencidos']} vehículos\n")
        self.result_text.insert(tk.END, f"   • Esta semana: {categorias['esta_semana']} vehículos\n")
        self.result_text.insert(tk.END, f"   • Próximas 2 semanas: {categorias['proximas_2_semanas']} vehículos\n")
        self.result_text.insert(tk.END, f"   • Este mes: {categorias['este_mes']} vehículos\n")
        self.result_text.insert(tk.END, f"   • Próximo mes: {categorias['proximo_mes']} vehículos\n")
        self.result_text.insert(tk.END, f"   • Más de 2 meses: {categorias['mas_2_meses']} vehículos\n")
        self.result_text.insert(tk.END, "\n")
        
        # Predicción más confiable
        if reporte['prediccion_mas_confiable']:
            confiable = reporte['prediccion_mas_confiable']
            self.result_text.insert(tk.END, "🏆 PREDICCIÓN MÁS CONFIABLE:\n")
            self.result_text.insert(tk.END, f"   • Vehículo: {confiable['marca']} {confiable['modelo']} - {confiable['placa']}\n")
            self.result_text.insert(tk.END, f"   • Cliente: {confiable['cliente']}\n")
            self.result_text.insert(tk.END, f"   • Confiabilidad: {confiable['confiabilidad']:.1f}%\n")
            self.result_text.insert(tk.END, f"   • Próximo servicio: {confiable['proximo_estimado']}\n")
            self.result_text.insert(tk.END, f"   • Días restantes: {confiable['dias_restantes']}\n")
            self.result_text.insert(tk.END, "\n")
        
        # Predicción más urgente
        if reporte['prediccion_mas_urgente']:
            urgente = reporte['prediccion_mas_urgente']
            self.result_text.insert(tk.END, "⚠️  PREDICCIÓN MÁS URGENTE:\n")
            self.result_text.insert(tk.END, f"   • Vehículo: {urgente['marca']} {urgente['modelo']} - {urgente['placa']}\n")
            self.result_text.insert(tk.END, f"   • Cliente: {urgente['cliente']}\n")
            self.result_text.insert(tk.END, f"   • Días restantes: {urgente['dias_restantes']}\n")
            self.result_text.insert(tk.END, f"   • Confiabilidad: {urgente['confiabilidad']:.1f}%\n")
            self.result_text.insert(tk.END, f"   • Próximo servicio: {urgente['proximo_estimado']}\n")
            self.result_text.insert(tk.END, "\n")
        
        # Análisis de calidad de datos
        self.result_text.insert(tk.END, "🔍 ANÁLISIS DE CALIDAD DE DATOS:\n")
        
        if reporte['promedio_confiabilidad'] >= 80:
            self.result_text.insert(tk.END, "   • 🟢 EXCELENTE - Los datos históricos son extensos y consistentes\n")
            self.result_text.insert(tk.END, "   • Las predicciones son muy confiables\n")
        elif reporte['promedio_confiabilidad'] >= 60:
            self.result_text.insert(tk.END, "   • 🟡 BUENA - Datos suficientes para predicciones aceptables\n")
            self.result_text.insert(tk.END, "   • Se recomienda validar con el cliente\n")
        else:
            self.result_text.insert(tk.END, "   • 🔴 LIMITADA - Pocos datos históricos disponibles\n")
            self.result_text.insert(tk.END, "   • Las predicciones son estimaciones básicas\n")
        
        # Recomendaciones de negocio
        self.result_text.insert(tk.END, "\n💡 RECOMENDACIONES DE NEGOCIO:\n")
        
        if categorias['vencidos'] > 0:
            self.result_text.insert(tk.END, f"   1. 🚨 Contactar URGENTEMENTE a los {categorias['vencidos']} clientes con servicios vencidos\n")
            self.result_text.insert(tk.END, f"      • Ofrecer descuento por retraso\n")
            self.result_text.insert(tk.END, f"      • Programar cita inmediata\n")
        
        if categorias['esta_semana'] > 0:
            self.result_text.insert(tk.END, f"   2. 📞 Llamar a los {categorias['esta_semana']} clientes de esta semana\n")
            self.result_text.insert(tk.END, f"      • Confirmar disponibilidad\n")
            self.result_text.insert(tk.END, f"      • Ofrecer horarios convenientes\n")
        
        if categorias['proximas_2_semanas'] + categorias['este_mes'] > 0:
            total_proximos = categorias['proximas_2_semanas'] + categorias['este_mes']
            self.result_text.insert(tk.END, f"   3. 📧 Enviar recordatorios a los {total_proximos} clientes del mes\n")
            self.result_text.insert(tk.END, f"      • Email o mensaje de texto\n")
            self.result_text.insert(tk.END, f"      • Incluir opción para agendar online\n")
        
        # Sugerencias para mejorar datos
        self.result_text.insert(tk.END, "\n🔧 PARA MEJORAR LAS PREDICCIONES:\n")
        self.result_text.insert(tk.END, f"   • Registrar siempre el kilometraje en cada orden\n")
        self.result_text.insert(tk.END, f"   • Especificar claramente el tipo de servicio\n")
        self.result_text.insert(tk.END, f"   • Actualizar datos de contacto de clientes\n")
    
    def salir(self):
        """Cierra el programa"""
        if messagebox.askyesno("Salir", "¿Está seguro que desea salir del sistema?"):
            self.root.destroy()

# ============================================================================
# INICIO DEL PROGRAMA
# ============================================================================
def main():
    """Función principal que inicia el programa"""
    # Creo la ventana principal
    root = tk.Tk()
    
    # Creo la aplicación
    app = TallerSEYMOGUI(root)
    
    # Ejecuto el programa
    root.mainloop()

# Este if hace que el programa solo se ejecute si lo abro directamente
if __name__ == "__main__":
    main()