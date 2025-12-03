# ============================================================================
# TALLER SEYMO - SISTEMA DE GESTIÓN PARA TALLER MECÁNICO CON TKINTER
# Proyecto personal
# Autor: Miguel Sajquín
# Fecha: 2025
# ============================================================================

# Importación de bibliotecas necesarias
import sqlite3
import os
from datetime import datetime, timedelta
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
from typing import Optional, Dict, List, Tuple
import warnings
import sys

# Importación de Tkinter para la interfaz gráfica
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Evitar advertencias
warnings.filterwarnings('ignore', category=DeprecationWarning)

# ============================================================================
# FUNCIÓN PARA CREAR CARPETAS
# ============================================================================
def crear_estructura_carpetas():
    """Crea todas las carpetas necesarias antes de iniciar el sistema"""
    try:
        carpetas = ['database', 'database/backups', 'reportes']
        for carpeta in carpetas:
            if not os.path.exists(carpeta):
                os.makedirs(carpeta)
        return True
    except Exception as e:
        print(f"❌ Error crítico creando carpetas: {e}")
        return False

# ============================================================================
# INICIALIZACIÓN DEL SISTEMA
# ============================================================================
if not crear_estructura_carpetas():
    print("❌ No se pudo crear la estructura de carpetas. Saliendo...")
    sys.exit(1)

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

print("✅ Estructura de carpetas configurada correctamente")

