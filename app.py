# ============================================================================
# TALLER SEYMO - SISTEMA DE GESTIÓN PARA TALLER MECÁNICO
# Proyecto personal
# Autor: Miguel Sajquín
# Fecha: 2025
# ============================================================================

# Importación de bibliotecas necesarias
# Nota: Algunas de estas bibliotecas las aprendí en clase, otras las investigué
import sqlite3  # Para trabajar con bases de datos (SQLite es fácil para empezar)
import os  # Para manejar archivos y carpetas del sistema
from datetime import datetime, timedelta  # Para manejar fechas y tiempos
import pandas as pd  # Para análisis de datos (la vi en matemáticas aplicadas)
from collections import Counter  # Para contar elementos en listas
import matplotlib.pyplot as plt  # Para crear gráficas (aprendí en el curso de métodos numéricos)
from typing import Optional, Dict, List, Tuple  # Para dar tipos a las variables (nuevo para mí)
import warnings  # Para manejar advertencias
import sys  # Para controlar el sistema

# Esto es para evitar advertencias molestas que aparecían
# El profesor dijo que está bien usar esto en proyectos pequeños
warnings.filterwarnings('ignore', category=DeprecationWarning)

# ============================================================================
# FUNCIÓN PARA CREAR CARPETAS
# Esto lo hice porque al principio el programa fallaba si no existían las carpetas
# ============================================================================
def crear_estructura_carpetas():
    """Crea todas las carpetas necesarias antes de iniciar el sistema"""
    try:
        # Defino las carpetas que necesito
        # 'database' para la base de datos
        # 'database/backups' para copias de seguridad (por si algo sale mal)
        # 'reportes' para guardar las gráficas que genere el sistema
        carpetas = ['database', 'database/backups', 'reportes']
        
        # Recorro cada carpeta
        for carpeta in carpetas:
            # Si la carpeta no existe, la creo
            if not os.path.exists(carpeta):
                os.makedirs(carpeta)  # makedirs crea carpetas y subcarpetas
                print(f"✅ Carpeta '{carpeta}' creada")
        return True  # Si todo sale bien, retorno True
    except Exception as e:
        # Si hay algún error, muestro mensaje y retorno False
        print(f"❌ Error crítico creando carpetas: {e}")
        return False

# ============================================================================
# INICIALIZACIÓN DEL SISTEMA
# Esto se ejecuta apenas se importa el archivo
# ============================================================================

# Primero creo las carpetas necesarias
if not crear_estructura_carpetas():
    # Si no se pueden crear las carpetas, el programa no puede continuar
    print("❌ No se pudo crear la estructura de carpetas. Saliendo...")
    sys.exit(1)  # Salgo del programa con código de error 1

# Intento importar seaborn para gráficas más bonitas
# Seaborn no es obligatorio, pero si está disponible, la uso
try:
    import seaborn as sns  # Seaborn hace gráficas más profesionales
    SEABORN_AVAILABLE = True  # Variable para saber si seaborn está disponible
    print("✅ seaborn cargado correctamente")
except ImportError:
    # Si seaborn no está instalado, uso matplotlib normal
    SEABORN_AVAILABLE = False
    print("⚠️  seaborn no está disponible. Usando estilos básicos de matplotlib.")

print("✅ Estructura de carpetas configurada correctamente")

