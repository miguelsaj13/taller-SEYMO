import sqlite3
import os
from datetime import datetime, timedelta
import pandas as pd
from collections import Counter

class TallerSEYMO:
    def __init__(self):
        if not os.path.exists('database'):
            os.makedirs('database')
            print("✅ Carpeta 'database' creada")
        
        self.conn = sqlite3.connect('database/taller.db', check_same_thread=False)
        self.crear_tablas()
    
    def crear_tablas(self):
        cursor = self.conn.cursor()
        
        # Tabla clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT UNIQUE,
                fecha_registro DATE DEFAULT CURRENT_DATE
            )
        ''')
        
        # Tabla vehículos
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
        
        # TABLA ORDENES MEJORADA
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
        
        self.conn.commit()
        print("✅ Tablas creadas/verificadas correctamente")

    # ========== FUNCIONES DE VALIDACIÓN ==========
    
    def validar_numero(self, valor, tipo="entero"):
        """Valida que el valor sea un número válido"""
        try:
            if tipo == "entero":
                return int(valor)
            elif tipo == "decimal":
                return float(valor)
            else:
                return valor
        except ValueError:
            return None

    def validar_telefono(self, telefono):
        """Valida que el teléfono contenga solo números y tenga longitud razonable"""
        if telefono is None or telefono.strip() == "":
            return None
        
        # Remover espacios, guiones, paréntesis
        telefono_limpio = ''.join(filter(str.isdigit, telefono))
        
        if len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
            return None
        
        return telefono_limpio

    def pedir_numero(self, mensaje, tipo="entero", intentos=3):
        """Pide un número al usuario con reintentos"""
        for intento in range(intentos):
            try:
                valor = input(mensaje)
                if tipo == "entero":
                    return int(valor)
                elif tipo == "decimal":
                    return float(valor)
            except ValueError:
                intentos_restantes = intentos - intento - 1
                if intentos_restantes > 0:
                    print(f"❌ Error: Debes ingresar un número {'entero' if tipo == 'entero' else 'decimal'}. Te quedan {intentos_restantes} intentos.")
                else:
                    print("❌ Has agotado todos los intentos. Volviendo al menú principal.")
                    return None
        return None

    def pedir_telefono(self, mensaje, obligatorio=False):
        """Pide un teléfono con validación y verificación de duplicados"""
        while True:
            telefono = input(mensaje)
            
            if not obligatorio and telefono.strip() == "":
                return None
            
            if obligatorio and telefono.strip() == "":
                print("❌ El teléfono es obligatorio para esta operación.")
                continue
            
            telefono_validado = self.validar_telefono(telefono)
            if not telefono_validado:
                print("❌ Error: El teléfono debe contener solo números (7-15 dígitos). Ejemplo: 1234567890")
                continue
            
            # Verificar si el teléfono ya existe
            if self.telefono_existe(telefono_validado):
                print("❌ Error: Este número de teléfono ya está registrado en el sistema.")
                continue
            
            return telefono_validado

    def telefono_existe(self, telefono):
        """Verifica si un teléfono ya existe en clientes o empleados"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM clientes WHERE telefono = ?', (telefono,))
        if cursor.fetchone():
            return True
        
        cursor.execute('SELECT id FROM empleados WHERE telefono = ?', (telefono,))
        return cursor.fetchone() is not None

    def placa_existe(self, placa):
        """Verifica si una placa ya existe"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM vehiculos WHERE placa = ?', (placa,))
        return cursor.fetchone() is not None

    # ========== FUNCIONES DE VALIDACIÓN DE EXISTENCIA ==========
    
    def cliente_existe(self, cliente_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM clientes WHERE id = ?', (cliente_id,))
        return cursor.fetchone() is not None
    
    def empleado_existe(self, empleado_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM empleados WHERE id = ?', (empleado_id,))
        return cursor.fetchone() is not None
    
    def vehiculo_existe(self, vehiculo_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM vehiculos WHERE id = ?', (vehiculo_id,))
        return cursor.fetchone() is not None
    
    def orden_existe(self, orden_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM ordenes_trabajo WHERE id = ?', (orden_id,))
        return cursor.fetchone() is not None
    
    # ========== FUNCIONES DE BÚSQUEDA MEJORADAS ==========
    
    def buscar_cliente_por_nombre(self, nombre_buscar):
        """Busca clientes por nombre y muestra todos los resultados"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, nombre, telefono FROM clientes 
            WHERE nombre LIKE ? 
            ORDER BY nombre
        ''', (f'%{nombre_buscar}%',))
        return cursor.fetchall()
    
    def seleccionar_cliente_interactivo(self):
        """Permite al usuario buscar y seleccionar un cliente interactivamente"""
        while True:
            nombre_buscar = input("\n🔍 Nombre del cliente a buscar (Enter para cancelar): ")
            if nombre_buscar.strip() == "":
                return None
            
            clientes = self.buscar_cliente_por_nombre(nombre_buscar)
            
            if not clientes:
                print("❌ No se encontraron clientes con ese nombre.")
                continue
            
            print(f"\n✅ Se encontraron {len(clientes)} cliente(s):")
            for i, cliente in enumerate(clientes, 1):
                print(f"   {i}. ID: {cliente[0]} - {cliente[1]} - Tel: {cliente[2] or 'No tiene'}")
            
            try:
                seleccion = input(f"\nSelecciona un cliente (1-{len(clientes)}) o 0 para buscar de nuevo: ")
                if seleccion == "0":
                    continue
                
                idx = int(seleccion) - 1
                if 0 <= idx < len(clientes):
                    return clientes[idx][0]  # Retorna el ID del cliente seleccionado
                else:
                    print("❌ Selección inválida.")
            except ValueError:
                print("❌ Por favor ingresa un número válido.")
    
    def seleccionar_vehiculo_interactivo(self, cliente_id):
        """Permite seleccionar un vehículo de un cliente"""
        vehiculos = self.obtener_vehiculos_cliente(cliente_id)
        
        if not vehiculos:
            print("❌ Este cliente no tiene vehículos registrados.")
            return None
        
        print(f"\n🚗 Vehículos del cliente:")
        for i, vehiculo in enumerate(vehiculos, 1):
            print(f"   {i}. {vehiculo[1]} {vehiculo[2]} {vehiculo[3]} - Placa: {vehiculo[4]}")
        
        try:
            seleccion = input(f"\nSelecciona un vehículo (1-{len(vehiculos)}): ")
            idx = int(seleccion) - 1
            if 0 <= idx < len(vehiculos):
                return vehiculos[idx][0]  # Retorna el ID del vehículo
            else:
                print("❌ Selección inválida.")
                return None
        except ValueError:
            print("❌ Por favor ingresa un número válido.")
            return None

    # ========== NUEVAS FUNCIONES ==========
    
    def agregar_varios_vehiculos(self, cliente_id, cantidad):
        """Agrega múltiples vehículos a un cliente"""
        vehiculos_agregados = 0
        
        for i in range(cantidad):
            print(f"\n--- Vehículo {i + 1} de {cantidad} ---")
            marca = input("Marca del vehículo: ")
            modelo = input("Modelo: ")
            
            año = self.pedir_numero("Año: ", "entero")
            if año is None:
                print("❌ Año inválido. Saltando este vehículo.")
                continue
                
            placa = input("Placa: ")
            if self.placa_existe(placa):
                print("❌ Error: Ya existe un vehículo con esa placa. Saltando este vehículo.")
                continue
                
            color = input("Color (opcional): ") or None
            
            # Preguntar por próximo mantenimiento
            print("Próximo mantenimiento (opcional):")
            print("  Formato: YYYY-MM-DD o días desde hoy (ej: 30 para 30 días)")
            mantenimiento_input = input("  Fecha o días: ")
            
            proximo_mantenimiento = None
            if mantenimiento_input:
                try:
                    # Si es un número, calcular días desde hoy
                    if mantenimiento_input.isdigit():
                        dias = int(mantenimiento_input)
                        proximo_mantenimiento = (datetime.now() + timedelta(days=dias)).date()
                    else:
                        # Si es una fecha, validar formato
                        proximo_mantenimiento = datetime.strptime(mantenimiento_input, '%Y-%m-%d').date()
                except ValueError:
                    print("  ❌ Formato inválido. No se asignó mantenimiento.")
            
            resultado = self.agregar_vehiculo(cliente_id, marca, modelo, año, placa, color)
            if "✅" in resultado:
                vehiculos_agregados += 1
                print(resultado)
                
                # Actualizar el mantenimiento si se especificó
                if proximo_mantenimiento:
                    cursor = self.conn.cursor()
                    cursor.execute('SELECT id FROM vehiculos WHERE placa = ?', (placa,))
                    vehiculo_id = cursor.fetchone()[0]
                    cursor.execute('UPDATE vehiculos SET proximo_mantenimiento = ? WHERE id = ?', 
                                 (proximo_mantenimiento, vehiculo_id))
                    self.conn.commit()
                    print(f"  📅 Próximo mantenimiento: {proximo_mantenimiento}")
            else:
                print(resultado)
        
        return f"✅ Se agregaron {vehiculos_agregados} de {cantidad} vehículos"

    def obtener_recordatorios_mantenimiento(self, dias=30):
        """Obtiene vehículos con mantenimiento próximo en los próximos X días"""
        cursor = self.conn.cursor()
        fecha_limite = datetime.now() + timedelta(days=dias)
        
        cursor.execute('''
            SELECT v.placa, v.marca, v.modelo, v.proximo_mantenimiento, c.nombre, c.telefono
            FROM vehiculos v
            JOIN clientes c ON v.cliente_id = c.id
            WHERE v.proximo_mantenimiento IS NOT NULL 
            AND v.proximo_mantenimiento <= ?
            ORDER BY v.proximo_mantenimiento ASC
        ''', (fecha_limite.date(),))
        
        return cursor.fetchall()

    def reporte_periodo_historico(self, año, periodo='año'):
        """Genera reportes para años pasados"""
        cursor = self.conn.cursor()
        
        if periodo == 'año':
            fecha_inicio = datetime(año, 1, 1)
            fecha_fin = datetime(año, 12, 31)
        elif periodo == 'mes':
            fecha_inicio = datetime(año, datetime.now().month, 1)
            fecha_fin = datetime(año, datetime.now().month, 1) + timedelta(days=32)
            fecha_fin = fecha_fin.replace(day=1) - timedelta(days=1)
        else:  # 'semana' - para años pasados es menos útil
            fecha_inicio = datetime(año, 1, 1)
            fecha_fin = datetime(año, 12, 31)
        
        # Datos básicos
        cursor.execute('''
            SELECT SUM(precio_final), SUM(horas_trabajadas), COUNT(*)
            FROM ordenes_trabajo 
            WHERE fecha_fin BETWEEN ? AND ?
        ''', (fecha_inicio.date(), fecha_fin.date()))
        
        ganancias, horas, trabajos = cursor.fetchone()
        
        # Servicios más solicitados
        cursor.execute('''
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

    def proyeccion_crecimiento(self):
        """Genera proyecciones de crecimiento basadas en datos históricos"""
        cursor = self.conn.cursor()
        
        # Obtener datos de los últimos 12 meses
        fecha_inicio = datetime.now().replace(day=1) - timedelta(days=365)
        
        cursor.execute('''
            SELECT strftime('%Y-%m', fecha_fin) as mes, 
                   SUM(precio_final) as ingresos,
                   COUNT(*) as trabajos
            FROM ordenes_trabajo 
            WHERE fecha_fin >= ?
            GROUP BY mes
            ORDER BY mes
        ''', (fecha_inicio.date(),))
        
        datos_mensuales = cursor.fetchall()
        
        if len(datos_mensuales) < 3:
            return None  # No hay suficientes datos
        
        # Calcular crecimiento promedio
        ingresos = [d[1] for d in datos_mensuales]
        crecimiento_promedio = sum((ingresos[i] - ingresos[i-1]) / ingresos[i-1] 
                                 for i in range(1, len(ingresos))) / (len(ingresos) - 1)
        
        # Proyección para los próximos 6 meses
        ultimo_ingreso = ingresos[-1]
        proyecciones = []
        
        for i in range(1, 7):
            mes_proyectado = (datetime.now() + timedelta(days=30*i)).strftime('%Y-%m')
            ingreso_proyectado = ultimo_ingreso * (1 + crecimiento_promedio) ** i
            proyecciones.append((mes_proyectado, ingreso_proyectado))
        
        return {
            'crecimiento_promedio': crecimiento_promedio,
            'proyecciones': proyecciones,
            'datos_historicos': datos_mensuales
        }
    
    # ========== FUNCIONES PRINCIPALES ==========
    
    # 1. AÑADIR CLIENTE NUEVO
    def agregar_cliente(self, nombre, telefono=None):
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO clientes (nombre, telefono) VALUES (?, ?)', 
                          (nombre, telefono))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    # AÑADIR VEHÍCULO A CLIENTE
    def agregar_vehiculo(self, cliente_id, marca, modelo, año, placa, color=None):
        if not self.cliente_existe(cliente_id):
            return "❌ Error: El cliente no existe"
        
        if self.placa_existe(placa):
            return "❌ Error: Ya existe un vehículo con esa placa"
        
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO vehiculos (cliente_id, marca, modelo, año, placa, color)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (cliente_id, marca, modelo, año, placa, color))
            self.conn.commit()
            return f"✅ Vehículo {marca} {modelo} agregado (ID: {cursor.lastrowid})"
        except sqlite3.IntegrityError:
            return "❌ Error: Ya existe un vehículo con esa placa"
    
    # 2. AÑADIR EMPLEADO NUEVO
    def agregar_empleado(self, nombre, telefono):
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO empleados (nombre, telefono) VALUES (?, ?)', 
                          (nombre, telefono))
            self.conn.commit()
            return f"✅ Empleado '{nombre}' agregado (ID: {cursor.lastrowid})"
        except sqlite3.IntegrityError:
            return "❌ Error: Ya existe un empleado con ese teléfono"
    
    # EDITAR EMPLEADO INTERACTIVO
    def editar_empleado_interactivo(self, empleado_id):
        if not self.empleado_existe(empleado_id):
            return "❌ Error: El empleado no existe"
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT nombre, telefono FROM empleados WHERE id = ?', (empleado_id,))
        empleado_actual = cursor.fetchone()
        
        print(f"\n📝 Editando empleado: {empleado_actual[0]}")
        print("¿Qué deseas editar?")
        print("1. Nombre")
        print("2. Teléfono")
        print("3. Ambos")
        print("4. Cancelar")
        
        opcion = input("\nSelecciona una opción: ")
        
        nuevo_nombre = empleado_actual[0]
        nuevo_telefono = empleado_actual[1]
        
        if opcion in ["1", "3"]:
            nuevo_nombre = input("Nuevo nombre: ")
        
        if opcion in ["2", "3"]:
            nuevo_telefono = self.pedir_telefono("Nuevo teléfono: ", obligatorio=True)
            if nuevo_telefono is None:
                return "❌ Edición cancelada"
        
        if opcion == "4":
            return "ℹ️ Edición cancelada"
        
        try:
            cursor.execute('''
                UPDATE empleados SET nombre = ?, telefono = ? WHERE id = ?
            ''', (nuevo_nombre, nuevo_telefono, empleado_id))
            self.conn.commit()
            return f"✅ Empleado ID {empleado_id} actualizado"
        except sqlite3.IntegrityError:
            return "❌ Error: Ya existe un empleado con ese teléfono"
    
    # 3. AÑADIR ORDEN NUEVA (MEJORADA)
    def agregar_orden(self, numero_orden, vehiculo_id, empleado_id, descripcion_trabajo, 
                     tipo_servicio, horas_trabajadas, costo_repuestos, costo_mano_obra, 
                     kilometraje, unidad_kilometraje='km', fecha_fin=None):
        
        # Validaciones
        if not self.vehiculo_existe(vehiculo_id):
            return "❌ Error: El vehículo no existe"
        if not self.empleado_existe(empleado_id):
            return "❌ Error: El empleado no existe"
        if self.orden_existe(numero_orden):
            return "❌ Error: Ya existe una orden con ese número"
        
        cursor = self.conn.cursor()
        precio_final = costo_repuestos + costo_mano_obra
        
        if fecha_fin is None:
            fecha_fin = datetime.now().date()
        
        cursor.execute('''
            INSERT INTO ordenes_trabajo 
            (id, vehiculo_id, empleado_id, descripcion_trabajo, tipo_servicio,
             horas_trabajadas, costo_repuestos, costo_mano_obra, precio_final,
             kilometraje, unidad_kilometraje, fecha_fin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (numero_orden, vehiculo_id, empleado_id, descripcion_trabajo, tipo_servicio,
              horas_trabajadas, costo_repuestos, costo_mano_obra, precio_final,
              kilometraje, unidad_kilometraje, fecha_fin))
        
        self.conn.commit()
        return f"✅ Orden #{numero_orden} agregada - Total: ${precio_final}"
    
    # EDITAR CLIENTE INTERACTIVO
    def editar_cliente_interactivo(self, cliente_id):
        if not self.cliente_existe(cliente_id):
            return "❌ Error: El cliente no existe"
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT nombre, telefono FROM clientes WHERE id = ?', (cliente_id,))
        cliente_actual = cursor.fetchone()
        
        print(f"\n📝 Editando cliente: {cliente_actual[0]}")
        print("¿Qué deseas editar?")
        print("1. Nombre")
        print("2. Teléfono")
        print("3. Ambos")
        print("4. Cancelar")
        
        opcion = input("\nSelecciona una opción: ")
        
        nuevo_nombre = cliente_actual[0]
        nuevo_telefono = cliente_actual[1]
        
        if opcion in ["1", "3"]:
            nuevo_nombre = input("Nuevo nombre: ")
        
        if opcion in ["2", "3"]:
            nuevo_telefono = self.pedir_telefono("Nuevo teléfono (opcional, Enter para mantener actual): ")
        
        if opcion == "4":
            return "ℹ️ Edición cancelada"
        
        try:
            cursor.execute('''
                UPDATE clientes SET nombre = ?, telefono = ? WHERE id = ?
            ''', (nuevo_nombre, nuevo_telefono, cliente_id))
            self.conn.commit()
            return f"✅ Cliente ID {cliente_id} actualizado"
        except sqlite3.IntegrityError:
            return "❌ Error: Ya existe un cliente con ese teléfono"
    
    # EDITAR ORDEN INTERACTIVO
    def editar_orden_interactivo(self, orden_id):
        if not self.orden_existe(orden_id):
            return "❌ Error: La orden no existe"
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT descripcion_trabajo, precio_final, tipo_servicio, kilometraje 
            FROM ordenes_trabajo WHERE id = ?
        ''', (orden_id,))
        orden_actual = cursor.fetchone()
        
        print(f"\n📝 Editando orden #{orden_id}")
        print("¿Qué deseas editar?")
        print("1. Descripción del trabajo")
        print("2. Precio final")
        print("3. Tipo de servicio")
        print("4. Kilometraje")
        print("5. Cancelar")
        
        opcion = input("\nSelecciona una opción: ")
        
        nueva_descripcion = orden_actual[0]
        nuevo_precio = orden_actual[1]
        nuevo_tipo = orden_actual[2]
        nuevo_km = orden_actual[3]
        
        if opcion == "1":
            nueva_descripcion = input("Nueva descripción: ")
        elif opcion == "2":
            nuevo_precio = self.pedir_numero("Nuevo precio: ", "decimal")
            if nuevo_precio is None:
                return "❌ Edición cancelada"
        elif opcion == "3":
            nuevo_tipo = input("Nuevo tipo de servicio: ")
        elif opcion == "4":
            nuevo_km = self.pedir_numero("Nuevo kilometraje: ", "decimal")
            if nuevo_km is None:
                return "❌ Edición cancelada"
        elif opcion == "5":
            return "ℹ️ Edición cancelada"
        else:
            return "❌ Opción inválida"
        
        cursor.execute('''
            UPDATE ordenes_trabajo 
            SET descripcion_trabajo = ?, precio_final = ?, tipo_servicio = ?, kilometraje = ?
            WHERE id = ?
        ''', (nueva_descripcion, nuevo_precio, nuevo_tipo, nuevo_km, orden_id))
        self.conn.commit()
        return f"✅ Orden #{orden_id} actualizada"
    
    # OBTENER VEHÍCULOS DE CLIENTE
    def obtener_vehiculos_cliente(self, cliente_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, marca, modelo, año, placa, color 
            FROM vehiculos 
            WHERE cliente_id = ?
        ''', (cliente_id,))
        return cursor.fetchall()
    
    # DETALLES DEL CLIENTE MEJORADO
    def detalles_cliente(self, cliente_id):
        if not self.cliente_existe(cliente_id):
            return None
        
        cursor = self.conn.cursor()
        
        # Información del cliente
        cursor.execute('SELECT nombre, telefono, fecha_registro FROM clientes WHERE id = ?', (cliente_id,))
        cliente_info = cursor.fetchone()
        
        # Vehículos del cliente
        vehiculos = self.obtener_vehiculos_cliente(cliente_id)
        
        return {
            'cliente': cliente_info,
            'vehiculos': vehiculos
        }
    
    # DETALLES POR VEHÍCULO
    def detalles_vehiculo(self, vehiculo_id):
        if not self.vehiculo_existe(vehiculo_id):
            return None
        
        cursor = self.conn.cursor()
        
        # Información del vehículo y cliente
        cursor.execute('''
            SELECT v.marca, v.modelo, v.año, v.placa, v.color, c.nombre, c.telefono
            FROM vehiculos v
            JOIN clientes c ON v.cliente_id = c.id
            WHERE v.id = ?
        ''', (vehiculo_id,))
        vehiculo_info = cursor.fetchone()
        
        # Historial de órdenes del vehículo
        cursor.execute('''
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
    
    # REPORTES MEJORADOS
    def reporte_periodo(self, periodo='semana'):
        cursor = self.conn.cursor()
        
        if periodo == 'semana':
            fecha_inicio = datetime.now() - timedelta(days=datetime.now().weekday())
        elif periodo == 'mes':
            fecha_inicio = datetime.now().replace(day=1)
        else:  # 'año'
            fecha_inicio = datetime.now().replace(month=1, day=1)
        
        # Datos básicos
        cursor.execute('''
            SELECT SUM(precio_final), SUM(horas_trabajadas), COUNT(*)
            FROM ordenes_trabajo 
            WHERE fecha_fin >= ?
        ''', (fecha_inicio.date(),))
        
        ganancias, horas, trabajos = cursor.fetchone()
        
        # Servicios más solicitados
        cursor.execute('''
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
    
    # FUNCIONES PARA LISTAR
    def listar_empleados(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, nombre FROM empleados ORDER BY nombre')
        return cursor.fetchall()

# INTERFAZ MEJORADA CON TODAS LAS NUEVAS FUNCIONALIDADES
def menu_principal():
    taller = TallerSEYMO()
    
    while True:
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
        
        print("\n🔔 MANTENIMIENTO")
        print("  12. Recordatorios de Mantenimiento")
        
        print("\n  0. Salir del Sistema")
        print("="*50)
        
        opcion = input("\nSelecciona una opción: ")
        
        # 📝 CREAR Y REGISTRAR
        if opcion == "1":
            print("\n📝 REGISTRAR NUEVO CLIENTE Y VEHÍCULOS")
            nombre = input("Nombre del cliente: ")
            telefono = taller.pedir_telefono("Teléfono (opcional, Enter para omitir): ")
            
            cliente_id = taller.agregar_cliente(nombre, telefono)
            if cliente_id is None:
                print("❌ Error: Ya existe un cliente con ese teléfono.")
                continue
                
            print(f"✅ Cliente '{nombre}' agregado (ID: {cliente_id})")
            
            # Preguntar cuántos vehículos agregar
            cantidad_vehiculos = taller.pedir_numero("\n¿Cuántos vehículos deseas agregar? ", "entero")
            if cantidad_vehiculos is None or cantidad_vehiculos <= 0:
                print("❌ Cantidad inválida. Se agregará 1 vehículo por defecto.")
                cantidad_vehiculos = 1
            
            resultado = taller.agregar_varios_vehiculos(cliente_id, cantidad_vehiculos)
            print(f"\n{resultado}")
            
        elif opcion == "2":
            print("\n📝 REGISTRAR NUEVO EMPLEADO")
            nombre = input("Nombre del empleado: ")
            telefono = taller.pedir_telefono("Teléfono (obligatorio): ", obligatorio=True)
            if telefono is None:
                continue
                
            resultado = taller.agregar_empleado(nombre, telefono)
            print(resultado)
            
        elif opcion == "3":
            print("\n📝 CREAR NUEVA ORDEN DE TRABAJO")
            
            # Buscar cliente interactivamente
            cliente_id = taller.seleccionar_cliente_interactivo()
            if cliente_id is None:
                continue
                
            # Seleccionar vehículo
            vehiculo_id = taller.seleccionar_vehiculo_interactivo(cliente_id)
            if vehiculo_id is None:
                continue
            
            print("\n--- Lista de Empleados ---")
            empleados = taller.listar_empleados()
            for empleado in empleados:
                print(f"  ID: {empleado[0]} - {empleado[1]}")
            
            # Validar todos los números
            numero_orden = taller.pedir_numero("Número de orden: ", "entero")
            if numero_orden is None:
                continue
                
            empleado_id = taller.pedir_numero("ID del empleado: ", "entero")
            if empleado_id is None:
                continue
                
            descripcion = input("Descripción del trabajo: ")
            tipo_servicio = input("Tipo de servicio (ej: frenos, aceite, motor): ")
            
            horas = taller.pedir_numero("Horas trabajadas: ", "decimal")
            if horas is None:
                continue
                
            repuestos = taller.pedir_numero("Costo repuestos: $", "decimal")
            if repuestos is None:
                continue
                
            mano_obra = taller.pedir_numero("Costo mano de obra: $", "decimal")
            if mano_obra is None:
                continue
                
            kilometraje = taller.pedir_numero("Kilometraje: ", "decimal")
            if kilometraje is None:
                continue
                
            unidad = input("Unidad (km/millas) [km]: ") or "km"
            
            fecha_fin_input = input("Fecha de finalización (YYYY-MM-DD) o Enter para hoy: ")
            fecha_fin = fecha_fin_input if fecha_fin_input else None
            
            resultado = taller.agregar_orden(numero_orden, vehiculo_id, empleado_id, descripcion, 
                                           tipo_servicio, horas, repuestos, mano_obra, 
                                           kilometraje, unidad, fecha_fin)
            print(resultado)
                
        elif opcion == "4":
            print("\n📝 AÑADIR VEHÍCULO A CLIENTE EXISTENTE")
            
            cliente_id = taller.seleccionar_cliente_interactivo()
            if cliente_id is None:
                continue
            
            marca = input("Marca del vehículo: ")
            modelo = input("Modelo: ")
            
            año = taller.pedir_numero("Año: ", "entero")
            if año is None:
                continue
                
            placa = input("Placa: ")
            if taller.placa_existe(placa):
                print("❌ Error: Ya existe un vehículo con esa placa.")
                continue
                
            color = input("Color (opcional): ") or None
            
            resultado = taller.agregar_vehiculo(cliente_id, marca, modelo, año, placa, color)
            print(resultado)
        
        # 🔍 BUSCAR Y CONSULTAR
        elif opcion == "5":
            print("\n🔍 BUSCAR Y VER CLIENTE")
            cliente_id = taller.seleccionar_cliente_interactivo()
            if cliente_id is None:
                continue
                
            detalles = taller.detalles_cliente(cliente_id)
            
            if detalles:
                cliente_info = detalles['cliente']
                vehiculos = detalles['vehiculos']
                
                print(f"\n📋 DETALLES DEL CLIENTE:")
                print(f"  👤 Nombre: {cliente_info[0]}")
                print(f"  📞 Teléfono: {cliente_info[1] or 'No tiene'}")
                print(f"  📅 Fecha registro: {cliente_info[2]}")
                
                if vehiculos:
                    print(f"\n🚗 VEHÍCULOS ({len(vehiculos)}):")
                    for vehiculo in vehiculos:
                        print(f"  🆔 ID: {vehiculo[0]}")
                        print(f"  🚙 {vehiculo[1]} {vehiculo[2]} {vehiculo[3]}")
                        print(f"  🪪 Placa: {vehiculo[4]}")
                        print("  " + "-" * 25)
                else:
                    print("\n  🚗 Este cliente no tiene vehículos registrados")
            else:
                print("❌ Cliente no encontrado")
                
        elif opcion == "6":
            print("\n🔍 HISTORIAL POR VEHÍCULO")
            
            # Primero buscar el cliente
            cliente_id = taller.seleccionar_cliente_interactivo()
            if cliente_id is None:
                continue
                
            # Luego seleccionar el vehículo
            vehiculo_id = taller.seleccionar_vehiculo_interactivo(cliente_id)
            if vehiculo_id is None:
                continue
                
            detalles = taller.detalles_vehiculo(vehiculo_id)
            
            if detalles:
                vehiculo_info = detalles['vehiculo']
                ordenes = detalles['ordenes']
                
                print(f"\n📋 INFORMACIÓN DEL VEHÍCULO:")
                print(f"  🚙 Vehículo: {vehiculo_info[0]} {vehiculo_info[1]} {vehiculo_info[2]}")
                print(f"  🪪 Placa: {vehiculo_info[3]}")
                print(f"  🎨 Color: {vehiculo_info[4] or 'No especificado'}")
                print(f"  👤 Cliente: {vehiculo_info[5]}")
                print(f"  📞 Tel: {vehiculo_info[6] or 'No tiene'}")
                
                if ordenes:
                    print(f"\n📊 HISTORIAL DE TRABAJOS ({len(ordenes)}):")
                    for orden in ordenes:
                        print(f"  🔧 Orden #{orden[0]}")
                        print(f"     📝 {orden[4]}: {orden[3]}")
                        print(f"     📅 {orden[1]} a {orden[2]}")
                        print(f"     💰 ${orden[5]} - 🛣️ {orden[6]} {orden[7]}")
                        print(f"     👷 Empleado: {orden[8]}")
                        print("     " + "-" * 40)
                else:
                    print("\n  📝 Este vehículo no tiene trabajos registrados")
            else:
                print("❌ Vehículo no encontrado")
                
        elif opcion == "7":
            print("\n🔍 BUSCAR ORDEN POR ID")
            orden_id = taller.pedir_numero("ID de la orden: ", "entero")
            if orden_id is None:
                continue
                
            if taller.orden_existe(orden_id):
                print(f"✅ La orden #{orden_id} existe en el sistema")
            else:
                print(f"❌ La orden #{orden_id} no existe")
        
        # ✏️ EDITAR Y ACTUALIZAR
        elif opcion == "8":
            print("\n✏️ EDITAR CLIENTE")
            cliente_id = taller.seleccionar_cliente_interactivo()
            if cliente_id is None:
                continue
                
            resultado = taller.editar_cliente_interactivo(cliente_id)
            print(resultado)
                
        elif opcion == "9":
            print("\n✏️ EDITAR EMPLEADO")
            empleado_id = taller.pedir_numero("ID del empleado a editar: ", "entero")
            if empleado_id is None:
                continue
                
            resultado = taller.editar_empleado_interactivo(empleado_id)
            print(resultado)
                
        elif opcion == "10":
            print("\n✏️ EDITAR ORDEN")
            orden_id = taller.pedir_numero("ID de la orden a editar: ", "entero")
            if orden_id is None:
                continue
                
            resultado = taller.editar_orden_interactivo(orden_id)
            print(resultado)
        
        # 📊 REPORTES Y ANÁLISIS
        elif opcion == "11":
            print("\n📊 REPORTES Y ANÁLISIS")
            print("  1. 📈 Reporte Semanal")
            print("  2. 📅 Reporte Mensual") 
            print("  3. 🗓️ Reporte Anual")
            print("  4. 📊 Reportes de Años Pasados")
            print("  5. 📈 Proyección de Crecimiento")
            print("  0. ↩️ Volver al menú principal")
            
            sub_opcion = input("\nSelecciona reporte: ")
            
            if sub_opcion == "0":
                continue
            elif sub_opcion in ["1", "2", "3"]:
                periodo = "semana" if sub_opcion == "1" else "mes" if sub_opcion == "2" else "año"
                reporte = taller.reporte_periodo(periodo)
                
                print(f"\n📈 REPORTE {periodo.upper()} ({reporte['fecha_inicio']} a hoy)")
                print(f"  💰 Ganancias: ${reporte['ganancias']:,.2f}")
                print(f"  ⏰ Horas trabajadas: {reporte['horas_trabajadas']} hrs")
                print(f"  🔧 Trabajos completados: {reporte['trabajos_completados']}")
                
                if reporte['servicios_populares']:
                    print(f"\n  🏆 SERVICIOS MÁS SOLICITADOS:")
                    for servicio in reporte['servicios_populares']:
                        print(f"    • {servicio[0]}: {servicio[1]} trabajos - ${servicio[2]:,.2f}")
                        
            elif sub_opcion == "4":
                print("\n📊 REPORTES DE AÑOS PASADOS")
                año = taller.pedir_numero("¿Qué año deseas consultar? (ej: 2023): ", "entero")
                if año is None:
                    continue
                    
                reporte = taller.reporte_periodo_historico(año)
                
                print(f"\n📈 REPORTE ANUAL {año}")
                print(f"  💰 Ganancias: ${reporte['ganancias']:,.2f}")
                print(f"  ⏰ Horas trabajadas: {reporte['horas_trabajadas']} hrs")
                print(f"  🔧 Trabajos completados: {reporte['trabajos_completados']}")
                
                if reporte['servicios_populares']:
                    print(f"\n  🏆 SERVICIOS MÁS SOLICITADOS:")
                    for servicio in reporte['servicios_populares']:
                        print(f"    • {servicio[0]}: {servicio[1]} trabajos - ${servicio[2]:,.2f}")
                        
            elif sub_opcion == "5":
                print("\n📈 PROYECCIÓN DE CRECIMIENTO")
                proyeccion = taller.proyeccion_crecimiento()
                
                if proyeccion is None:
                    print("❌ No hay suficientes datos históricos para generar proyecciones.")
                    print("   Se necesitan al menos 3 meses de datos.")
                    continue
                
                print(f"\n📊 ANÁLISIS DE CRECIMIENTO")
                print(f"  📈 Crecimiento promedio mensual: {proyeccion['crecimiento_promedio']*100:.1f}%")
                
                print(f"\n🎯 PROYECCIÓN PRÓXIMOS 6 MESES:")
                for mes, ingreso in proyeccion['proyecciones']:
                    print(f"  • {mes}: ${ingreso:,.2f}")
                
                print(f"\n💡 RECOMENDACIÓN:")
                if proyeccion['crecimiento_promedio'] > 0.1:
                    print("  ¡Excelente crecimiento! Considera expandir capacidad.")
                elif proyeccion['crecimiento_promedio'] > 0.05:
                    print("  Crecimiento saludable. Mantén la estrategia actual.")
                else:
                    print("  Crecimiento lento. Considera promociones o nuevos servicios.")
            else:
                print("❌ Opción no válida")
        
        # 🔔 MANTENIMIENTO
        elif opcion == "12":
            print("\n🔔 RECORDATORIOS DE MANTENIMIENTO")
            print("  1. Próximos 30 días")
            print("  2. Próximos 60 días")
            print("  3. Personalizado")
            print("  0. ↩️ Volver")
            
            sub_opcion = input("\nSelecciona período: ")
            
            if sub_opcion == "0":
                continue
            elif sub_opcion == "1":
                dias = 30
            elif sub_opcion == "2":
                dias = 60
            elif sub_opcion == "3":
                dias = taller.pedir_numero("¿Cuántos días? ", "entero")
                if dias is None:
                    continue
            else:
                print("❌ Opción inválida")
                continue
            
            recordatorios = taller.obtener_recordatorios_mantenimiento(dias)
            
            if recordatorios:
                print(f"\n🔔 VEHÍCULOS CON MANTENIMIENTO PRÓXIMO ({dias} días):")
                for vehiculo in recordatorios:
                    dias_restantes = (vehiculo[3] - datetime.now().date()).days
                    print(f"  🚗 {vehiculo[1]} {vehiculo[2]} - Placa: {vehiculo[0]}")
                    print(f"     👤 Cliente: {vehiculo[4]} - Tel: {vehiculo[5] or 'No tiene'}")
                    print(f"     📅 {vehiculo[3]} ({dias_restantes} días restantes)")
                    print("     " + "-" * 40)
            else:
                print(f"\n✅ No hay vehículos con mantenimiento programado en los próximos {dias} días.")
                
        elif opcion == "0":
            print("\n👋 ¡Gracias por usar el Sistema de Gestión del Taller SEYMO!")
            print("¡Hasta pronto! 🚗💨")
            break
        else:
            print("❌ Opción no válida. Por favor, selecciona una opción del menú.")

if __name__ == "__main__":
    menu_principal()