# ============================================================================
# CLASE DATABASEMANAGER
# ============================================================================
class DatabaseManager:
    """Maneja la conexión y operaciones básicas de la base de datos"""
    
    def __init__(self, db_path: str = 'database/taller.db'):
        self.db_path = db_path
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Inicializa la base de datos con manejo robusto de errores"""
        try:
            self.conn = self._create_connection()
            if self.conn is not None:
                self.create_tables()
                print("✅ Base de datos inicializada correctamente")
            else:
                raise sqlite3.Error("No se pudo crear la conexión")
        except sqlite3.Error as e:
            print(f"❌ Error inicializando base de datos: {e}")
            raise
    
    def _create_connection(self):
        """Crea conexión a la base de datos con manejo de errores"""
        try:
            conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as e:
            print(f"❌ Error creando conexión a la base de datos: {e}")
            return None
    
    def create_tables(self):
        """Crea todas las tablas necesarias"""
        if self.conn is None:
            raise sqlite3.Error("No hay conexión a la base de datos")
        
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    telefono TEXT UNIQUE,
                    nit TEXT UNIQUE
                )
            ''')
            
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
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS empleados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    telefono TEXT UNIQUE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ordenes_trabajo (
                    id INTEGER PRIMARY KEY,
                    vehiculo_id INTEGER,
                    empleado_id INTEGER,
                    fecha_inicio DATE DEFAULT CURRENT_DATE,
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
            
            self._verificar_y_actualizar_tablas()
            self.conn.commit()
            print("✅ Tablas creadas/verificadas correctamente")
            
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"❌ Error creando tablas: {e}")
            raise
    
    def _verificar_y_actualizar_tablas(self):
        """Verifica y actualiza la estructura de las tablas si es necesario"""
        cursor = self.conn.cursor()
        
        try:
            print("🔄 Verificando estructura de tablas...")
            
            cursor.execute("PRAGMA table_info(clientes)")
            columnas_clientes = [col[1] for col in cursor.fetchall()]
            
            if 'nit' not in columnas_clientes:
                print("🔄 Agregando columna 'nit' a tabla clientes...")
                cursor.execute('ALTER TABLE clientes ADD COLUMN nit TEXT UNIQUE')
                print("✅ Columna 'nit' agregada a clientes")
            
            cursor.execute("PRAGMA table_info(vehiculos)")
            columnas_vehiculos = [col[1] for col in cursor.fetchall()]
            
            if 'proximo_mantenimiento' not in columnas_vehiculos:
                print("🔄 Agregando columna 'proximo_mantenimiento' a vehiculos...")
                cursor.execute('ALTER TABLE vehiculos ADD COLUMN proximo_mantenimiento DATE')
            
            if 'kilometraje_ultimo_mantenimiento' not in columnas_vehiculos:
                print("🔄 Agregando columna 'kilometraje_ultimo_mantenimiento' a vehiculos...")
                cursor.execute('ALTER TABLE vehiculos ADD COLUMN kilometraje_ultimo_mantenimiento REAL')
            
            self.conn.commit()
            print("✅ Estructura de tablas actualizada correctamente")
            
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"❌ Error al actualizar tablas: {e}")
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Ejecuta una consulta y retorna el cursor"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor
    
    def commit(self):
        """Realiza commit"""
        self.conn.commit()

    def diagnosticar_estructura_bd(self):
        """Diagnostica la estructura actual de la base de datos"""
        cursor = self.conn.cursor()
        
        try:
            print("\n🔍 DIAGNÓSTICO DE ESTRUCTURA DE BD")
            
            cursor.execute("PRAGMA table_info(clientes)")
            columnas = cursor.fetchall()
            print("\n📋 TABLA CLIENTES:")
            for col in columnas:
                print(f"   - {col[1]} ({col[2]})")
            
            cursor.execute("SELECT COUNT(*) FROM clientes")
            total_clientes = cursor.fetchone()[0]
            print(f"   Total de clientes: {total_clientes}")
            
            cursor.execute("PRAGMA table_info(vehiculos)")
            columnas_vehiculos = cursor.fetchall()
            print("\n📋 TABLA VEHICULOS:")
            for col in columnas_vehiculos:
                print(f"   - {col[1]} ({col[2]})")
            
        except sqlite3.Error as e:
            print(f"❌ Error en diagnóstico: {e}")

# ============================================================================
# CLASE VALIDATOR
# ============================================================================
class Validator:
    """Maneja todas las validaciones de datos"""
    
    @staticmethod
    def validar_numero(valor: str, tipo: str = "entero") -> Optional[float]:
        """Valida que el valor sea un número válido"""
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
        """Valida que el teléfono contenga solo números y tenga longitud razonable"""
        if telefono is None or telefono.strip() == "":
            return None
        
        telefono_limpio = ''.join(filter(str.isdigit, telefono))
        
        if len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
            return None
        
        return telefono_limpio
    
    @staticmethod
    def validar_nit(nit: str) -> Optional[str]:
        """Valida que el NIT contenga solo números, letras y guiones, y tenga longitud razonable"""
        if nit is None or nit.strip() == "":
            return None
        
        nit_limpio = ''.join(filter(lambda c: c.isalnum() or c in '- ', nit))
        
        if len(nit_limpio) < 3 or len(nit_limpio) > 20:
            return None
        
        return nit_limpio
    
    @staticmethod
    def validar_fecha(fecha_str: str, permitir_futuro: bool = True, permitir_pasado: bool = True) -> Optional[datetime.date]:
        """Valida y convierte una fecha en formato string a date"""
        try:
            if not fecha_str.strip():
                return None
                
            if fecha_str.isdigit():
                dias = int(fecha_str)
                fecha = datetime.now() + timedelta(days=dias)
            else:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            
            hoy = datetime.now().date()
            fecha_date = fecha.date()
            
            if fecha_date < datetime(2000, 1, 1).date():
                return None
            
            if fecha_date > hoy + timedelta(days=365):
                return None
                
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
        return 1900 <= año <= año_actual + 2

# ============================================================================
# CLASE CLIENTEMANAGER
# ============================================================================
class ClienteManager:
    """Gestiona todas las operaciones relacionadas con clientes"""
    
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
            if "telefono" in str(e):
                raise Exception("Ya existe un cliente con ese teléfono")
            elif "nit" in str(e):
                raise Exception("Ya existe un cliente con ese NIT")
            else:
                raise Exception("Error de integridad en la base de datos")
    
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
                return "❌ Error de integridad en la base de datos"
    
    def detalles_cliente(self, cliente_id: int) -> Optional[Dict]:
        """Obtiene detalles completos de un cliente"""
        if not self.cliente_existe(cliente_id):
            return None
        
        cursor = self.db.execute_query(
            'SELECT nombre, telefono, nit FROM clientes WHERE id = ?', 
            (cliente_id,)
        )
        cliente_info = cursor.fetchone()
        
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
# CLASE VEHICULOMANAGER
# ============================================================================
class VehiculoManager:
    """Gestiona todas las operaciones relacionadas con vehículos"""
    
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
        """Obtiene detalles completos de un vehículo"""
        if not self.vehiculo_existe(vehiculo_id):
            return None
        
        cursor = self.db.execute_query('''
            SELECT v.marca, v.modelo, v.año, v.placa, v.color, c.nombre, c.telefono, c.nit
            FROM vehiculos v
            JOIN clientes c ON v.cliente_id = c.id
            WHERE v.id = ?
        ''', (vehiculo_id,))
        vehiculo_info = cursor.fetchone()
        
        cursor = self.db.execute_query('''
            SELECT o.id, o.fecha_inicio, o.fecha_fin, o.descripcion_trabajo, 
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
# CLASE EMPLEADOMANAGER
# ============================================================================
class EmpleadoManager:
    """Gestiona todas las operaciones relacionadas con empleados"""
    
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
# CLASE ORDENMANAGER
# ============================================================================
class OrdenManager:
    """Gestiona todas las operaciones relacionadas con órdenes de trabajo"""
    
    def __init__(self, db_manager: DatabaseManager, validator: Validator):
        self.db = db_manager
        self.validator = validator
    
    def orden_existe(self, orden_id: int) -> bool:
        """Verifica si una orden existe"""
        cursor = self.db.execute_query('SELECT id FROM ordenes_trabajo WHERE id = ?', (orden_id,))
        return cursor.fetchone() is not None
    
    def obtener_detalles_orden(self, orden_id: int) -> Optional[Dict]:
        """Obtiene detalles completos de una orden"""
        if not self.orden_existe(orden_id):
            return None
        
        cursor = self.db.execute_query('''
            SELECT 
                o.id, o.fecha_inicio, o.fecha_fin, o.descripcion_trabajo, 
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
        
        return {
            'id': orden_info[0],
            'fecha_inicio': orden_info[1],
            'fecha_fin': orden_info[2],
            'descripcion_trabajo': orden_info[3],
            'tipo_servicio': orden_info[4],
            'horas_trabajadas': orden_info[5],
            'costo_repuestos': orden_info[6],
            'costo_mano_obra': orden_info[7],
            'precio_final': orden_info[8],
            'kilometraje': orden_info[9],
            'unidad_kilometraje': orden_info[10],
            'vehiculo_marca': orden_info[11],
            'vehiculo_modelo': orden_info[12],
            'vehiculo_placa': orden_info[13],
            'vehiculo_año': orden_info[14],
            'cliente_nombre': orden_info[15],
            'cliente_telefono': orden_info[16],
            'cliente_nit': orden_info[17],
            'empleado_nombre': orden_info[18]
        }
    
    def agregar_orden(self, numero_orden: int, vehiculo_id: int, empleado_id: int, 
                     descripcion_trabajo: str, tipo_servicio: str, horas_trabajadas: float,
                     costo_repuestos: float, costo_mano_obra: float, kilometraje: float,
                     unidad_kilometraje: str = 'km', fecha_fin: Optional[str] = None) -> str:
        """Agrega una nueva orden de trabajo"""
        
        fecha_fin_validada = None
        if fecha_fin:
            fecha_fin_validada = self.validator.validar_fecha(fecha_fin, permitir_futuro=True, permitir_pasado=True)
            if fecha_fin_validada is None:
                return "❌ Error: Fecha de finalización inválida."
        else:
            fecha_fin_validada = datetime.now().date()
        
        precio_final = costo_repuestos + costo_mano_obra
        
        try:
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
            return f"✅ Orden #{numero_orden} agregada - Total: Q{precio_final:.2f}"
        except sqlite3.IntegrityError as e:
            return f"❌ Error al agregar orden: {e}"
    
    def editar_orden(self, orden_id: int, nueva_descripcion: str, nuevo_precio: float,
                    nuevo_tipo: str, nuevo_km: float) -> str:
        """Edita una orden de trabajo existente"""
        try:
            self.db.execute_query('''
                UPDATE ordenes_trabajo 
                SET descripcion_trabajo = ?, precio_final = ?, tipo_servicio = ?, kilometraje = ?
                WHERE id = ?
            ''', (nueva_descripcion, nuevo_precio, nuevo_tipo, nuevo_km, orden_id))
            
            self.db.commit()
            return f"✅ Orden #{orden_id} actualizada"
        except Exception as e:
            return f"❌ Error al editar orden: {e}"

# ============================================================================
# CLASE REPORTMANAGER
# ============================================================================
class ReportManager:
    """Gestiona la generación de reportes y gráficas"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def reporte_periodo(self, periodo: str = 'semana') -> Dict:
        """Genera reportes del período especificado"""
        if periodo == 'semana':
            fecha_inicio = datetime.now() - timedelta(days=datetime.now().weekday())
        elif periodo == 'mes':
            fecha_inicio = datetime.now().replace(day=1)
        else:
            fecha_inicio = datetime.now().replace(month=1, day=1)
        
        cursor = self.db.execute_query('''
            SELECT SUM(precio_final), SUM(horas_trabajadas), COUNT(*)
            FROM ordenes_trabajo 
            WHERE fecha_fin >= ?
        ''', (fecha_inicio.date(),))
        
        ganancias, horas, trabajos = cursor.fetchone()
        
        cursor = self.db.execute_query('''
            SELECT tipo_servicio, COUNT(*), SUM(precio_final)
            FROM ordenes_trabajo 
            WHERE fecha_fin >= ?
            GROUP BY tipo_servicio
            ORDER BY COUNT(*) DESC
            LIMIT 5
        ''', (fecha_inicio.date(),))
        
        servicios_populares = cursor.fetchall()
        
        return {
            'ganancias': ganancias or 0,
            'horas_trabajadas': horas or 0,
            'trabajos_completados': trabajos or 0,
            'periodo': periodo,
            'fecha_inicio': fecha_inicio.date(),
            'servicios_populares': servicios_populares
        }
    
    def crear_grafica_servicios_populares(self, reporte: Dict, nombre_archivo: str):
        """Crea gráfica de servicios más populares"""
        if not reporte['servicios_populares']:
            print("❌ No hay datos para generar la gráfica")
            return
        
        servicios = [s[0] for s in reporte['servicios_populares']]
        cantidades = [s[1] for s in reporte['servicios_populares']]
        
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        if SEABORN_AVAILABLE:
            import seaborn as sns
            sns.barplot(x=cantidades, y=servicios, palette='viridis', ax=ax)
        else:
            ax.barh(servicios, cantidades, color='skyblue', alpha=0.7)
        
        ax.set_title('Servicios Más Solicitados', fontsize=14, fontweight='bold')
        ax.set_xlabel('Cantidad de Trabajos')
        
        fig.tight_layout()
        
        archivo_path = f'reportes/{nombre_archivo}.png'
        fig.savefig(archivo_path, dpi=300, bbox_inches='tight')
        
        print(f"✅ Gráfica guardada: {archivo_path}")
        return fig
    
    def proyeccion_crecimiento(self) -> Dict:
        """Genera proyecciones de crecimiento basadas en datos históricos"""
        try:
            # Obtener datos históricos de los últimos 6 meses
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
            
            if len(datos) < 2:
                return None
            
            # Calcular crecimiento promedio
            totales = [d[1] for d in datos]
            crecimientos = []
            
            for i in range(1, len(totales)):
                if totales[i-1] > 0:
                    crecimiento = (totales[i] - totales[i-1]) / totales[i-1]
                    crecimientos.append(crecimiento)
            
            if not crecimientos:
                return None
            
            crecimiento_promedio = sum(crecimientos) / len(crecimientos)
            
            # Generar proyecciones para los próximos 6 meses
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