# ============================================================================
# CLASE DATABASEMANAGER
# Esta clase maneja todo lo relacionado con la base de datos
# La hice siguiendo el patrón que vimos en clase: una clase por responsabilidad
# ============================================================================
class DatabaseManager:
    """Maneja la conexión y operaciones básicas de la base de datos"""
    
    def __init__(self, db_path: str = 'database/taller.db'):
        # Inicializo la ruta de la base de datos
        # Por defecto usa 'database/taller.db'
        self.db_path = db_path
        self.conn = None  # La conexión empieza como None
        self._initialize_database()  # Llamo al método de inicialización
    
    def _initialize_database(self):
        """Inicializa la base de datos con manejo robusto de errores"""
        try:
            # Creo la conexión a la base de datos
            self.conn = self._create_connection()
            if self.conn is not None:
                # Si la conexión se creó, creo las tablas
                self.create_tables()
                print("✅ Base de datos inicializada correctamente")
            else:
                # Si no se pudo crear, lanzo un error
                raise sqlite3.Error("No se pudo crear la conexión")
        except sqlite3.Error as e:
            # Capturo cualquier error y muestro mensaje
            print(f"❌ Error inicializando base de datos: {e}")
            raise  # Vuelvo a lanzar el error para que lo maneje el código que llamó
    
    def _create_connection(self):
        """Crea conexión a la base de datos con manejo de errores"""
        try:
            # Creo la conexión con SQLite
            # check_same_thread=False permite usar la conexión desde varios hilos
            # detect_types ayuda a manejar tipos de datos como fechas
            conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            # Activo las foreign keys (relaciones entre tablas)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as e:
            print(f"❌ Error creando conexión a la base de datos: {e}")
            return None
    
    def create_tables(self):
        """Crea todas las tablas necesarias"""
        # Verifico que haya conexión
        if self.conn is None:
            raise sqlite3.Error("No hay conexión a la base de datos")
        
        cursor = self.conn.cursor()  # Creo un cursor para ejecutar comandos SQL
        
        try:
            # Tabla clientes - almacena información de los clientes del taller
            # AUTOINCREMENT hace que el ID se genere automáticamente
            # UNIQUE asegura que no haya duplicados en teléfono y NIT
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    telefono TEXT UNIQUE,
                    nit TEXT UNIQUE
                )
            ''')
            
            # Tabla vehículos - almacena los vehículos de cada cliente
            # FOREIGN KEY relaciona con la tabla clientes
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
            
            # Tabla empleados - información de los mecánicos del taller
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS empleados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    telefono TEXT UNIQUE
                )
            ''')
            
            # Tabla órdenes de trabajo - registro de todos los trabajos realizados
            # Aquí es donde se guarda la información de cada servicio
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
            
            # Verifico si necesito actualizar las tablas
            # Esto es útil cuando cambio la estructura de la base de datos
            self._verificar_y_actualizar_tablas()
            
            self.conn.commit()  # Guardo los cambios en la base de datos
            print("✅ Tablas creadas/verificadas correctamente")
            
        except sqlite3.Error as e:
            # Si hay error, deshago los cambios
            self.conn.rollback()
            print(f"❌ Error creando tablas: {e}")
            raise
    
    def _verificar_y_actualizar_tablas(self):
        """Verifica y actualiza la estructura de las tablas si es necesario"""
        cursor = self.conn.cursor()
        
        try:
            print("🔄 Verificando estructura de tablas...")
            
            # Verifico la tabla clientes
            # PRAGMA table_info me dice qué columnas tiene una tabla
            cursor.execute("PRAGMA table_info(clientes)")
            columnas_clientes = [col[1] for col in cursor.fetchall()]
            print(f"📋 Columnas actuales en clientes: {columnas_clientes}")
            
            # Si la columna 'nit' no existe, la agrego
            # Esto pasó cuando agregué el campo NIT después de crear la base de datos
            if 'nit' not in columnas_clientes:
                print("🔄 Agregando columna 'nit' a tabla clientes...")
                cursor.execute('ALTER TABLE clientes ADD COLUMN nit TEXT UNIQUE')
                print("✅ Columna 'nit' agregada a clientes")
            
            # Verifico la tabla vehículos
            cursor.execute("PRAGMA table_info(vehiculos)")
            columnas_vehiculos = [col[1] for col in cursor.fetchall()]
            print(f"📋 Columnas actuales en vehiculos: {columnas_vehiculos}")
            
            # Agrego columnas si no existen
            if 'proximo_mantenimiento' not in columnas_vehiculos:
                print("🔄 Agregando columna 'proximo_mantenimiento' a vehiculos...")
                cursor.execute('ALTER TABLE vehiculos ADD COLUMN proximo_mantenimiento DATE')
                print("✅ Columna 'proximo_mantenimiento' agregada a vehiculos")
            
            if 'kilometraje_ultimo_mantenimiento' not in columnas_vehiculos:
                print("🔄 Agregando columna 'kilometraje_ultimo_mantenimiento' a vehiculos...")
                cursor.execute('ALTER TABLE vehiculos ADD COLUMN kilometraje_ultimo_mantenimiento REAL')
                print("✅ Columna 'kilometraje_ultimo_mantenimiento' agregada a vehiculos")
            
            self.conn.commit()
            print("✅ Estructura de tablas actualizada correctamente")
            
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"❌ Error al actualizar tablas: {e}")
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Ejecuta una consulta y retorna el cursor"""
        # Método simple para ejecutar consultas SQL
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor
    
    def commit(self):
        """Realiza commit"""
        # Método para guardar cambios en la base de datos
        self.conn.commit()

    def diagnosticar_estructura_bd(self):
        """Diagnostica la estructura actual de la base de datos"""
        # Este método me ayuda a ver qué tablas y columnas tengo
        # Es útil para depurar problemas
        cursor = self.conn.cursor()
        
        try:
            print("\n🔍 DIAGNÓSTICO DE ESTRUCTURA DE BD")
            
            # Muestro información de la tabla clientes
            cursor.execute("PRAGMA table_info(clientes)")
            columnas = cursor.fetchall()
            print("\n📋 TABLA CLIENTES:")
            for col in columnas:
                print(f"   - {col[1]} ({col[2]})")  # Nombre de columna y tipo
            
            # Cuento cuántos clientes hay
            cursor.execute("SELECT COUNT(*) FROM clientes")
            total_clientes = cursor.fetchone()[0]
            print(f"   Total de clientes: {total_clientes}")
            
            # Muestro información de la tabla vehículos
            cursor.execute("PRAGMA table_info(vehiculos)")
            columnas_vehiculos = cursor.fetchall()
            print("\n📋 TABLA VEHICULOS:")
            for col in columnas_vehiculos:
                print(f"   - {col[1]} ({col[2]})")
            
        except sqlite3.Error as e:
            print(f"❌ Error en diagnóstico: {e}")

# ============================================================================
# CLASE VALIDATOR
# Esta clase se encarga de validar todos los datos que ingresan los usuarios
# Aprendí que es importante validar para evitar errores y datos incorrectos
# ============================================================================
class Validator:
    """Maneja todas las validaciones de datos"""
    
    @staticmethod
    def validar_numero(valor: str, tipo: str = "entero") -> Optional[float]:
        """Valida que el valor sea un número válido"""
        try:
            if not valor.strip():  # Si el valor está vacío
                return None
            if tipo == "entero":
                return int(valor)  # Convierto a entero
            elif tipo == "decimal":
                return float(valor)  # Convierto a decimal
            else:
                return valor
        except ValueError:
            # Si no se puede convertir a número, retorno None
            return None
    
    @staticmethod
    def validar_telefono(telefono: str) -> Optional[str]:
        """Valida que el teléfono contenga solo números y tenga longitud razonable"""
        if telefono is None or telefono.strip() == "":
            return None
        
        # Filtro solo los dígitos del teléfono
        telefono_limpio = ''.join(filter(str.isdigit, telefono))
        
        # Verifico que tenga una longitud razonable
        if len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
            return None
        
        return telefono_limpio
    
    @staticmethod
    def validar_nit(nit: str) -> Optional[str]:
        """Valida que el NIT contenga solo números, letras y guiones, y tenga longitud razonable"""
        if nit is None or nit.strip() == "":
            return None
        
        # Filtro caracteres válidos: letras, números, guiones y espacios
        nit_limpio = ''.join(filter(lambda c: c.isalnum() or c in '- ', nit))
        
        # Verifico longitud
        if len(nit_limpio) < 3 or len(nit_limpio) > 20:
            return None
        
        return nit_limpio
    
    @staticmethod
    def validar_fecha(fecha_str: str, permitir_futuro: bool = True, permitir_pasado: bool = True) -> Optional[datetime.date]:
        """Valida y convierte una fecha en formato string a date"""
        try:
            if not fecha_str.strip():
                return None
                
            # Si el usuario ingresa un número, lo interpreto como días desde hoy
            if fecha_str.isdigit():
                dias = int(fecha_str)
                fecha = datetime.now() + timedelta(days=dias)
            else:
                # Si ingresa una fecha en formato YYYY-MM-DD
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            
            hoy = datetime.now().date()
            fecha_date = fecha.date()
            
            # Validaciones de rango de fecha
            if fecha_date < datetime(2000, 1, 1).date():
                print("❌ Error: La fecha no puede ser anterior al año 2000.")
                return None
            
            if fecha_date > hoy + timedelta(days=365):
                print("❌ Error: La fecha no puede ser más de 1 año en el futuro.")
                return None
                
            if not permitir_futuro and fecha_date > hoy:
                print("❌ Error: La fecha no puede ser futura.")
                return None
                
            if not permitir_pasado and fecha_date < hoy:
                print("❌ Error: La fecha no puede ser pasada.")
                return None
            
            return fecha_date
            
        except ValueError:
            print("❌ Error: Formato de fecha inválido. Use YYYY-MM-DD o número de días.")
            return None
    
    @staticmethod
    def validar_año_vehiculo(año: int) -> bool:
        """Valida que el año del vehículo sea razonable"""
        año_actual = datetime.now().year
        # Un vehículo no puede ser de antes de 1900 ni de más de 2 años en el futuro
        return 1900 <= año <= año_actual + 2

# ============================================================================
# CLASE CLIENTEMANAGER
# Maneja todas las operaciones relacionadas con clientes
# Usé el principio de responsabilidad única: cada clase hace una cosa
# ============================================================================
class ClienteManager:
    """Gestiona todas las operaciones relacionadas con clientes"""
    
    def __init__(self, db_manager: DatabaseManager, validator: Validator):
        # Recibo las dependencias por constructor (inyección de dependencias)
        self.db = db_manager
        self.validator = validator
    
    def agregar_cliente(self, nombre: str, telefono: Optional[str] = None, nit: Optional[str] = None) -> Optional[int]:
        """Agrega un nuevo cliente a la base de datos"""
        try:
            # Ejecuto la consulta INSERT para agregar el cliente
            cursor = self.db.execute_query(
                'INSERT INTO clientes (nombre, telefono, nit) VALUES (?, ?, ?)', 
                (nombre, telefono, nit)
            )
            self.db.commit()  # Guardo los cambios
            print(f"✅ Cliente '{nombre}' agregado con ID: {cursor.lastrowid}")
            return cursor.lastrowid  # Retorno el ID del nuevo cliente
        except sqlite3.IntegrityError as e:
            # Manejo errores de duplicados
            if "telefono" in str(e):
                print("❌ Error: Ya existe un cliente con ese teléfono")
            elif "nit" in str(e):
                print("❌ Error: Ya existe un cliente con ese NIT")
            else:
                print("❌ Error de integridad en la base de datos")
            return None
    
    def cliente_existe(self, cliente_id: int) -> bool:
        """Verifica si un cliente existe"""
        # Consulta simple para verificar existencia
        cursor = self.db.execute_query('SELECT id FROM clientes WHERE id = ?', (cliente_id,))
        return cursor.fetchone() is not None
    
    def buscar_cliente_por_nombre(self, nombre_buscar: str) -> List[Tuple]:
        """Busca clientes por nombre"""
        # Uso LIKE para búsqueda parcial (contiene el texto)
        cursor = self.db.execute_query(
            'SELECT id, nombre, telefono, nit FROM clientes WHERE nombre LIKE ? ORDER BY nombre',
            (f'%{nombre_buscar}%',)  # % significa "cualquier texto antes/después"
        )
        return cursor.fetchall()
    
    def editar_cliente(self, cliente_id: int, nuevo_nombre: str, nuevo_telefono: Optional[str], nuevo_nit: Optional[str]) -> str:
        """Edita la información de un cliente"""
        try:
            # Consulta UPDATE para modificar el cliente
            self.db.execute_query(
                'UPDATE clientes SET nombre = ?, telefono = ?, nit = ? WHERE id = ?',
                (nuevo_nombre, nuevo_telefono, nuevo_nit, cliente_id)
            )
            self.db.commit()
            print(f"✅ Cliente ID {cliente_id} actualizado")
            return f"✅ Cliente ID {cliente_id} actualizado"
        except sqlite3.IntegrityError as e:
            # Manejo errores de duplicados
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
        
        # Obtengo información básica del cliente
        cursor = self.db.execute_query(
            'SELECT nombre, telefono, nit FROM clientes WHERE id = ?', 
            (cliente_id,)
        )
        cliente_info = cursor.fetchone()
        
        # Obtengo todos los vehículos del cliente
        cursor = self.db.execute_query(
            'SELECT id, marca, modelo, año, placa, color FROM vehiculos WHERE cliente_id = ?',
            (cliente_id,)
        )
        vehiculos = cursor.fetchall()
        
        # Retorno un diccionario con toda la información
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
# Maneja operaciones relacionadas con vehículos
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
            mensaje = f"✅ Vehículo {marca} {modelo} agregado (ID: {cursor.lastrowid})"
            print(mensaje)
            return mensaje
        except sqlite3.IntegrityError:
            return "❌ Error: Ya existe un vehículo con esa placa"
    
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
        
        # Obtengo información del vehículo y su dueño
        cursor = self.db.execute_query('''
            SELECT v.marca, v.modelo, v.año, v.placa, v.color, c.nombre, c.telefono, c.nit
            FROM vehiculos v
            JOIN clientes c ON v.cliente_id = c.id
            WHERE v.id = ?
        ''', (vehiculo_id,))
        vehiculo_info = cursor.fetchone()
        
        # Obtengo el historial de órdenes de este vehículo
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

# ============================================================================
# CLASE EMPLEADOMANAGER
# Maneja operaciones relacionadas con empleados
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
            mensaje = f"✅ Empleado '{nombre}' agregado (ID: {cursor.lastrowid})"
            print(mensaje)
            return mensaje
        except sqlite3.IntegrityError:
            return "❌ Error: Ya existe un empleado con ese teléfono"
    
    def empleado_existe(self, empleado_id: int) -> bool:
        """Verifica si un empleado existe"""
        cursor = self.db.execute_query('SELECT id FROM empleados WHERE id = ?', (empleado_id,))
        return cursor.fetchone() is not None
    
    def listar_empleados(self) -> List[Tuple]:
        """Lista todos los empleados"""
        cursor = self.db.execute_query('SELECT id, nombre FROM empleados ORDER BY nombre')
        return cursor.fetchall()
    
    def editar_empleado(self, empleado_id: int, nuevo_nombre: str, nuevo_telefono: str) -> str:
        """Edita la información de un empleado"""
        try:
            self.db.execute_query(
                'UPDATE empleados SET nombre = ?, telefono = ? WHERE id = ?',
                (nuevo_nombre, nuevo_telefono, empleado_id)
            )
            self.db.commit()
            print(f"✅ Empleado ID {empleado_id} actualizado")
            return f"✅ Empleado ID {empleado_id} actualizado"
        except sqlite3.IntegrityError:
            return "❌ Error: Ya existe un empleado con ese teléfono"

# ============================================================================
# CLASE ORDENMANAGER
# Maneja operaciones relacionadas con órdenes de trabajo
# Aquí es donde se guarda la información de los servicios realizados
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
        
        # Consulta compleja que junta información de varias tablas
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
        
        # Organizo toda la información en un diccionario
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
        
        # Valido la fecha de finalización
        fecha_fin_validada = None
        if fecha_fin:
            fecha_fin_validada = self.validator.validar_fecha(fecha_fin, permitir_futuro=True, permitir_pasado=True)
            if fecha_fin_validada is None:
                return "❌ Error: Fecha de finalización inválida."
        else:
            # Si no se especifica fecha, uso la actual
            fecha_fin_validada = datetime.now().date()
        
        # Calculo el precio final (repuestos + mano de obra)
        precio_final = costo_repuestos + costo_mano_obra
        
        try:
            # Inserto la nueva orden
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
            mensaje = f"✅ Orden #{numero_orden} agregada - Total: Q{precio_final}"
            print(mensaje)
            return mensaje
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
            print(f"✅ Orden #{orden_id} actualizada")
            return f"✅ Orden #{orden_id} actualizada"
        except Exception as e:
            return f"❌ Error al editar orden: {e}"

# ============================================================================
# CLASE REPORTMANAGER
# Maneja la generación de reportes y gráficas
# Esta es la parte más interesante del proyecto, donde uso análisis de datos
# ============================================================================
class ReportManager:
    """Gestiona la generación de reportes y gráficas"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def reporte_periodo(self, periodo: str = 'semana') -> Dict:
        """Genera reportes del período especificado"""
        # Determino la fecha de inicio según el período
        if periodo == 'semana':
            fecha_inicio = datetime.now() - timedelta(days=datetime.now().weekday())
        elif periodo == 'mes':
            fecha_inicio = datetime.now().replace(day=1)
        else:  # 'año'
            fecha_inicio = datetime.now().replace(month=1, day=1)
        
        # Obtengo estadísticas básicas
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
        
        # Retorno todo en un diccionario
        return {
            'ganancias': ganancias or 0,
            'horas_trabajadas': horas or 0,
            'trabajos_completados': trabajos or 0,
            'periodo': periodo,
            'fecha_inicio': fecha_inicio.date(),
            'servicios_populares': servicios_populares
        }
    
    def reporte_periodo_historico(self, año: int, periodo: str = 'año') -> Dict:
        """Genera reportes para años pasados"""
        # Similar al anterior, pero para períodos históricos
        if periodo == 'año':
            fecha_inicio = datetime(año, 1, 1)
            fecha_fin = datetime(año, 12, 31)
        elif periodo == 'mes':
            fecha_inicio = datetime(año, datetime.now().month, 1)
            fecha_fin = datetime(año, datetime.now().month, 1) + timedelta(days=32)
            fecha_fin = fecha_fin.replace(day=1) - timedelta(days=1)
        else:
            fecha_inicio = datetime(año, 1, 1)
            fecha_fin = datetime(año, 12, 31)
        
        cursor = self.db.execute_query('''
            SELECT SUM(precio_final), SUM(horas_trabajadas), COUNT(*)
            FROM ordenes_trabajo 
            WHERE fecha_fin BETWEEN ? AND ?
        ''', (fecha_inicio.date(), fecha_fin.date()))
        
        ganancias, horas, trabajos = cursor.fetchone()
        
        cursor = self.db.execute_query('''
            SELECT tipo_servicio, COUNT(*), SUM(precio_final)
            FROM ordenes_trabajo 
            WHERE fecha_fin BETWEEN ? AND ?
            GROUP BY tipo_servicio
            ORDER BY COUNT(*) DESC
            LIMIT 5
        ''', (fecha_inicio.date(), fecha_fin.date()))
        
        servicios_populares = cursor.fetchall()
        
        return {
            'ganancias': ganancias or 0,
            'horas_trabajadas': horas or 0,
            'trabajos_completados': trabajos or 0,
            'periodo': periodo,
            'año': año,
            'fecha_inicio': fecha_inicio.date(),
            'fecha_fin': fecha_fin.date(),
            'servicios_populares': servicios_populares
        }
    
    def proyeccion_crecimiento(self) -> Optional[Dict]:
        """Genera proyecciones de crecimiento basadas en datos históricos"""
        # Este es el método más avanzado, usa análisis de tendencias
        fecha_inicio = datetime.now().replace(day=1) - timedelta(days=365)
        
        # Obtengo datos mensuales
        cursor = self.db.execute_query('''
            SELECT strftime('%Y-%m', fecha_fin) as mes, 
                   SUM(precio_final) as ingresos,
                   COUNT(*) as trabajos
            FROM ordenes_trabajo 
            WHERE fecha_fin >= ?
            GROUP BY mes
            ORDER BY mes
        ''', (fecha_inicio.date(),))
        
        datos_mensuales = cursor.fetchall()
        
        # Necesito al menos 3 meses de datos para hacer proyecciones
        if len(datos_mensuales) < 3:
            return None
        
        # Calculo el crecimiento promedio
        ingresos = [d[1] for d in datos_mensuales]
        crecimiento_promedio = sum((ingresos[i] - ingresos[i-1]) / ingresos[i-1] 
                                 for i in range(1, len(ingresos))) / (len(ingresos) - 1)
        
        # Proyecto para los próximos 6 meses
        ultimo_ingreso = ingresos[-1]
        proyecciones = []
        
        for i in range(1, 7):
            mes_proyectado = (datetime.now() + timedelta(days=30*i)).strftime('%Y-%m')
            # Fórmula de crecimiento compuesto
            ingreso_proyectado = ultimo_ingreso * (1 + crecimiento_promedio) ** i
            proyecciones.append((mes_proyectado, ingreso_proyectado))
        
        return {
            'crecimiento_promedio': crecimiento_promedio,
            'proyecciones': proyecciones,
            'datos_historicos': datos_mensuales
        }
    
    def predecir_alta_demanda(self) -> Dict:
        """Predice períodos de alta demanda basado en patrones históricos"""
        # Analizo en qué meses hay más trabajo históricamente
        cursor = self.db.execute_query('''
            SELECT strftime('%m', fecha_fin) as mes, 
                   COUNT(*) as cantidad_trabajos,
                   AVG(precio_final) as precio_promedio
            FROM ordenes_trabajo 
            GROUP BY mes
            ORDER BY cantidad_trabajos DESC
        ''')
        
        datos_mensuales = cursor.fetchall()
        
        # Identifico los 3 meses con mayor demanda
        meses_alta_demanda = []
        for mes, cantidad, precio in datos_mensuales[:3]:
            nombre_mes = self._obtener_nombre_mes(int(mes))
            meses_alta_demanda.append({
                'mes': nombre_mes,
                'trabajos': cantidad,
                'precio_promedio': precio or 0
            })
        
        return {
            'meses_alta_demanda': meses_alta_demanda,
            'todos_los_meses': datos_mensuales
        }
    
    def _obtener_nombre_mes(self, numero_mes: int) -> str:
        """Convierte número de mes a nombre"""
        meses = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        return meses[numero_mes - 1] if 1 <= numero_mes <= 12 else f"Mes {numero_mes}"
    
    def crear_grafica_servicios_populares(self, reporte: Dict, nombre_archivo: str):
        """Crea gráfica de servicios más populares"""
        if not reporte['servicios_populares']:
            print("❌ No hay datos para generar la gráfica")
            return
        
        # Extraigo datos para la gráfica
        servicios = [s[0] for s in reporte['servicios_populares']]
        cantidades = [s[1] for s in reporte['servicios_populares']]
        
        # Creo la figura
        plt.figure(figsize=(10, 6))
        
        # Uso seaborn si está disponible (hace gráficas más bonitas)
        if SEABORN_AVAILABLE:
            sns.barplot(x=cantidades, y=servicios, palette='viridis')
            plt.title('Servicios Más Solicitados', fontsize=14, fontweight='bold')
        else:
            plt.barh(servicios, cantidades, color='skyblue', alpha=0.7)
            plt.title('Servicios Más Solicitados', fontsize=14, fontweight='bold')
        
        plt.xlabel('Cantidad de Trabajos')
        plt.tight_layout()
        
        # Guardo la gráfica en un archivo
        archivo_path = f'reportes/{nombre_archivo}.png'
        plt.savefig(archivo_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Gráfica guardada: {archivo_path}")
    
    def crear_grafica_ingresos_mensuales(self, datos_mensuales: List[Tuple], nombre_archivo: str):
        """Crea gráfica de ingresos mensuales"""
        if not datos_mensuales:
            print("❌ No hay datos para generar la gráfica")
            return
        
        meses = [d[0] for d in datos_mensuales]
        ingresos = [d[1] for d in datos_mensuales]
        
        plt.figure(figsize=(12, 6))
        
        if SEABORN_AVAILABLE:
            sns.lineplot(x=meses, y=ingresos, marker='o', linewidth=2.5)
            plt.title('Ingresos Mensuales', fontsize=14, fontweight='bold')
        else:
            plt.plot(meses, ingresos, marker='o', linewidth=2, markersize=6)
            plt.title('Ingresos Mensuales', fontsize=14, fontweight='bold')
            
        plt.xlabel('Mes')
        plt.ylabel('Ingresos (Q)')  # Q es Quetzales (moneda de Guatemala)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        archivo_path = f'reportes/{nombre_archivo}.png'
        plt.savefig(archivo_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Gráfica guardada: {archivo_path}")
    
    def crear_grafica_proyeccion(self, proyeccion: Dict, nombre_archivo: str):
        """Crea gráfica de proyección de crecimiento"""
        # Separo datos históricos y proyecciones
        meses_historicos = [d[0] for d in proyeccion['datos_historicos']]
        ingresos_historicos = [d[1] for d in proyeccion['datos_historicos']]
        
        meses_proyeccion = [p[0] for p in proyeccion['proyecciones']]
        ingresos_proyeccion = [p[1] for p in proyeccion['proyecciones']]
        
        plt.figure(figsize=(12, 6))
        
        if SEABORN_AVAILABLE:
            sns.lineplot(x=meses_historicos, y=ingresos_historicos, marker='o', label='Histórico', linewidth=2.5)
            sns.lineplot(x=meses_proyeccion, y=ingresos_proyeccion, marker='o', label='Proyección', linestyle='--', linewidth=2.5)
        else:
            plt.plot(meses_historicos, ingresos_historicos, 'b-o', label='Histórico', linewidth=2)
            plt.plot(meses_proyeccion, ingresos_proyeccion, 'r--o', label='Proyección', linewidth=2)
        
        plt.title('Proyección de Crecimiento', fontsize=14, fontweight='bold')
        plt.xlabel('Mes')
        plt.ylabel('Ingresos (Q)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        archivo_path = f'reportes/{nombre_archivo}.png'
        plt.savefig(archivo_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Gráfica guardada: {archivo_path}")

# ============================================================================
# CLASE RECORDATORIOSINTELIGENTES
# Esta es la parte más avanzada del sistema
# Usa análisis de datos para predecir cuándo los vehículos necesitarán mantenimiento
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
    
    def calcular_promedio_entre_servicios(self, tipo_servicio: str) -> Dict:
        """Calcula el promedio de tiempo entre servicios para un tipo específico"""
        # Uso la función LAG de SQL para comparar servicios consecutivos
        cursor = self.db.execute_query('''
            SELECT o.vehiculo_id, o.fecha_fin, o.kilometraje,
                   LAG(o.fecha_fin) OVER (PARTITION BY o.vehiculo_id ORDER BY o.fecha_fin) as fecha_anterior,
                   LAG(o.kilometraje) OVER (PARTITION BY o.vehiculo_id ORDER BY o.fecha_fin) as km_anterior
            FROM ordenes_trabajo o
            WHERE o.tipo_servicio = ?
            ORDER BY o.vehiculo_id, o.fecha_fin
        ''', (tipo_servicio,))
        
        datos = cursor.fetchall()
        
        if not datos:
            return {'dias_promedio': 0, 'km_promedio': 0, 'total_vehiculos': 0, 'total_servicios': 0}
        
        # Calculo diferencias entre servicios consecutivos
        diferencias_dias = []
        diferencias_km = []
        vehiculos_analizados = set()
        total_servicios = 0
        
        for i in range(1, len(datos)):
            vehiculo_actual, fecha_actual, km_actual, fecha_anterior, km_anterior = datos[i]
            
            if fecha_anterior and km_anterior: 
                # Manejo diferentes formatos de fecha (string vs date)
                if isinstance(fecha_actual, str):
                    fecha_actual_dt = datetime.strptime(fecha_actual, '%Y-%m-%d')
                else:
                    fecha_actual_dt = datetime.combine(fecha_actual, datetime.min.time())
                    
                if isinstance(fecha_anterior, str):
                    fecha_anterior_dt = datetime.strptime(fecha_anterior, '%Y-%m-%d')
                else:
                    fecha_anterior_dt = datetime.combine(fecha_anterior, datetime.min.time())
                
                # Calculo diferencia en días
                dias_diferencia = (fecha_actual_dt - fecha_anterior_dt).days
                
                # Calculo diferencia en kilómetros
                km_diferencia = km_actual - km_anterior
                
                # Solo considero diferencias positivas
                if dias_diferencia > 0 and km_diferencia > 0:
                    diferencias_dias.append(dias_diferencia)
                    diferencias_km.append(km_diferencia)
                    vehiculos_analizados.add(vehiculo_actual)
                    total_servicios += 1
        
        if diferencias_dias:
            return {
                'dias_promedio': sum(diferencias_dias) / len(diferencias_dias),
                'km_promedio': sum(diferencias_km) / len(diferencias_km),
                'total_vehiculos': len(vehiculos_analizados),
                'total_servicios': total_servicios
            }
        else:
            return {'dias_promedio': 0, 'km_promedio': 0, 'total_vehiculos': 0, 'total_servicios': 0}
    
    def obtener_ultimo_servicio_vehiculo(self, vehiculo_id: int, tipo_servicio: str) -> Optional[Tuple]:
        """Obtiene el último servicio de un tipo específico para un vehículo"""
        cursor = self.db.execute_query('''
            SELECT fecha_fin, kilometraje 
            FROM ordenes_trabajo 
            WHERE vehiculo_id = ? AND tipo_servicio = ?
            ORDER BY fecha_fin DESC 
            LIMIT 1
        ''', (vehiculo_id, tipo_servicio))
        
        resultado = cursor.fetchone()
        
        if resultado:
            fecha, kilometraje = resultado
            if not isinstance(fecha, str):
                fecha = fecha.strftime('%Y-%m-%d')  # Convierto a string si es date
            return (fecha, kilometraje)
        
        return None
    
    def predecir_proximo_servicio(self, tipo_servicio: str, margen_dias: int = 30) -> List[Dict]:
        """Predice qué vehículos necesitarán pronto un servicio específico"""
        # Obtengo estadísticas del servicio
        estadisticas = self.calcular_promedio_entre_servicios(tipo_servicio)
        
        if estadisticas['total_servicios'] == 0:
            return []
        
        # Obtengo todos los vehículos que han tenido este servicio
        cursor = self.db.execute_query('''
            SELECT DISTINCT v.id, v.marca, v.modelo, v.placa, c.nombre, c.telefono, c.nit
            FROM vehiculos v
            JOIN ordenes_trabajo o ON v.id = o.vehiculo_id
            JOIN clientes c ON v.cliente_id = c.id
            WHERE o.tipo_servicio = ?
        ''', (tipo_servicio,))
        
        vehiculos = cursor.fetchall()
        resultados = []
        
        for vehiculo in vehiculos:
            vehiculo_id, marca, modelo, placa, cliente, telefono, nit = vehiculo
            
            # Obtengo último servicio de este tipo
            ultimo_servicio = self.obtener_ultimo_servicio_vehiculo(vehiculo_id, tipo_servicio)
            
            if ultimo_servicio:
                fecha_ultimo, km_ultimo = ultimo_servicio
                
                # Convierto fecha si es necesario
                if isinstance(fecha_ultimo, str):
                    fecha_ultimo_dt = datetime.strptime(fecha_ultimo, '%Y-%m-%d')
                else:
                    fecha_ultimo_dt = datetime.combine(fecha_ultimo, datetime.min.time())
                
                # Calculo fecha estimada del próximo servicio
                # Usando el promedio histórico
                fecha_estimada = fecha_ultimo_dt + timedelta(days=estadisticas['dias_promedio'])
                km_estimado = km_ultimo + estadisticas['km_promedio']
                
                # Verifico si está próximo (dentro del margen de días)
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
                        'ultimo_servicio': fecha_ultimo if isinstance(fecha_ultimo, str) else fecha_ultimo.strftime('%Y-%m-%d'),
                        'km_ultimo': km_ultimo,
                        'proximo_estimado': fecha_estimada.strftime('%Y-%m-%d'),
                        'km_estimado': km_estimado,
                        'dias_restantes': dias_restantes,
                        'dias_promedio_historico': estadisticas['dias_promedio'],
                        'km_promedio_historico': estadisticas['km_promedio']
                    })
        
        # Ordeno por proximidad (menos días primero)
        resultados.sort(key=lambda x: x['dias_restantes'])
        return resultados
    
    def obtener_vehiculos_sin_servicio(self, tipo_servicio: str) -> List[Tuple]:
        """Obtiene vehículos que nunca han tenido este tipo de servicio"""
        # Estos vehículos podrían necesitar su primer servicio
        cursor = self.db.execute_query('''
            SELECT v.id, v.marca, v.modelo, v.placa, c.nombre, c.telefono, c.nit
            FROM vehiculos v
            JOIN clientes c ON v.cliente_id = c.id
            WHERE v.id NOT IN (
                SELECT DISTINCT vehiculo_id 
                FROM ordenes_trabajo 
                WHERE tipo_servicio = ?
            )
        ''', (tipo_servicio,))
        
        return cursor.fetchall()
    
    def analizar_patrones_todos_servicios(self) -> Dict:
        """Analiza patrones para todos los tipos de servicio disponibles"""
        # Este método analiza todos los servicios de una vez
        tipos_servicio = self.obtener_tipos_servicio_disponibles()
        resultados = {}
        
        for tipo_servicio in tipos_servicio:
            estadisticas = self.calcular_promedio_entre_servicios(tipo_servicio)
            predicciones = self.predecir_proximo_servicio(tipo_servicio, 60)  # 60 días de margen
            
            resultados[tipo_servicio] = {
                'estadisticas': estadisticas,
                'predicciones': predicciones,
                'total_predicciones': len(predicciones)
            }
        
        return resultados

# ============================================================================
# CLASE TALLERSEYMO
# Clase principal que coordina todas las funcionalidades
# Esta es la clase que orquesta todo el sistema
# ============================================================================
class TallerSEYMO:
    """Clase principal que coordina todas las funcionalidades del taller"""
    
    def __init__(self):
        try:
            # Inicializo todas las dependencias
            self.db = DatabaseManager()
            self.validator = Validator()
            self.clientes = ClienteManager(self.db, self.validator)
            self.vehiculos = VehiculoManager(self.db, self.validator)
            self.empleados = EmpleadoManager(self.db, self.validator)
            self.ordenes = OrdenManager(self.db, self.validator)
            self.reportes = ReportManager(self.db)
            self.recordatorios = RecordatoriosInteligentes(self.db)
            
            # Diagnóstico inicial
            self.db.diagnosticar_estructura_bd()
            
            print("✅ Sistema Taller SEYMO inicializado correctamente")
            
        except Exception as e:
            # Si hay error al inicializar, intento recrear la base de datos
            print(f"❌ Error crítico iniciando el sistema: {e}")
            print("🔄 Intentando recrear base de datos...")
            self._recrear_base_datos()
    
    def _recrear_base_datos(self):
        """Recrea la base de datos desde cero"""
        import os
        import sqlite3
        
        db_path = 'database/taller.db'
        
        # Cierro conexión si existe
        if hasattr(self, 'db') and self.db.conn:
            self.db.conn.close()
        
        # Elimino el archivo existente
        if os.path.exists(db_path):
            os.remove(db_path)
            print("🗑️ Base de datos anterior eliminada")
        
        # Recreo carpetas
        crear_estructura_carpetas()
        
        # Reintento inicialización
        try:
            self.db = DatabaseManager()
            self.validator = Validator()
            self.clientes = ClienteManager(self.db, self.validator)
            self.vehiculos = VehiculoManager(self.db, self.validator)
            self.empleados = EmpleadoManager(self.db, self.validator)
            self.ordenes = OrdenManager(self.db, self.validator)
            self.reportes = ReportManager(self.db)
            self.recordatorios = RecordatoriosInteligentes(self.db)
            
            print("✅ Nueva base de datos creada exitosamente")
            
        except Exception as e:
            print(f"❌ Error fatal: No se pudo crear la base de datos: {e}")
            raise

    # ==========================================================================
    # MÉTODOS PARA INTERACCIÓN CON EL USUARIO
    # Estos métodos manejan la entrada de datos con validación y reintentos
    # ==========================================================================
    
    def pedir_numero_con_reintentos(self, mensaje: str, tipo: str = "entero", intentos: int = 5) -> Optional[float]:
        """Pide un número al usuario con reintentos y mensajes de error claros"""
        for intento in range(intentos):
            try:
                valor = input(mensaje).strip()
                if not valor:
                    print("❌ Error: No puedes dejar este campo vacío.")
                    continue
                    
                resultado = self.validator.validar_numero(valor, tipo)
                
                if resultado is not None:
                    return resultado
                else:
                    print(f"❌ Error: Debes ingresar un número {'entero' if tipo == 'entero' else 'decimal'} válido.")
                    intentos_restantes = intentos - intento - 1
                    if intentos_restantes > 0:
                        print(f"💡 Te quedan {intentos_restantes} intentos.")
                    else:
                        print("❌ Has agotado todos los intentos.")
                    
            except KeyboardInterrupt:
                print("\n❌ Operación cancelada por el usuario.")
                return None
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                return None
        return None
    
    def pedir_telefono_con_reintentos(self, mensaje: str, obligatorio: bool = False, intentos: int = 5) -> Optional[str]:
        """Pide un teléfono con validación y reintentos"""
        for intento in range(intentos):
            try:
                telefono = input(mensaje).strip()
                
                if not obligatorio and not telefono:
                    return None
                
                if obligatorio and not telefono:
                    print("❌ Error: El teléfono es obligatorio.")
                    continue
                
                telefono_validado = self.validator.validar_telefono(telefono)
                if not telefono_validado:
                    print("❌ Error: El teléfono debe contener solo números (7-15 dígitos). Ejemplo: 1234567890")
                    intentos_restantes = intentos - intento - 1
                    if intentos_restantes > 0:
                        print(f"💡 Te quedan {intentos_restantes} intentos.")
                    continue
                
                if self.telefono_existe(telefono_validado):
                    print("❌ Error: Este número de teléfono ya está registrado en el sistema.")
                    intentos_restantes = intentos - intento - 1
                    if intentos_restantes > 0:
                        print(f"💡 Te quedan {intentos_restantes} intentos.")
                    continue
                
                return telefono_validado
                
            except KeyboardInterrupt:
                print("\n❌ Operación cancelada por el usuario.")
                return None
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                return None
        return None
    
    def pedir_nit_con_reintentos(self, mensaje: str, obligatorio: bool = False, intentos: int = 5) -> Optional[str]:
        """Pide un NIT con validación y reintentos"""
        for intento in range(intentos):
            try:
                nit = input(mensaje).strip()
                
                if not obligatorio and not nit:
                    return None
                
                if obligatorio and not nit:
                    print("❌ Error: El NIT es obligatorio.")
                    continue
                
                nit_validado = self.validator.validar_nit(nit)
                if not nit_validado:
                    print("❌ Error: El NIT debe contener solo números, letras y guiones (3-20 caracteres).")
                    intentos_restantes = intentos - intento - 1
                    if intentos_restantes > 0:
                        print(f"💡 Te quedan {intentos_restantes} intentos.")
                    continue
                
                if self.nit_existe(nit_validado):
                    print("❌ Error: Este NIT ya está registrado en el sistema.")
                    intentos_restantes = intentos - intento - 1
                    if intentos_restantes > 0:
                        print(f"💡 Te quedan {intentos_restantes} intentos.")
                    continue
                
                return nit_validado
                
            except KeyboardInterrupt:
                print("\n❌ Operación cancelada por el usuario.")
                return None
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                return None
        return None
    
    def telefono_existe(self, telefono: str) -> bool:
        """Verifica si un teléfono ya existe"""
        # Verifico en clientes
        cursor = self.db.execute_query('SELECT id FROM clientes WHERE telefono = ?', (telefono,))
        if cursor.fetchone():
            return True
        
        # Verifico en empleados
        cursor = self.db.execute_query('SELECT id FROM empleados WHERE telefono = ?', (telefono,))
        return cursor.fetchone() is not None
    
    def nit_existe(self, nit: str) -> bool:
        """Verifica si un NIT ya existe"""
        return self.clientes.nit_existe(nit)
    
    def seleccionar_cliente_interactivo(self) -> Optional[int]:
        """Permite al usuario buscar y seleccionar un cliente interactivamente"""
        while True:
            try:
                nombre_buscar = input("\n🔍 Nombre del cliente a buscar (Enter para cancelar): ").strip()
                if not nombre_buscar:
                    return None
                
                clientes = self.clientes.buscar_cliente_por_nombre(nombre_buscar)
                
                if not clientes:
                    print("❌ No se encontraron clientes con ese nombre. Intenta con otro nombre.")
                    continue
                
                print(f"\n✅ Se encontraron {len(clientes)} cliente(s):")
                for i, cliente in enumerate(clientes, 1):
                    telefono_info = f" - Tel: {cliente[2]}" if cliente[2] else ""
                    nit_info = f" - NIT: {cliente[3]}" if cliente[3] else ""
                    print(f"   {i}. ID: {cliente[0]} - {cliente[1]}{telefono_info}{nit_info}")
                
                seleccion = input(f"\nSelecciona un cliente (1-{len(clientes)}) o 0 para buscar de nuevo: ").strip()
                if seleccion == "0":
                    continue
                
                if not seleccion.isdigit():
                    print("❌ Error: Debes ingresar un número.")
                    continue
                
                idx = int(seleccion) - 1
                if 0 <= idx < len(clientes):
                    return clientes[idx][0]
                else:
                    print(f"❌ Error: Selección inválida. Debe ser entre 1 y {len(clientes)}.")
                    
            except KeyboardInterrupt:
                print("\n❌ Operación cancelada por el usuario.")
                return None
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                return None
    
    def seleccionar_vehiculo_interactivo(self, cliente_id: int) -> Optional[int]:
        """Permite seleccionar un vehículo de un cliente con reintentos"""
        while True:
            try:
                vehiculos = self.vehiculos.obtener_vehiculos_cliente(cliente_id)
                
                if not vehiculos:
                    print("❌ Este cliente no tiene vehículos registrados.")
                    return None
                
                print(f"\n🚗 Vehículos del cliente:")
                for i, vehiculo in enumerate(vehiculos, 1):
                    print(f"   {i}. {vehiculo[1]} {vehiculo[2]} {vehiculo[3]} - Placa: {vehiculo[4]}")
                
                seleccion = input(f"\nSelecciona un vehículo (1-{len(vehiculos)}) o 0 para cancelar: ").strip()
                if seleccion == "0":
                    return None
                
                if not seleccion.isdigit():
                    print("❌ Error: Debes ingresar un número.")
                    continue
                
                idx = int(seleccion) - 1
                if 0 <= idx < len(vehiculos):
                    return vehiculos[idx][0]
                else:
                    print(f"❌ Error: Selección inválida. Debe ser entre 1 y {len(vehiculos)}.")
                    
            except KeyboardInterrupt:
                print("\n❌ Operación cancelada por el usuario.")
                return None
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                return None
    
    def pedir_empleado_id_con_reintentos(self, intentos: int = 5) -> Optional[int]:
        """Pide el ID de un empleado con validación y reintentos"""
        for intento in range(intentos):
            try:
                print("\n--- Lista de Empleados ---")
                empleados = self.empleados.listar_empleados()
                if not empleados:
                    print("❌ No hay empleados registrados en el sistema.")
                    return None
                
                for empleado in empleados:
                    print(f"  ID: {empleado[0]} - {empleado[1]}")
                
                empleado_id = self.pedir_numero_con_reintentos("\nID del empleado: ", "entero", 3)
                if empleado_id is None:
                    return None
                
                if not self.empleados.empleado_existe(empleado_id):
                    print("❌ Error: El empleado no existe. Verifica el ID e intenta nuevamente.")
                    intentos_restantes = intentos - intento - 1
                    if intentos_restantes > 0:
                        print(f"💡 Te quedan {intentos_restantes} intentos.")
                    continue
                
                return empleado_id
                
            except KeyboardInterrupt:
                print("\n❌ Operación cancelada por el usuario.")
                return None
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                return None
        return None

    # ==========================================================================
    # MÉTODOS PARA EL SISTEMA INTELIGENTE DE RECORDATORIOS
    # ==========================================================================
    
    def menu_recordatorios_inteligentes(self):
        """Menú interactivo para recordatorios inteligentes predictivos"""
        while True:
            print(f"\n{'='*60}")
            print("🧠 SISTEMA INTELIGENTE DE RECORDATORIOS PREDICTIVOS")
            print("="*60)
            
            tipos_servicio = self.recordatorios.obtener_tipos_servicio_disponibles()
            
            if not tipos_servicio:
                print("❌ No hay tipos de servicio registrados en el sistema.")
                print("   Agregue algunas órdenes de trabajo primero.")
                return
            
            print("🔧 TIPOS DE SERVICIO DISPONIBLES:")
            for i, servicio in enumerate(tipos_servicio, 1):
                print(f"   {i}. {servicio}")
            
            print(f"   0. ↩️ Volver al menú principal")
            print("="*60)
            
            try:
                seleccion = input("\nSelecciona el tipo de mantenimiento a analizar: ")
                
                if seleccion == "0":
                    return
                
                idx = int(seleccion) - 1
                if 0 <= idx < len(tipos_servicio):
                    tipo_servicio_seleccionado = tipos_servicio[idx]
                    self.analizar_recordatorios_servicio(tipo_servicio_seleccionado)
                else:
                    print("❌ Selección inválida.")
                    
            except ValueError:
                print("❌ Por favor ingresa un número válido.")

    def analizar_recordatorios_servicio(self, tipo_servicio: str):
        """Analiza y muestra recordatorios para un tipo de servicio específico"""
        print(f"\n📊 ANALIZANDO: {tipo_servicio}")
        print("⏳ Calculando patrones de mantenimiento...")
        
        estadisticas = self.recordatorios.calcular_promedio_entre_servicios(tipo_servicio)
        
        print(f"\n📈 ESTADÍSTICAS DEL SISTEMA PARA '{tipo_servicio}':")
        print(f"   📅 Promedio de días entre servicios: {estadisticas['dias_promedio']:.0f} días")
        print(f"   🛣️  Promedio de km entre servicios: {estadisticas['km_promedio']:.0f} km")
        print(f"   🚗 Vehículos analizados: {estadisticas['total_vehiculos']}")
        print(f"   🔧 Servicios analizados: {estadisticas['total_servicios']}")
        
        if estadisticas['total_servicios'] == 0:
            print("\n❌ No hay suficientes datos históricos para hacer predicciones.")
            return
        
        # Pido al usuario el margen de días para buscar
        margen_dias = self.pedir_numero_con_reintentos("\n🔍 ¿En cuántos días quieres buscar recordatorios? (ej: 30): ", "entero")
        if margen_dias is None:
            margen_dias = 30
        
        print(f"\n🔔 BUSCANDO VEHÍCULOS QUE NECESITARÁN SERVICIO EN PRÓXIMOS {margen_dias} DÍAS...")
        
        recordatorios = self.recordatorios.predecir_proximo_servicio(tipo_servicio, margen_dias)
        
        if recordatorios:
            print(f"\n🚗 VEHÍCULOS PRÓXIMOS A '{tipo_servicio}' ({len(recordatorios)}):")
            for i, recordatorio in enumerate(recordatorios, 1):
                print(f"\n   {i}. {recordatorio['marca']} {recordatorio['modelo']} - {recordatorio['placa']}")
                print(f"      👤 Cliente: {recordatorio['cliente']} - 📞 {recordatorio['telefono'] or 'No tiene'} - 🏢 {recordatorio['nit'] or 'No tiene'}")
                print(f"      📅 Último servicio: {recordatorio['ultimo_servicio']} ({recordatorio['km_ultimo']} km)")
                print(f"      🎯 Próximo estimado: {recordatorio['proximo_estimado']} ({recordatorio['km_estimado']:.0f} km)")
                print(f"      ⏰ Días restantes: {recordatorio['dias_restantes']} días")
                print(f"      📊 Basado en: {recordatorio['dias_promedio_historico']:.0f} días / {recordatorio['km_promedio_historico']:.0f} km promedio")
                print("      " + "-" * 50)
        else:
            print(f"\n✅ No hay vehículos que necesiten '{tipo_servicio}' en los próximos {margen_dias} días")
        
        # Muestro vehículos sin historial de este servicio
        vehiculos_sin_servicio = self.recordatorios.obtener_vehiculos_sin_servicio(tipo_servicio)
        if vehiculos_sin_servicio:
            print(f"\n🚙 VEHÍCULOS SIN HISTORIAL DE '{tipo_servicio}' ({len(vehiculos_sin_servicio)}):")
            print("   (Podrían necesitar su primer servicio de este tipo)")
            for vehiculo in vehiculos_sin_servicio[:5]: 
                nit_info = f" - NIT: {vehiculo[6]}" if vehiculo[6] else ""
                print(f"   • {vehiculo[1]} {vehiculo[2]} - {vehiculo[3]} - {vehiculo[4]}{nit_info}")
            
            if len(vehiculos_sin_servicio) > 5:
                print(f"   ... y {len(vehiculos_sin_servicio) - 5} más")

    def analizar_todos_los_servicios(self):
        """Analiza todos los tipos de servicio disponibles"""
        print(f"\n{'='*60}")
        print("📊 ANÁLISIS COMPLETO DE TODOS LOS SERVICIOS")
        print("="*60)
        
        resultados = self.recordatorios.analizar_patrones_todos_servicios()
        
        if not resultados:
            print("❌ No hay datos suficientes para realizar el análisis.")
            return
        
        total_predicciones = 0
        for tipo_servicio, datos in resultados.items():
            estadisticas = datos['estadisticas']
            predicciones = datos['predicciones']
            
            print(f"\n🔧 {tipo_servicio.upper()}:")
            print(f"   📊 {estadisticas['total_servicios']} servicios analizados")
            print(f"   🚗 {estadisticas['total_vehiculos']} vehículos en historial")
            print(f"   ⏱️  Promedio: {estadisticas['dias_promedio']:.0f} días / {estadisticas['km_promedio']:.0f} km")
            print(f"   🔔 {len(predicciones)} vehículos necesitarán servicio pronto")
            
            total_predicciones += len(predicciones)
        
        print(f"\n📈 RESUMEN GENERAL:")
        print(f"   🔧 Tipos de servicio analizados: {len(resultados)}")
        print(f"   🚗 Total de predicciones activas: {total_predicciones}")
        print(f"   💡 Recomendación: {'Contacta clientes proactivamente' if total_predicciones > 0 else 'Mantenimiento preventivo al día'}")

    def generar_reporte_proactivo(self):
        """Genera un reporte proactivo para contactar clientes"""
        print(f"\n{'='*60}")
        print("📞 REPORTE PROACTIVO PARA CONTACTO DE CLIENTES")
        print("="*60)
        
        tipos_servicio = self.recordatorios.obtener_tipos_servicio_disponibles()
        clientes_a_contactar = []
        
        for tipo_servicio in tipos_servicio:
            # Busco vehículos que necesitarán servicio en los próximos 15 días
            recordatorios = self.recordatorios.predecir_proximo_servicio(tipo_servicio, 15)
            
            for recordatorio in recordatorios:
                clientes_a_contactar.append({
                    'tipo_servicio': tipo_servicio,
                    'cliente': recordatorio['cliente'],
                    'telefono': recordatorio['telefono'],
                    'nit': recordatorio['nit'],
                    'vehiculo': f"{recordatorio['marca']} {recordatorio['modelo']}",
                    'placa': recordatorio['placa'],
                    'proximo_servicio': recordatorio['proximo_estimado'],
                    'dias_restantes': recordatorio['dias_restantes']
                })
        
        # Ordeno por días restantes (más urgentes primero)
        clientes_a_contactar.sort(key=lambda x: x['dias_restantes'])
        
        if clientes_a_contactar:
            print(f"\n📞 CLIENTES A CONTACTAR ({len(clientes_a_contactar)}):")
            for i, cliente in enumerate(clientes_a_contactar, 1):
                print(f"\n   {i}. {cliente['cliente']}")
                print(f"      📞 Teléfono: {cliente['telefono'] or 'No tiene'}")
                print(f"      🏢 NIT: {cliente['nit'] or 'No tiene'}")
                print(f"      🚗 Vehículo: {cliente['vehiculo']} - {cliente['placa']}")
                print(f"      🔧 Servicio: {cliente['tipo_servicio']}")
                print(f"      📅 Próximo servicio: {cliente['proximo_servicio']}")
                print(f"      ⏰ Urgencia: {cliente['dias_restantes']} días restantes")
                print("      " + "-" * 40)
            
            print(f"\n💡 ACCIONES RECOMENDADAS:")
            print("   • Contacta a los clientes con menos de 7 días restantes primero")
            print("   • Ofrece descuentos por reserva anticipada")
            print("   • Programa citas con al menos 3 días de anticipación")
        else:
            print("\n✅ No hay clientes que necesiten contacto inmediato")
            print("💡 Todos los mantenimientos están bajo control")

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================
def mostrar_reporte(reporte: Dict, taller):
    """Muestra un reporte formateado"""
    print(f"\n📊 REPORTE {reporte['periodo'].upper()}")
    print(f"   📅 Período: {reporte['fecha_inicio']} al {datetime.now().date()}")
    print(f"   💰 Ganancias totales: Q{reporte['ganancias']:.2f}")
    print(f"   ⏱️  Horas trabajadas: {reporte['horas_trabajadas']:.1f}")
    print(f"   🔧 Trabajos completados: {reporte['trabajos_completados']}")
    
    if reporte['servicios_populares']:
        print(f"\n   🏆 SERVICIOS MÁS POPULARES:")
        for servicio, cantidad, total in reporte['servicios_populares']:
            print(f"      • {servicio}: {cantidad} trabajos (Q{total:.2f})")
    
    # Pregunto si quiere generar gráfica
    if reporte['servicios_populares'] and input("\n¿Generar gráfica? (s/n): ").lower() == 's':
        nombre_archivo = f"servicios_populares_{reporte['periodo']}_{datetime.now().strftime('%Y%m%d')}"
        taller.reportes.crear_grafica_servicios_populares(reporte, nombre_archivo)

# ============================================================================
# MENÚ PRINCIPAL
# Esta es la función principal que muestra el menú y maneja las opciones
# ============================================================================
def menu_principal():
    """Función principal con todas las opciones implementadas"""
    try:
        # Inicializo el sistema
        taller = TallerSEYMO()
    except Exception as e:
        print(f"❌ Error crítico iniciando el sistema: {e}")
        return
    
    while True:
        try:
            # Muestro el menú principal
            print("\n" + "="*50)
            print("🔧 TALLER SEYMO - SISTEMA DE GESTIÓN")
            print("="*50)
            
            print("📝 CREAR Y REGISTRAR")
            print("  1. Nuevo Cliente + Vehículos")
            print("  2. Nuevo Empleado")
            print("  3. Nueva Orden de Trabajo")
            print("  4. Añadir Vehículo a Cliente Existente")
            
            print("\n🔍 BUSCAR Y CONSULTAR")
            print("  5. Buscar y Ver Cliente")
            print("  6. Ver Historial por Vehículo")
            print("  7. Buscar Orden por ID")
            
            print("\n✏️ EDITAR Y ACTUALIZAR")
            print("  8. Editar Cliente")
            print("  9. Editar Empleado")
            print("  10. Editar Orden")
            
            print("\n📊 REPORTES Y ANÁLISIS")
            print("  11. Ver Reportes Avanzados")
            
            print("\n🧠 MANTENIMIENTO INTELIGENTE")
            print("  12. Recordatorios Inteligentes Predictivos")
            print("  13. Análisis Completo de Servicios")
            print("  14. Reporte Proactivo para Clientes")
            
            print("\n  0. Salir del Sistema")
            print("="*50)
            
            opcion = input("\nSelecciona una opción: ").strip()
            
            # Opción 1: Nuevo Cliente + Vehículos
            if opcion == "1":
                print("\n👤 REGISTRAR NUEVO CLIENTE Y VEHÍCULOS")
                nombre = input("Nombre del cliente: ").strip()
                if not nombre:
                    print("❌ El nombre del cliente es obligatorio.")
                    continue
                
                telefono = taller.pedir_telefono_con_reintentos("Teléfono del cliente (opcional): ", obligatorio=False)
                if telefono is None and input("¿Continuar sin teléfono? (s/n): ").lower() != 's':
                    continue
                
                nit = taller.pedir_nit_con_reintentos("NIT del cliente (opcional): ", obligatorio=False)
                
                cliente_id = taller.clientes.agregar_cliente(nombre, telefono, nit)
                if cliente_id is None:
                    continue
                
                while True:
                    print(f"\n🚗 AGREGAR VEHÍCULO PARA {nombre}")
                    marca = input("Marca del vehículo: ").strip()
                    modelo = input("Línea del vehículo: ").strip()
                    
                    año = taller.pedir_numero_con_reintentos("Año del vehículo: ", "entero")
                    if año is None:
                        continue
                    
                    if not taller.validator.validar_año_vehiculo(año):
                        print("❌ Año del vehículo inválido.")
                        continue
                    
                    placa = input("Placa del vehículo: ").strip().upper()
                    if not placa:
                        print("❌ La placa es obligatoria.")
                        continue
                    
                    if taller.vehiculos.placa_existe(placa):
                        print("❌ Ya existe un vehículo con esa placa.")
                        continue
                    
                    color = input("Color del vehículo (opcional): ").strip()
                    
                    resultado = taller.vehiculos.agregar_vehiculo(cliente_id, marca, modelo, año, placa, color)
                    print(resultado)
                    
                    if input("\n¿Agregar otro vehículo? (s/n): ").lower() != 's':
                        break

            # Opción 2: Nuevo Empleado
            elif opcion == "2":
                print("\n👷 REGISTRAR NUEVO EMPLEADO")
                nombre = input("Nombre del empleado: ").strip()
                if not nombre:
                    print("❌ El nombre del empleado es obligatorio.")
                    continue
                
                telefono = taller.pedir_telefono_con_reintentos("Teléfono del empleado: ", obligatorio=True)
                if telefono is None:
                    continue
                
                resultado = taller.empleados.agregar_empleado(nombre, telefono)
                print(resultado)

            # Opción 3: Nueva Orden de Trabajo
            elif opcion == "3":
                print("\n📋 NUEVA ORDEN DE TRABAJO")
                
                cliente_id = taller.seleccionar_cliente_interactivo()
                if cliente_id is None:
                    continue
                
                vehiculo_id = taller.seleccionar_vehiculo_interactivo(cliente_id)
                if vehiculo_id is None:
                    continue
                
                empleado_id = taller.pedir_empleado_id_con_reintentos()
                if empleado_id is None:
                    continue
                
                numero_orden = taller.pedir_numero_con_reintentos("Número de orden: ", "entero")
                if numero_orden is None:
                    continue
                
                descripcion = input("Descripción del trabajo: ").strip()
                if not descripcion:
                    print("❌ La descripción es obligatoria.")
                    continue
                
                tipo_servicio = input("Tipo de servicio: ").strip()
                if not tipo_servicio:
                    print("❌ El tipo de servicio es obligatorio.")
                    continue
                
                horas = taller.pedir_numero_con_reintentos("Horas trabajadas: ", "decimal")
                if horas is None:
                    continue
                
                costo_repuestos = taller.pedir_numero_con_reintentos("Costo de repuestos (Q): ", "decimal")
                if costo_repuestos is None:
                    continue
                
                costo_mano_obra = taller.pedir_numero_con_reintentos("Costo de mano de obra (Q): ", "decimal")
                if costo_mano_obra is None:
                    continue
                
                kilometraje = taller.pedir_numero_con_reintentos("Kilometraje del vehículo: ", "decimal")
                if kilometraje is None:
                    continue
                
                unidad_km = input("Unidad de kilometraje (km/millas) [km]: ").strip() or "km"
                
                fecha_fin = input("Fecha de finalización (YYYY-MM-DD o Enter para hoy): ").strip()
                
                resultado = taller.ordenes.agregar_orden(
                    numero_orden, vehiculo_id, empleado_id, descripcion, tipo_servicio,
                    horas, costo_repuestos, costo_mano_obra, kilometraje, unidad_km, fecha_fin
                )
                print(resultado)

            # Opción 4: Añadir Vehículo a Cliente Existente
            elif opcion == "4":
                print("\n🚗 AÑADIR VEHÍCULO A CLIENTE EXISTENTE")
                
                cliente_id = taller.seleccionar_cliente_interactivo()
                if cliente_id is None:
                    continue
                
                marca = input("Marca del vehículo: ").strip()
                modelo = input("Línea del vehículo: ").strip()
                
                año = taller.pedir_numero_con_reintentos("Año del vehículo: ", "entero")
                if año is None:
                    continue
                
                if not taller.validator.validar_año_vehiculo(año):
                    print("❌ Año del vehículo inválido.")
                    continue
                
                placa = input("Placa del vehículo: ").strip().upper()
                if not placa:
                    print("❌ La placa es obligatoria.")
                    continue
                
                if taller.vehiculos.placa_existe(placa):
                    print("❌ Ya existe un vehículo con esa placa.")
                    continue
                
                color = input("Color del vehículo (opcional): ").strip()
                
                resultado = taller.vehiculos.agregar_vehiculo(cliente_id, marca, modelo, año, placa, color)
                print(resultado)

            # Opción 5: Buscar y Ver Cliente
            elif opcion == "5":
                print("\n🔍 BUSCAR Y VER CLIENTE")
                cliente_id = taller.seleccionar_cliente_interactivo()
                if cliente_id is None:
                    continue
                
                detalles = taller.clientes.detalles_cliente(cliente_id)
                if detalles:
                    cliente_info, vehiculos = detalles['cliente'], detalles['vehiculos']
                    print(f"\n📋 DETALLES DEL CLIENTE:")
                    print(f"   👤 Nombre: {cliente_info[0]}")
                    print(f"   📞 Teléfono: {cliente_info[1] or 'No tiene'}")
                    print(f"   🏢 NIT: {cliente_info[2] or 'No tiene'}")
                    
                    if vehiculos:
                        print(f"\n🚗 VEHÍCULOS ({len(vehiculos)}):")
                        for i, vehiculo in enumerate(vehiculos, 1):
                            print(f"   {i}. {vehiculo[1]} {vehiculo[2]} {vehiculo[3]} - Placa: {vehiculo[4]} - Color: {vehiculo[5] or 'No especificado'}")
                    else:
                        print("\n❌ Este cliente no tiene vehículos registrados.")
                else:
                    print("❌ No se pudieron obtener los detalles del cliente.")

            # Opción 6: Ver Historial por Vehículo
            elif opcion == "6":
                print("\n🚗 VER HISTORIAL POR VEHÍCULO")
                cliente_id = taller.seleccionar_cliente_interactivo()
                if cliente_id is None:
                    continue
                
                vehiculo_id = taller.seleccionar_vehiculo_interactivo(cliente_id)
                if vehiculo_id is None:
                    continue
                
                detalles = taller.vehiculos.detalles_vehiculo(vehiculo_id)
                if detalles:
                    vehiculo_info, ordenes = detalles['vehiculo'], detalles['ordenes']
                    print(f"\n📋 DETALLES DEL VEHÍCULO:")
                    print(f"   🚗 Vehículo: {vehiculo_info[0]} {vehiculo_info[1]} {vehiculo_info[2]}")
                    print(f"   🏷️  Placa: {vehiculo_info[3]}")
                    print(f"   🎨 Color: {vehiculo_info[4] or 'No especificado'}")
                    print(f"   👤 Cliente: {vehiculo_info[5]} - 📞 {vehiculo_info[6] or 'No tiene'} - 🏢 {vehiculo_info[7] or 'No tiene'}")
                    
                    if ordenes:
                        print(f"\n🔧 HISTORIAL DE ÓRDENES ({len(ordenes)}):")
                        for orden in ordenes:
                            print(f"\n   📋 Orden #{orden[0]}")
                            print(f"      📅 Fecha: {orden[1]} a {orden[2] or 'En progreso'}")
                            print(f"      🔧 Servicio: {orden[4]}")
                            print(f"      💰 Precio: Q{orden[5]:.2f}")
                            print(f"      🛣️  Kilometraje: {orden[6]} {orden[7]}")
                            print(f"      👷 Empleado: {orden[8] or 'No asignado'}")
                            print(f"      📝 Descripción: {orden[3]}")
                            print("      " + "-" * 40)
                    else:
                        print("\n❌ Este vehículo no tiene órdenes de trabajo.")
                else:
                    print("❌ No se pudieron obtener los detalles del vehículo.")

            # Opción 7: Buscar Orden por ID
            elif opcion == "7":
                print("\n🔍 BUSCAR ORDEN POR ID")
                orden_id = taller.pedir_numero_con_reintentos("ID de la orden: ", "entero")
                if orden_id is None:
                    continue
                
                detalles = taller.ordenes.obtener_detalles_orden(orden_id)
                if detalles:
                    print(f"\n📋 DETALLES DE ORDEN #{detalles['id']}:")
                    print(f"   🚗 Vehículo: {detalles['vehiculo_marca']} {detalles['vehiculo_modelo']} {detalles['vehiculo_año']}")
                    print(f"   🏷️  Placa: {detalles['vehiculo_placa']}")
                    print(f"   👤 Cliente: {detalles['cliente_nombre']} - 📞 {detalles['cliente_telefono'] or 'No tiene'} - 🏢 {detalles['cliente_nit'] or 'No tiene'}")
                    print(f"   👷 Empleado: {detalles['empleado_nombre'] or 'No asignado'}")
                    print(f"   📅 Fechas: {detalles['fecha_inicio']} a {detalles['fecha_fin']}")
                    print(f"   🔧 Tipo servicio: {detalles['tipo_servicio']}")
                    print(f"   ⏱️  Horas trabajadas: {detalles['horas_trabajadas']}")
                    print(f"   💰 Costo repuestos: Q{detalles['costo_repuestos']:.2f}")
                    print(f"   💰 Costo mano obra: Q{detalles['costo_mano_obra']:.2f}")
                    print(f"   💰 Precio final: Q{detalles['precio_final']:.2f}")
                    print(f"   🛣️  Kilometraje: {detalles['kilometraje']} {detalles['unidad_kilometraje']}")
                    print(f"   📝 Descripción: {detalles['descripcion_trabajo']}")
                else:
                    print("❌ No se encontró la orden con ese ID.")

            # Opción 8: Editar Cliente
            elif opcion == "8":
                print("\n✏️ EDITAR CLIENTE")
                cliente_id = taller.seleccionar_cliente_interactivo()
                if cliente_id is None:
                    continue
                
                nuevo_nombre = input("Nuevo nombre del cliente: ").strip()
                if not nuevo_nombre:
                    print("❌ El nombre no puede estar vacío.")
                    continue
                
                nuevo_telefono = taller.pedir_telefono_con_reintentos("Nuevo teléfono (opcional): ", obligatorio=False)
                nuevo_nit = taller.pedir_nit_con_reintentos("Nuevo NIT (opcional): ", obligatorio=False)
                
                resultado = taller.clientes.editar_cliente(cliente_id, nuevo_nombre, nuevo_telefono, nuevo_nit)
                print(resultado)

            # Opción 9: Editar Empleado
            elif opcion == "9":
                print("\n✏️ EDITAR EMPLEADO")
                empleado_id = taller.pedir_numero_con_reintentos("ID del empleado a editar: ", "entero")
                if empleado_id is None:
                    continue
                
                if not taller.empleados.empleado_existe(empleado_id):
                    print("❌ No existe un empleado con ese ID.")
                    continue
                
                nuevo_nombre = input("Nuevo nombre del empleado: ").strip()
                if not nuevo_nombre:
                    print("❌ El nombre no puede estar vacío.")
                    continue
                
                nuevo_telefono = taller.pedir_telefono_con_reintentos("Nuevo teléfono del empleado: ", obligatorio=True)
                if nuevo_telefono is None:
                    continue
                
                resultado = taller.empleados.editar_empleado(empleado_id, nuevo_nombre, nuevo_telefono)
                print(resultado)

            # Opción 10: Editar Orden
            elif opcion == "10":
                print("\n✏️ EDITAR ORDEN")
                orden_id = taller.pedir_numero_con_reintentos("ID de la orden a editar: ", "entero")
                if orden_id is None:
                    continue
                
                if not taller.ordenes.orden_existe(orden_id):
                    print("❌ No existe una orden con ese ID.")
                    continue
                
                nueva_descripcion = input("Nueva descripción del trabajo: ").strip()
                if not nueva_descripcion:
                    print("❌ La descripción no puede estar vacía.")
                    continue
                
                nuevo_precio = taller.pedir_numero_con_reintentos("Nuevo precio final (Q): ", "decimal")
                if nuevo_precio is None:
                    continue
                
                nuevo_tipo = input("Nuevo tipo de servicio: ").strip()
                if not nuevo_tipo:
                    print("❌ El tipo de servicio no puede estar vacío.")
                    continue
                
                nuevo_km = taller.pedir_numero_con_reintentos("Nuevo kilometraje: ", "decimal")
                if nuevo_km is None:
                    continue
                
                resultado = taller.ordenes.editar_orden(orden_id, nueva_descripcion, nuevo_precio, nuevo_tipo, nuevo_km)
                print(resultado)

            # Opción 11: Ver Reportes Avanzados
            elif opcion == "11":
                print("\n📊 REPORTES AVANZADOS")
                print("  1. Reporte Semanal")
                print("  2. Reporte Mensual")
                print("  3. Reporte Anual")
                print("  4. Reporte Histórico por Año")
                print("  5. Proyección de Crecimiento")
                print("  6. Predicción de Alta Demanda")
                
                sub_opcion = input("\nSelecciona tipo de reporte: ").strip()
                
                if sub_opcion == "1":
                    reporte = taller.reportes.reporte_periodo('semana')
                    mostrar_reporte(reporte, taller)
                elif sub_opcion == "2":
                    reporte = taller.reportes.reporte_periodo('mes')
                    mostrar_reporte(reporte, taller)
                elif sub_opcion == "3":
                    reporte = taller.reportes.reporte_periodo('año')
                    mostrar_reporte(reporte, taller)
                elif sub_opcion == "4":
                    año = taller.pedir_numero_con_reintentos("Año para el reporte histórico: ", "entero")
                    if año is not None:
                        reporte = taller.reportes.reporte_periodo_historico(año)
                        mostrar_reporte(reporte, taller)
                elif sub_opcion == "5":
                    proyeccion = taller.reportes.proyeccion_crecimiento()
                    if proyeccion:
                        print(f"\n📈 PROYECCIÓN DE CRECIMIENTO:")
                        print(f"   📊 Crecimiento promedio: {proyeccion['crecimiento_promedio']*100:.1f}% mensual")
                        print(f"\n   🔮 PROYECCIONES PRÓXIMOS 6 MESES:")
                        for mes, ingreso in proyeccion['proyecciones']:
                            print(f"      {mes}: Q{ingreso:.2f}")
                        
                        if input("\n¿Generar gráfica? (s/n): ").lower() == 's':
                            taller.reportes.crear_grafica_proyeccion(proyeccion, f"proyeccion_crecimiento_{datetime.now().strftime('%Y%m%d')}")
                    else:
                        print("❌ No hay suficientes datos para generar proyecciones.")
                elif sub_opcion == "6":
                    prediccion = taller.reportes.predecir_alta_demanda()
                    print(f"\n🎯 PREDICCIÓN DE ALTA DEMANDA:")
                    print(f"   📅 MESES CON MAYOR DEMANDA HISTÓRICA:")
                    for i, mes_data in enumerate(prediccion['meses_alta_demanda'], 1):
                        print(f"      {i}. {mes_data['mes']}: {mes_data['trabajos']} trabajos (Q{mes_data['precio_promedio']:.2f} promedio)")
                else:
                    print("❌ Opción de reporte no válida.")

            # Opción 12: Recordatorios Inteligentes
            elif opcion == "12":
                taller.menu_recordatorios_inteligentes()
            
            # Opción 13: Análisis Completo de Servicios
            elif opcion == "13":
                taller.analizar_todos_los_servicios()
            
            # Opción 14: Reporte Proactivo para Clientes
            elif opcion == "14":
                taller.generar_reporte_proactivo()
            
            # Opción 0: Salir
            elif opcion == "0":
                print("\n👋 ¡Gracias por usar el Sistema de Gestión del Taller SEYMO!")
                print("¡Hasta pronto! 🚗💨")
                break
            else:
                print("❌ Opción no válida. Por favor, selecciona una opción del menú.")
                
        except KeyboardInterrupt:
            print("\n\n❌ Operación cancelada por el usuario.")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

# ============================================================================
# PUNTO DE ENTRADA DEL PROGRAMA
# ============================================================================
if __name__ == "__main__":
    menu_principal()