# ============================================================================
# CLASE RECORDATORIOSINTELIGENTES
# ============================================================================
class RecordatoriosInteligentes:
    """Sistema inteligente que predice mantenimiento basado en historial de servicios"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def obtener_tipos_servicio_disponibles(self) -> List[str]:
        """Obtiene todos los tipos de servicio únicos de la base de datos"""
        cursor = self.db.execute_query('''
            SELECT DISTINCT tipo_servicio FROM ordenes_trabajo 
            WHERE tipo_servicio IS NOT NULL AND tipo_servicio != ''
            ORDER BY tipo_servicio
        ''')
        return [servicio[0] for servicio in cursor.fetchall()]
    
    def predecir_proximo_servicio(self, tipo_servicio: str, margen_dias: int = 30) -> List[Dict]:
        """Predice qué vehículos necesitarán pronto un servicio específico"""
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
            
            if ultima_fecha:
                if isinstance(ultima_fecha, str):
                    fecha_ultimo_dt = datetime.strptime(ultima_fecha, '%Y-%m-%d')
                else:
                    fecha_ultimo_dt = datetime.combine(ultima_fecha, datetime.min.time())
                
                # Estimación simple: 6 meses después del último servicio
                fecha_estimada = fecha_ultimo_dt + timedelta(days=180)
                dias_restantes = (fecha_estimada - datetime.now()).days
                
                if dias_restantes <= margen_dias and dias_restantes >= 0:
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
                        'dias_restantes': dias_restantes
                    })
        
        resultados.sort(key=lambda x: x['dias_restantes'])
        return resultados

# ============================================================================
# CLASE TALLERSEYMO
# ============================================================================
class TallerSEYMO:
    """Clase principal que coordina todas las funcionalidades del taller"""
    
    def __init__(self):
        try:
            self.db = DatabaseManager()
            self.validator = Validator()
            self.clientes = ClienteManager(self.db, self.validator)
            self.vehiculos = VehiculoManager(self.db, self.validator)
            self.empleados = EmpleadoManager(self.db, self.validator)
            self.ordenes = OrdenManager(self.db, self.validator)
            self.reportes = ReportManager(self.db)
            self.recordatorios = RecordatoriosInteligentes(self.db)
            
            print("✅ Sistema Taller SEYMO inicializado correctamente")
            
        except Exception as e:
            print(f"❌ Error crítico iniciando el sistema: {e}")
            raise

# ============================================================================
# INTERFAZ GRÁFICA CON TKINTER
# ============================================================================
class TallerSEYMOGUI:
    """Interfaz gráfica para el sistema del taller"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Taller SEYMO - Sistema de Gestión")
        self.root.geometry("1200x800")
        
        # Inicializar sistema
        try:
            self.taller = TallerSEYMO()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo inicializar el sistema: {e}")
            self.root.destroy()
            return
        
        # Variables para seguimiento
        self.cliente_seleccionado = None
        self.vehiculo_seleccionado = None
        self.empleado_seleccionado = None
        
        # Configurar estilo
        self.setup_styles()
        
        # Crear interfaz
        self.create_widgets()
        
    def setup_styles(self):
        """Configura los estilos de la interfaz"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colores
        self.primary_color = "#2c3e50"
        self.secondary_color = "#3498db"
        self.success_color = "#27ae60"
        self.warning_color = "#e67e22"
        self.danger_color = "#e74c3c"
        
        # Configurar estilos
        self.root.configure(bg=self.primary_color)
        
    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg=self.primary_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
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
        
        # Frame para botones (2 filas de botones)
        buttons_frame = tk.Frame(main_frame, bg=self.primary_color)
        buttons_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Crear botones principales
        self.create_main_buttons(buttons_frame)
        
        # Frame para área de resultados
        self.result_frame = tk.Frame(main_frame, bg="white", relief=tk.SUNKEN, borderwidth=2)
        self.result_frame.pack(fill=tk.BOTH, expand=True)
        
        # Área de texto para resultados
        self.result_text = scrolledtext.ScrolledText(
            self.result_frame,
            font=("Consolas", 10),
            wrap=tk.WORD,
            bg="#f8f9fa",
            relief=tk.FLAT
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Barra de estado
        self.status_bar = tk.Label(
            self.root,
            text="✅ Sistema listo | © 2025 Taller SEYMO",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#2c3e50",
            fg="white"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_main_buttons(self, parent):
        """Crea los botones principales del menú"""
        # Primera fila de botones
        row1_frame = tk.Frame(parent, bg=self.primary_color)
        row1_frame.pack(fill=tk.X, pady=5)
        
        buttons_row1 = [
            ("📝 Nuevo Cliente", self.registrar_cliente),
            ("🚗 Nuevo Vehículo", self.registrar_vehiculo),
            ("👷 Nuevo Empleado", self.registrar_empleado),
            ("📋 Nueva Orden", self.nueva_orden),
            ("🔍 Buscar Cliente", self.buscar_cliente)
        ]
        
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
        
        buttons_row2 = [
            ("🔧 Historial Vehículo", self.historial_vehiculo),
            ("✏️ Editar Cliente", self.editar_cliente),
            ("✏️ Editar Empleado", self.editar_empleado),
            ("📊 Reportes", self.menu_reportes),
            ("🧠 Recordatorios", self.recordatorios_inteligentes),
            ("❌ Salir", self.salir)
        ]
        
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
        """Limpia el área de resultados"""
        self.result_text.delete(1.0, tk.END)
        
    def show_message(self, message, success=True):
        """Muestra un mensaje en el área de resultados"""
        self.clear_results()
        color = self.success_color if success else self.danger_color
        self.result_text.insert(tk.END, message)
        self.result_text.tag_configure("center", justify='center', foreground=color)
        self.result_text.tag_add("center", "1.0", "end")
        
    # ==========================================================================
    # FUNCIONALIDADES PRINCIPALES - CORREGIDAS
    # ==========================================================================
    
    def registrar_cliente(self):
        """Registra un nuevo cliente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar Nuevo Cliente")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables
        nombre_var = tk.StringVar()
        telefono_var = tk.StringVar()
        nit_var = tk.StringVar()
        
        def guardar():
            try:
                # Validar datos del cliente
                if not nombre_var.get().strip():
                    messagebox.showerror("Error", "El nombre del cliente es obligatorio")
                    return
                
                telefono = None
                if telefono_var.get().strip():
                    telefono = self.taller.validator.validar_telefono(telefono_var.get())
                    if not telefono:
                        messagebox.showerror("Error", "Teléfono inválido")
                        return
                
                nit = None
                if nit_var.get().strip():
                    nit = self.taller.validator.validar_nit(nit_var.get())
                    if not nit:
                        messagebox.showerror("Error", "NIT inválido")
                        return
                
                # Agregar cliente
                cliente_id = self.taller.clientes.agregar_cliente(
                    nombre_var.get().strip(),
                    telefono,
                    nit
                )
                
                self.show_message(f"✅ Cliente registrado exitosamente\nID: {cliente_id}")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Formulario
        ttk.Label(dialog, text="👤 REGISTRAR NUEVO CLIENTE", font=("Arial", 12, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Nombre completo:").pack(pady=5)
        ttk.Entry(dialog, textvariable=nombre_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="Teléfono (opcional):").pack(pady=5)
        ttk.Entry(dialog, textvariable=telefono_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="NIT (opcional):").pack(pady=5)
        ttk.Entry(dialog, textvariable=nit_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Guardar", command=guardar).pack(pady=20)
    
    def registrar_vehiculo(self):
        """Registra un nuevo vehículo para un cliente existente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar Nuevo Vehículo")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables
        cliente_id_var = tk.StringVar()
        marca_var = tk.StringVar()
        modelo_var = tk.StringVar()
        año_var = tk.StringVar()
        placa_var = tk.StringVar()
        color_var = tk.StringVar()
        
        def buscar_cliente():
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
                listbox.delete(0, tk.END)
                clientes = self.taller.clientes.buscar_cliente_por_nombre(search_var.get())
                for cliente in clientes:
                    listbox.insert(tk.END, f"ID: {cliente[0]} | Nombre: {cliente[1]} | Tel: {cliente[2] or 'N/A'} | NIT: {cliente[3] or 'N/A'}")
            
            def seleccionar():
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
            try:
                # Validar datos
                if not cliente_id_var.get().strip():
                    messagebox.showerror("Error", "Debe seleccionar un cliente")
                    return
                
                if not marca_var.get().strip():
                    messagebox.showerror("Error", "La marca es obligatoria")
                    return
                
                if not modelo_var.get().strip():
                    messagebox.showerror("Error", "El modelo es obligatorio")
                    return
                
                if not año_var.get().strip():
                    messagebox.showerror("Error", "El año es obligatorio")
                    return
                
                año = int(año_var.get())
                if not self.taller.validator.validar_año_vehiculo(año):
                    messagebox.showerror("Error", "Año del vehículo inválido")
                    return
                
                if not placa_var.get().strip():
                    messagebox.showerror("Error", "La placa es obligatoria")
                    return
                
                placa = placa_var.get().strip().upper()
                if self.taller.vehiculos.placa_existe(placa):
                    messagebox.showerror("Error", "Ya existe un vehículo con esa placa")
                    return
                
                # Agregar vehículo
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
        
        # Formulario
        ttk.Label(dialog, text="🚗 REGISTRAR NUEVO VEHÍCULO", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Cliente
        frame_cliente = ttk.LabelFrame(dialog, text="Cliente")
        frame_cliente.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(frame_cliente, text="ID Cliente:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(frame_cliente, textvariable=cliente_id_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_cliente, text="Buscar Cliente", command=buscar_cliente).pack(side=tk.LEFT, padx=5)
        
        # Datos del vehículo
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
        """Registra un nuevo empleado"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar Nuevo Empleado")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables
        nombre_var = tk.StringVar()
        telefono_var = tk.StringVar()
        
        def guardar():
            try:
                if not nombre_var.get().strip():
                    messagebox.showerror("Error", "El nombre del empleado es obligatorio")
                    return
                
                telefono = self.taller.validator.validar_telefono(telefono_var.get())
                if not telefono:
                    messagebox.showerror("Error", "Teléfono inválido (7-15 dígitos)")
                    return
                
                resultado = self.taller.empleados.agregar_empleado(
                    nombre_var.get().strip(),
                    telefono
                )
                
                self.show_message(resultado)
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Formulario
        ttk.Label(dialog, text="👷 REGISTRAR NUEVO EMPLEADO", font=("Arial", 12, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Nombre completo:").pack(pady=5)
        ttk.Entry(dialog, textvariable=nombre_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="Teléfono:").pack(pady=5)
        ttk.Entry(dialog, textvariable=telefono_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Guardar", command=guardar).pack(pady=20)
    
    def nueva_orden(self):
        """Crea una nueva orden de trabajo - VERSIÓN CORREGIDA"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Nueva Orden de Trabajo")
        dialog.geometry("650x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables
        orden_var = tk.StringVar()
        descripcion_var = tk.StringVar()
        tipo_servicio_var = tk.StringVar()
        horas_var = tk.StringVar()
        repuestos_var = tk.StringVar()
        mano_obra_var = tk.StringVar()
        kilometraje_var = tk.StringVar()
        unidad_km_var = tk.StringVar(value="km")
        
        # Variables para seguimiento
        cliente_id = None
        vehiculo_id = None
        empleado_id = None
        
        # Frame principal usando pack
        main_content = tk.Frame(dialog)
        main_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Título
        tk.Label(main_content, text="📋 NUEVA ORDEN DE TRABAJO", 
                font=("Arial", 12, "bold")).pack(pady=10)
        
        # Frame para selecciones usando grid internamente
        frame_selecciones = tk.LabelFrame(main_content, text="Selecciones")
        frame_selecciones.pack(fill=tk.X, pady=10, padx=5)
        
        # Variables para labels de estado
        cliente_label = tk.Label(frame_selecciones, text="Cliente: No seleccionado", anchor="w")
        vehiculo_label = tk.Label(frame_selecciones, text="Vehículo: No seleccionado", anchor="w")
        empleado_label = tk.Label(frame_selecciones, text="Empleado: No seleccionado", anchor="w")
        
        def buscar_cliente():
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
                listbox.delete(0, tk.END)
                clientes = self.taller.clientes.buscar_cliente_por_nombre(search_var.get())
                for cliente in clientes:
                    listbox.insert(tk.END, f"ID: {cliente[0]} | Nombre: {cliente[1]} | Tel: {cliente[2] or 'N/A'}")
            
            def seleccionar():
                nonlocal cliente_id, vehiculo_id
                seleccion = listbox.curselection()
                if seleccion:
                    texto = listbox.get(seleccion[0])
                    cliente_id = int(texto.split("ID: ")[1].split(" |")[0])
                    cliente_label.config(text=f"Cliente: ID {cliente_id} seleccionado")
                    # Resetear vehículo cuando se cambia de cliente
                    vehiculo_id = None
                    vehiculo_label.config(text="Vehículo: No seleccionado")
                    search_dialog.destroy()
            
            ttk.Button(search_dialog, text="Buscar", command=perform_search).pack(pady=5)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            ttk.Button(search_dialog, text="Seleccionar", command=seleccionar).pack(pady=10)
        
        def seleccionar_vehiculo():
            nonlocal vehiculo_id
            if not cliente_id:
                messagebox.showwarning("Advertencia", "Primero seleccione un cliente")
                return
            
            vehiculos = self.taller.vehiculos.obtener_vehiculos_cliente(cliente_id)
            
            if not vehiculos:
                messagebox.showinfo("Información", "Este cliente no tiene vehículos registrados")
                return
            
            search_dialog = tk.Toplevel(dialog)
            search_dialog.title("Seleccionar Vehículo")
            search_dialog.geometry("500x400")
            
            listbox = tk.Listbox(search_dialog, width=60, height=15)
            scrollbar = ttk.Scrollbar(search_dialog)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            
            for vehiculo in vehiculos:
                listbox.insert(tk.END, f"ID: {vehiculo[0]} | {vehiculo[1]} {vehiculo[2]} {vehiculo[3]} | Placa: {vehiculo[4]}")
            
            def seleccionar():
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
            nonlocal empleado_id
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
            
            for empleado in empleados:
                listbox.insert(tk.END, f"ID: {empleado[0]} | {empleado[1]} | Tel: {empleado[2]}")
            
            def seleccionar():
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
            try:
                # Validaciones
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
                
                try:
                    numero_orden = int(orden_var.get())
                except ValueError:
                    messagebox.showerror("Error", "El número de orden debe ser un número")
                    return
                
                # Validar que el número de orden no exista ya
                if self.taller.ordenes.orden_existe(numero_orden):
                    respuesta = messagebox.askyesno(
                        "Orden existente", 
                        f"La orden #{numero_orden} ya existe. ¿Desea usar un número diferente?"
                    )
                    if not respuesta:
                        return
                    messagebox.showinfo("Información", "Por favor use un número de orden diferente")
                    return
                
                descripcion = descripcion_var.get().strip()
                if not descripcion:
                    messagebox.showerror("Error", "La descripción es obligatoria")
                    return
                
                tipo_servicio = tipo_servicio_var.get().strip()
                if not tipo_servicio:
                    messagebox.showerror("Error", "El tipo de servicio es obligatorio")
                    return
                
                try:
                    horas = float(horas_var.get() or 0)
                    repuestos = float(repuestos_var.get() or 0)
                    mano_obra = float(mano_obra_var.get() or 0)
                    kilometraje = float(kilometraje_var.get() or 0)
                except ValueError:
                    messagebox.showerror("Error", "Los valores numéricos deben ser válidos")
                    return
                
                unidad_km = unidad_km_var.get().strip() or "km"
                
                # Agregar orden
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
                    unidad_km
                )
                
                self.show_message(resultado)
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Usar grid dentro del LabelFrame (esto está permitido)
        tk.Button(frame_selecciones, text="1. Seleccionar Cliente", 
                  command=buscar_cliente).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        cliente_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        tk.Button(frame_selecciones, text="2. Seleccionar Vehículo", 
                  command=seleccionar_vehiculo).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        vehiculo_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        tk.Button(frame_selecciones, text="3. Seleccionar Empleado", 
                  command=seleccionar_empleado).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        empleado_label.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Campos de la orden usando pack
        fields_frame = tk.Frame(main_content)
        fields_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Crear todos los campos usando pack
        fields = [
            ("Número de orden:", orden_var),
            ("Descripción del trabajo:", descripcion_var),
            ("Tipo de servicio:", tipo_servicio_var),
            ("Horas trabajadas:", horas_var),
            ("Costo repuestos (Q):", repuestos_var),
            ("Costo mano de obra (Q):", mano_obra_var),
            ("Kilometraje:", kilometraje_var),
            ("Unidad kilometraje:", unidad_km_var)
        ]
        
        for label_text, var in fields:
            frame = tk.Frame(fields_frame)
            frame.pack(fill=tk.X, pady=5)
            tk.Label(frame, text=label_text, width=25, anchor="w").pack(side=tk.LEFT, padx=5)
            tk.Entry(frame, textvariable=var, width=30).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Botón de guardar
        tk.Button(main_content, text="Guardar Orden", command=guardar, 
                  bg="#4CAF50", fg="white", padx=20, pady=10, font=("Arial", 10, "bold")).pack(pady=20)
    
    def buscar_cliente(self):
        """Busca y muestra información de un cliente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Buscar Cliente")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        search_var = tk.StringVar()
        resultados_text = scrolledtext.ScrolledText(dialog, height=25, width=70)
        
        def buscar():
            resultados_text.delete(1.0, tk.END)
            clientes = self.taller.clientes.buscar_cliente_por_nombre(search_var.get())
            
            if not clientes:
                resultados_text.insert(tk.END, "❌ No se encontraron clientes")
                return
            
            for cliente in clientes:
                resultados_text.insert(tk.END, f"\n{'═'*60}\n")
                resultados_text.insert(tk.END, f"📋 ID: {cliente[0]}\n")
                resultados_text.insert(tk.END, f"👤 Nombre: {cliente[1]}\n")
                resultados_text.insert(tk.END, f"📞 Teléfono: {cliente[2] or 'No tiene'}\n")
                resultados_text.insert(tk.END, f"🏢 NIT: {cliente[3] or 'No tiene'}\n")
                
                # Mostrar vehículos del cliente
                vehiculos = self.taller.vehiculos.obtener_vehiculos_cliente(cliente[0])
                if vehiculos:
                    resultados_text.insert(tk.END, f"\n🚗 VEHÍCULOS ({len(vehiculos)}):\n")
                    for vehiculo in vehiculos:
                        resultados_text.insert(tk.END, f"   • {vehiculo[1]} {vehiculo[2]} {vehiculo[3]} - Placa: {vehiculo[4]}\n")
                else:
                    resultados_text.insert(tk.END, "\n❌ Este cliente no tiene vehículos registrados.\n")
            
            resultados_text.insert(tk.END, f"\n{'═'*60}\n")
        
        ttk.Label(dialog, text="🔍 BUSCAR CLIENTE", font=("Arial", 12, "bold")).pack(pady=10)
        
        ttk.Label(dialog, text="Nombre del cliente:").pack(pady=5)
        ttk.Entry(dialog, textvariable=search_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Buscar", command=buscar).pack(pady=10)
        
        resultados_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
    
    def historial_vehiculo(self):
        """Muestra el historial de un vehículo - VERSIÓN CORREGIDA"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Historial de Vehículo")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables
        placa_var = tk.StringVar()
        resultados_text = scrolledtext.ScrolledText(dialog, height=30, width=80)
        
        def buscar_por_placa():
            resultados_text.delete(1.0, tk.END)
            placa = placa_var.get().strip().upper()
            
            if not placa:
                resultados_text.insert(tk.END, "❌ Ingrese una placa para buscar")
                return
            
            # Buscar vehículo por placa
            cursor = self.taller.db.execute_query(
                'SELECT id FROM vehiculos WHERE placa = ?', 
                (placa,)
            )
            resultado = cursor.fetchone()
            
            if not resultado:
                resultados_text.insert(tk.END, f"❌ No se encontró vehículo con placa: {placa}")
                return
            
            vehiculo_id = resultado[0]
            
            # Obtener detalles del vehículo
            detalles = self.taller.vehiculos.detalles_vehiculo(vehiculo_id)
            
            if not detalles:
                resultados_text.insert(tk.END, f"❌ Error al obtener detalles del vehículo")
                return
            
            vehiculo_info, ordenes = detalles['vehiculo'], detalles['ordenes']
            
            # Mostrar información del vehículo
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
            
            # Mostrar historial de órdenes
            if ordenes:
                resultados_text.insert(tk.END, f"\n{'═'*60}\n")
                resultados_text.insert(tk.END, f"🔧 HISTORIAL DE ÓRDENES ({len(ordenes)})\n")
                resultados_text.insert(tk.END, f"{'═'*60}\n\n")
                
                for orden in ordenes:
                    resultados_text.insert(tk.END, f"📋 ORDEN #{orden[0]}\n")
                    resultados_text.insert(tk.END, f"   📅 Fecha: {orden[1]} a {orden[2] or 'En progreso'}\n")
                    resultados_text.insert(tk.END, f"   🔧 Servicio: {orden[4]}\n")
                    resultados_text.insert(tk.END, f"   💰 Precio: Q{orden[5]:.2f}\n")
                    resultados_text.insert(tk.END, f"   🛣️  Kilometraje: {orden[6]} {orden[7]}\n")
                    resultados_text.insert(tk.END, f"   👷 Empleado: {orden[8] or 'No asignado'}\n")
                    resultados_text.insert(tk.END, f"   📝 Descripción: {orden[3][:100]}...\n")
                    resultados_text.insert(tk.END, f"{'─'*50}\n")
            else:
                resultados_text.insert(tk.END, f"\n❌ Este vehículo no tiene órdenes de trabajo registradas.\n")
        
        def buscar_interactivo():
            # Diálogo para buscar cliente primero
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
                listbox.delete(0, tk.END)
                clientes = self.taller.clientes.buscar_cliente_por_nombre(search_var.get())
                for cliente in clientes:
                    listbox.insert(tk.END, f"ID: {cliente[0]} | Nombre: {cliente[1]}")
            
            def seleccionar_cliente():
                seleccion = listbox.curselection()
                if not seleccion:
                    return
                
                texto = listbox.get(seleccion[0])
                cliente_id = int(texto.split("ID: ")[1].split(" |")[0])
                search_dialog.destroy()
                
                # Ahora mostrar vehículos del cliente
                mostrar_vehiculos_cliente(cliente_id)
            
            def mostrar_vehiculos_cliente(cliente_id):
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
        
        ttk.Label(dialog, text="🔍 HISTORIAL DE VEHÍCULO", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Opción 1: Buscar por placa
        frame_placa = ttk.Frame(dialog)
        frame_placa.pack(pady=10)
        ttk.Label(frame_placa, text="Placa del vehículo:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(frame_placa, textvariable=placa_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_placa, text="Buscar por Placa", command=buscar_por_placa).pack(side=tk.LEFT, padx=5)
        
        # Opción 2: Buscar interactivo
        ttk.Label(dialog, text="O buscar por cliente:").pack(pady=5)
        ttk.Button(dialog, text="Buscar Cliente Primero", command=buscar_interactivo).pack(pady=10)
        
        resultados_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
    
    def editar_cliente(self):
        """Edita la información de un cliente existente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Cliente")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables
        cliente_id_var = tk.StringVar()
        nombre_var = tk.StringVar()
        telefono_var = tk.StringVar()
        nit_var = tk.StringVar()
        
        def buscar_cliente():
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
                listbox.delete(0, tk.END)
                clientes = self.taller.clientes.buscar_cliente_por_nombre(search_var.get())
                for cliente in clientes:
                    listbox.insert(tk.END, f"ID: {cliente[0]} | Nombre: {cliente[1]} | Tel: {cliente[2] or 'N/A'}")
            
            def seleccionar():
                seleccion = listbox.curselection()
                if seleccion:
                    texto = listbox.get(seleccion[0])
                    cliente_id = int(texto.split("ID: ")[1].split(" |")[0])
                    cliente_id_var.set(str(cliente_id))
                    
                    # Cargar datos del cliente
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
            try:
                if not cliente_id_var.get().strip():
                    messagebox.showerror("Error", "Debe seleccionar un cliente")
                    return
                
                cliente_id = int(cliente_id_var.get())
                
                if not nombre_var.get().strip():
                    messagebox.showerror("Error", "El nombre del cliente es obligatorio")
                    return
                
                telefono = None
                if telefono_var.get().strip():
                    telefono = self.taller.validator.validar_telefono(telefono_var.get())
                    if not telefono:
                        messagebox.showerror("Error", "Teléfono inválido")
                        return
                
                nit = None
                if nit_var.get().strip():
                    nit = self.taller.validator.validar_nit(nit_var.get())
                    if not nit:
                        messagebox.showerror("Error", "NIT inválido")
                        return
                
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
        
        ttk.Label(dialog, text="✏️ EDITAR CLIENTE", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Buscar cliente
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
        """Edita la información de un empleado existente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Empleado")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variables
        empleado_id_var = tk.StringVar()
        nombre_var = tk.StringVar()
        telefono_var = tk.StringVar()
        
        def cargar_empleados():
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
            
            for empleado in empleados:
                listbox.insert(tk.END, f"ID: {empleado[0]} | {empleado[1]} | Tel: {empleado[2]}")
            
            def seleccionar():
                seleccion = listbox.curselection()
                if seleccion:
                    texto = listbox.get(seleccion[0])
                    empleado_id = int(texto.split("ID: ")[1].split(" |")[0])
                    empleado_id_var.set(str(empleado_id))
                    
                    # Cargar datos del empleado
                    nombre = texto.split("| ")[1].split(" |")[0]
                    telefono = texto.split("Tel: ")[1]
                    nombre_var.set(nombre)
                    telefono_var.set(telefono)
                    
                    search_dialog.destroy()
            
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            ttk.Button(search_dialog, text="Seleccionar", command=seleccionar).pack(pady=10)
        
        def guardar():
            try:
                if not empleado_id_var.get().strip():
                    messagebox.showerror("Error", "Debe seleccionar un empleado")
                    return
                
                empleado_id = int(empleado_id_var.get())
                
                if not nombre_var.get().strip():
                    messagebox.showerror("Error", "El nombre del empleado es obligatorio")
                    return
                
                telefono = self.taller.validator.validar_telefono(telefono_var.get())
                if not telefono:
                    messagebox.showerror("Error", "Teléfono inválido")
                    return
                
                resultado = self.taller.empleados.editar_empleado(
                    empleado_id,
                    nombre_var.get().strip(),
                    telefono
                )
                
                self.show_message(resultado)
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Label(dialog, text="✏️ EDITAR EMPLEADO", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Cargar empleados
        ttk.Button(dialog, text="Seleccionar Empleado", command=cargar_empleados).pack(pady=10)
        
        ttk.Label(dialog, text="ID Empleado:").pack(pady=5)
        ttk.Entry(dialog, textvariable=empleado_id_var, width=40, state='readonly').pack(pady=5)
        
        ttk.Label(dialog, text="Nombre completo:").pack(pady=5)
        ttk.Entry(dialog, textvariable=nombre_var, width=40).pack(pady=5)
        
        ttk.Label(dialog, text="Teléfono:").pack(pady=5)
        ttk.Entry(dialog, textvariable=telefono_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Guardar Cambios", command=guardar).pack(pady=20)
    
    def menu_reportes(self):
        """Muestra el menú de reportes con generación de gráficas"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Reportes Avanzados")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        def generar_reporte(periodo):
            reporte = self.taller.reportes.reporte_periodo(periodo)
            
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*60}\n")
            self.result_text.insert(tk.END, f"📊 REPORTE {periodo.upper()}\n")
            self.result_text.insert(tk.END, f"{'='*60}\n\n")
            self.result_text.insert(tk.END, f"📅 Período: {reporte['fecha_inicio']} al {datetime.now().date()}\n\n")
            self.result_text.insert(tk.END, f"💰 Ganancias totales: Q{reporte['ganancias']:.2f}\n")
            self.result_text.insert(tk.END, f"⏱️  Horas trabajadas: {reporte['horas_trabajadas']:.1f}\n")
            self.result_text.insert(tk.END, f"🔧 Trabajos completados: {reporte['trabajos_completados']}\n")
            
            if reporte['servicios_populares']:
                self.result_text.insert(tk.END, f"\n🏆 SERVICIOS MÁS POPULARES:\n")
                for servicio, cantidad, total in reporte['servicios_populares']:
                    self.result_text.insert(tk.END, f"   • {servicio}: {cantidad} trabajos (Q{total:.2f})\n")
            
            # Preguntar si generar gráfica
            dialog.destroy()
            
            if reporte['servicios_populares']:
                respuesta = messagebox.askyesno("Generar Gráfica", 
                    "¿Desea generar una gráfica de los servicios más populares?")
                
                if respuesta:
                    try:
                        nombre_archivo = f"servicios_populares_{periodo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        fig = self.taller.reportes.crear_grafica_servicios_populares(reporte, nombre_archivo)
                        
                        # Mostrar gráfica en nueva ventana
                        graph_dialog = tk.Toplevel(self.root)
                        graph_dialog.title(f"Gráfica - Servicios Populares {periodo.capitalize()}")
                        graph_dialog.geometry("800x600")
                        
                        canvas = FigureCanvasTkAgg(fig, master=graph_dialog)
                        canvas.draw()
                        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                        
                        ttk.Label(graph_dialog, 
                                 text=f"Gráfica guardada en: reportes/{nombre_archivo}.png",
                                 font=("Arial", 10)).pack(pady=10)
                        
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo generar la gráfica: {e}")
        
        def mostrar_proyeccion():
            proyeccion = self.taller.reportes.proyeccion_crecimiento()
            
            if not proyeccion:
                messagebox.showinfo("Información", "No hay suficientes datos históricos (se necesitan al menos 2 meses) para generar proyecciones")
                return
            
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*60}\n")
            self.result_text.insert(tk.END, "📈 PROYECCIÓN DE CRECIMIENTO\n")
            self.result_text.insert(tk.END, f"{'='*60}\n\n")
            
            # Mostrar datos históricos
            if 'datos_historicos' in proyeccion and proyeccion['datos_historicos']:
                self.result_text.insert(tk.END, "📊 DATOS HISTÓRICOS (últimos 6 meses):\n")
                for mes, total in proyeccion['datos_historicos']:
                    self.result_text.insert(tk.END, f"   {mes}: Q{total:.2f}\n")
                self.result_text.insert(tk.END, "\n")
            
            self.result_text.insert(tk.END, f"📈 Crecimiento promedio: {proyeccion['crecimiento_promedio']*100:.1f}% mensual\n")
            self.result_text.insert(tk.END, f"\n🔮 PROYECCIONES PRÓXIMOS 6 MESES:\n")
            for mes, ingreso in proyeccion['proyecciones']:
                self.result_text.insert(tk.END, f"   {mes}: Q{ingreso:.2f}\n")
            
            dialog.destroy()
        
        ttk.Label(dialog, text="📊 REPORTES AVANZADOS", font=("Arial", 12, "bold")).pack(pady=20)
        
        tk.Frame(dialog, height=2, bg="gray").pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(dialog, text="📅 Reporte Semanal", 
                  command=lambda: generar_reporte('semana')).pack(pady=5, padx=50, fill=tk.X)
        ttk.Button(dialog, text="📅 Reporte Mensual", 
                  command=lambda: generar_reporte('mes')).pack(pady=5, padx=50, fill=tk.X)
        ttk.Button(dialog, text="📅 Reporte Anual", 
                  command=lambda: generar_reporte('año')).pack(pady=5, padx=50, fill=tk.X)
        
        tk.Frame(dialog, height=2, bg="gray").pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(dialog, text="📈 Proyección de Crecimiento", 
                  command=mostrar_proyeccion).pack(pady=5, padx=50, fill=tk.X)
    
    def recordatorios_inteligentes(self):
        """Muestra recordatorios inteligentes"""
        tipos_servicio = self.taller.recordatorios.obtener_tipos_servicio_disponibles()
        
        if not tipos_servicio:
            messagebox.showinfo("Información", "No hay tipos de servicio registrados")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Recordatorios Inteligentes")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        listbox = tk.Listbox(dialog, width=70, height=15)
        scrollbar = tk.Scrollbar(dialog)
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        
        for servicio in tipos_servicio:
            listbox.insert(tk.END, f"🔧 {servicio}")
        
        def analizar_servicio():
            seleccion = listbox.curselection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Seleccione un tipo de servicio")
                return
            
            tipo_servicio = tipos_servicio[seleccion[0]]
            
            # Pedir margen de días
            margen_dias = simpledialog.askinteger(
                "Margen de días",
                f"¿En cuántos días quieres buscar recordatorios para '{tipo_servicio}'?",
                parent=dialog,
                minvalue=1,
                maxvalue=365,
                initialvalue=30
            )
            
            if not margen_dias:
                return
            
            recordatorios = self.taller.recordatorios.predecir_proximo_servicio(tipo_servicio, margen_dias)
            
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*60}\n")
            self.result_text.insert(tk.END, f"🔔 RECORDATORIOS PARA: {tipo_servicio}\n")
            self.result_text.insert(tk.END, f"📅 Margen: {margen_dias} días\n")
            self.result_text.insert(tk.END, f"{'='*60}\n\n")
            
            if recordatorios:
                self.result_text.insert(tk.END, f"🚗 VEHÍCULOS PRÓXIMOS A '{tipo_servicio}' ({len(recordatorios)}):\n\n")
                for i, recordatorio in enumerate(recordatorios, 1):
                    self.result_text.insert(tk.END, f"   {i}. {recordatorio['marca']} {recordatorio['modelo']} - {recordatorio['placa']}\n")
                    self.result_text.insert(tk.END, f"      👤 Cliente: {recordatorio['cliente']}\n")
                    self.result_text.insert(tk.END, f"      📞 Teléfono: {recordatorio['telefono'] or 'No tiene'}\n")
                    self.result_text.insert(tk.END, f"      📅 Último servicio: {recordatorio['ultimo_servicio']}\n")
                    self.result_text.insert(tk.END, f"      🎯 Próximo estimado: {recordatorio['proximo_estimado']}\n")
                    self.result_text.insert(tk.END, f"      ⏰ Días restantes: {recordatorio['dias_restantes']}\n")
                    self.result_text.insert(tk.END, "      " + "-" * 40 + "\n")
                
                self.result_text.insert(tk.END, f"\n💡 RECOMENDACIÓN: Contactar a estos clientes para programar su próximo servicio.\n")
            else:
                self.result_text.insert(tk.END, f"✅ No hay vehículos que necesiten '{tipo_servicio}' en los próximos {margen_dias} días\n")
                self.result_text.insert(tk.END, f"💡 ¡Buen trabajo! Los mantenimientos están al día.\n")
            
            dialog.destroy()
        
        ttk.Label(dialog, text="Seleccione el tipo de servicio a analizar:", 
                 font=("Arial", 10, "bold")).pack(pady=10)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        ttk.Button(dialog, text="Analizar", command=analizar_servicio).pack(pady=10)
    
    def salir(self):
        """Cierra la aplicación"""
        if messagebox.askyesno("Salir", "¿Está seguro que desea salir del sistema?"):
            self.root.destroy()

# ============================================================================
# PUNTO DE ENTRADA DEL PROGRAMA
# ============================================================================
def main():
    """Función principal para iniciar la aplicación"""
    root = tk.Tk()
    app = TallerSEYMOGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()