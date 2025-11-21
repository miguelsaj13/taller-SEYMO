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
                telefono TEXT,
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
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT
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
    
    # FUNCIONES DE VALIDACIÓN
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
    
    # 1. AÑADIR CLIENTE NUEVO
    def agregar_cliente(self, nombre, telefono=None):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO clientes (nombre, telefono) VALUES (?, ?)', 
                      (nombre, telefono))
        self.conn.commit()
        return cursor.lastrowid
    
    # AÑADIR VEHÍCULO A CLIENTE
    def agregar_vehiculo(self, cliente_id, marca, modelo, año, placa, color=None):
        if not self.cliente_existe(cliente_id):
            return "❌ Error: El cliente no existe"
        
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
    def agregar_empleado(self, nombre, telefono=None):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO empleados (nombre, telefono) VALUES (?, ?)', 
                      (nombre, telefono))
        self.conn.commit()
        return f"✅ Empleado '{nombre}' agregado (ID: {cursor.lastrowid})"
    
    # NUEVO: EDITAR EMPLEADO
    def editar_empleado(self, empleado_id, nuevo_nombre, nuevo_telefono):
        if not self.empleado_existe(empleado_id):
            return "❌ Error: El empleado no existe"
        
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE empleados SET nombre = ?, telefono = ? WHERE id = ?
        ''', (nuevo_nombre, nuevo_telefono, empleado_id))
        self.conn.commit()
        return f"✅ Empleado ID {empleado_id} actualizado"
    
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
    
    # EDITAR CLIENTE (MEJORADO CON VALIDACIÓN)
    def editar_cliente(self, cliente_id, nuevo_nombre, nuevo_telefono):
        if not self.cliente_existe(cliente_id):
            return "❌ Error: El cliente no existe"
        
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE clientes SET nombre = ?, telefono = ? WHERE id = ?
        ''', (nuevo_nombre, nuevo_telefono, cliente_id))
        self.conn.commit()
        return f"✅ Cliente ID {cliente_id} actualizado"
    
    # EDITAR ORDEN (MEJORADO CON VALIDACIÓN)
    def editar_orden(self, orden_id, nueva_descripcion=None, nuevo_precio_final=None,
                    nuevo_tipo_servicio=None, nuevo_kilometraje=None):
        
        if not self.orden_existe(orden_id):
            return "❌ Error: La orden no existe"
        
        cursor = self.conn.cursor()
        
        updates = []
        params = []
        
        if nueva_descripcion:
            updates.append("descripcion_trabajo = ?")
            params.append(nueva_descripcion)
        
        if nuevo_precio_final is not None:
            updates.append("precio_final = ?")
            params.append(nuevo_precio_final)
        
        if nuevo_tipo_servicio:
            updates.append("tipo_servicio = ?")
            params.append(nuevo_tipo_servicio)
            
        if nuevo_kilometraje is not None:
            updates.append("kilometraje = ?")
            params.append(nuevo_kilometraje)
        
        if updates:
            query = f"UPDATE ordenes_trabajo SET {', '.join(updates)} WHERE id = ?"
            params.append(orden_id)
            cursor.execute(query, params)
            self.conn.commit()
            return f"✅ Orden #{orden_id} actualizada"
        else:
            return "ℹ️ No se especificaron cambios"
    
    # 4. BUSCAR CLIENTE POR NOMBRE
    def buscar_cliente(self, nombre_buscar):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, nombre, telefono FROM clientes 
            WHERE nombre LIKE ? 
            ORDER BY nombre
        ''', (f'%{nombre_buscar}%',))
        return cursor.fetchall()
    
    # OBTENER VEHÍCULOS DE CLIENTE
    def obtener_vehiculos_cliente(self, cliente_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, marca, modelo, año, placa, color 
            FROM vehiculos 
            WHERE cliente_id = ?
        ''', (cliente_id,))
        return cursor.fetchall()
    
    # 5. DETALLES DEL CLIENTE MEJORADO
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
    
    # 6. REPORTES MEJORADOS
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
        
        # Rentabilidad por tipo de servicio
        cursor.execute('''
            SELECT tipo_servicio, 
                   COUNT(*) as cantidad,
                   SUM(precio_final) as ingresos,
                   AVG(precio_final - (costo_repuestos + costo_mano_obra)) as margen_promedio
            FROM ordenes_trabajo 
            WHERE fecha_fin >= ?
            GROUP BY tipo_servicio
            ORDER BY margen_promedio DESC
        ''', (fecha_inicio.date(),))
        
        rentabilidad = cursor.fetchall()
        
        return {
            'ganancias': ganancias or 0,
            'horas_trabajadas': horas or 0,
            'trabajos_completados': trabajos or 0,
            'periodo': periodo,
            'fecha_inicio': fecha_inicio.date(),
            'servicios_populares': servicios_populares,
            'rentabilidad_servicios': rentabilidad
        }
    
    # PREDICCIÓN TEMPORADAS ALTAS
    def prediccion_temporadas(self):
        cursor = self.conn.cursor()
        
        # Análisis histórico por mes
        cursor.execute('''
            SELECT strftime('%m', fecha_fin) as mes, 
                   COUNT(*) as trabajos,
                   SUM(precio_final) as ingresos
            FROM ordenes_trabajo 
            GROUP BY mes
            ORDER BY ingresos DESC
        ''')
        
        analisis_mensual = cursor.fetchall()
        
        # Meses más ocupados (top 3)
        meses_altos = analisis_mensual[:3] if analisis_mensual else []
        
        return {
            'meses_altos': meses_altos,
            'analisis_completo': analisis_mensual
        }
    
    # FUNCIONES PARA LISTAR
    def listar_empleados(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, nombre FROM empleados ORDER BY nombre')
        return cursor.fetchall()

# INTERFAZ MEJORADA
def menu_principal():
    taller = TallerSEYMO()
    
    while True:
        print("\n" + "="*50)
        print("🔧 TALLER SEYMO - SISTEMA DE GESTIÓN")
        print("="*50)
        
        print("📝 CREAR Y REGISTRAR")
        print("  1. Nuevo Cliente + Vehículo")
        print("  2. Nuevo Empleado")
        print("  3. Nueva Orden de Trabajo")
        print("  4. Añadir Vehículo a Cliente Existente")
        
        print("\n🔍 BUSCAR Y CONSULTAR")
        print("  5. Buscar Cliente")
        print("  6. Ver Detalles de Cliente")
        print("  7. Ver Historial por Vehículo")
        print("  8. Buscar Orden por ID")
        
        print("\n✏️ EDITAR Y ACTUALIZAR")
        print("  9. Editar Cliente")
        print("  10. Editar Empleado")
        print("  11. Editar Orden")
        
        print("\n📊 REPORTES Y ANÁLISIS")
        print("  12. Ver Reportes Avanzados")
        
        print("\n  0. Salir del Sistema")
        print("="*50)
        
        opcion = input("\nSelecciona una opción: ")
        
        # 📝 CREAR Y REGISTRAR
        if opcion == "1":
            print("\n📝 REGISTRAR NUEVO CLIENTE Y VEHÍCULO")
            nombre = input("Nombre del cliente: ")
            telefono = input("Teléfono (opcional): ")
            cliente_id = taller.agregar_cliente(nombre, telefono or None)
            print(f"✅ Cliente '{nombre}' agregado (ID: {cliente_id})")
            
            print("\n--- Registrar primer vehículo ---")
            marca = input("Marca del vehículo: ")
            modelo = input("Modelo: ")
            año = input("Año: ")
            placa = input("Placa: ")
            color = input("Color (opcional): ")
            
            resultado = taller.agregar_vehiculo(cliente_id, marca, modelo, año, placa, color or None)
            print(resultado)
            
        elif opcion == "2":
            print("\n📝 REGISTRAR NUEVO EMPLEADO")
            nombre = input("Nombre del empleado: ")
            telefono = input("Teléfono (opcional): ")
            resultado = taller.agregar_empleado(nombre, telefono or None)
            print(resultado)
            
        elif opcion == "3":
            print("\n📝 CREAR NUEVA ORDEN DE TRABAJO")
            print("--- Lista de Empleados ---")
            empleados = taller.listar_empleados()
            for empleado in empleados:
                print(f"  ID: {empleado[0]} - {empleado[1]}")
            
            try:
                cliente_id = int(input("\nID del cliente: "))
                vehiculos = taller.obtener_vehiculos_cliente(cliente_id)
                
                if not vehiculos:
                    print("❌ Este cliente no tiene vehículos registrados")
                    continue
                
                print("\n--- Vehículos del cliente ---")
                for vehiculo in vehiculos:
                    print(f"  ID: {vehiculo[0]} - {vehiculo[1]} {vehiculo[2]} ({vehiculo[4]})")
                
                vehiculo_id = int(input("\nID del vehículo: "))
                numero_orden = int(input("Número de orden: "))
                empleado_id = int(input("ID del empleado: "))
                descripcion = input("Descripción del trabajo: ")
                tipo_servicio = input("Tipo de servicio (ej: frenos, aceite, motor): ")
                horas = float(input("Horas trabajadas: "))
                repuestos = float(input("Costo repuestos: $"))
                mano_obra = float(input("Costo mano de obra: $"))
                kilometraje = float(input("Kilometraje: "))
                unidad = input("Unidad (km/millas) [km]: ") or "km"
                
                fecha_fin_input = input("Fecha de finalización (YYYY-MM-DD) o Enter para hoy: ")
                fecha_fin = fecha_fin_input if fecha_fin_input else None
                
                resultado = taller.agregar_orden(numero_orden, vehiculo_id, empleado_id, descripcion, 
                                               tipo_servicio, horas, repuestos, mano_obra, 
                                               kilometraje, unidad, fecha_fin)
                print(resultado)
            except ValueError:
                print("❌ Error: Ingresa valores numéricos válidos")
                
        elif opcion == "4":
            print("\n📝 AÑADIR VEHÍCULO A CLIENTE EXISTENTE")
            try:
                cliente_id = int(input("ID del cliente: "))
                
                if not taller.cliente_existe(cliente_id):
                    print("❌ Error: El cliente no existe")
                    continue
                
                marca = input("Marca del vehículo: ")
                modelo = input("Modelo: ")
                año = input("Año: ")
                placa = input("Placa: ")
                color = input("Color (opcional): ")
                
                resultado = taller.agregar_vehiculo(cliente_id, marca, modelo, año, placa, color or None)
                print(resultado)
            except ValueError:
                print("❌ Error: Ingresa un ID válido")
        
        # 🔍 BUSCAR Y CONSULTAR
        elif opcion == "5":
            print("\n🔍 BUSCAR CLIENTE")
            nombre_buscar = input("Nombre del cliente a buscar: ")
            clientes = taller.buscar_cliente(nombre_buscar)
            
            if clientes:
                print(f"\n✅ Resultados para '{nombre_buscar}':")
                for cliente in clientes:
                    print(f"  🆔 ID: {cliente[0]}")
                    print(f"  👤 Nombre: {cliente[1]}")
                    print(f"  📞 Teléfono: {cliente[2] or 'No tiene'}")
                    print("  " + "-" * 30)
            else:
                print("❌ No se encontraron clientes con ese nombre")
                
        elif opcion == "6":
            print("\n🔍 DETALLES DE CLIENTE")
            try:
                cliente_id = int(input("ID del cliente: "))
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
                    
            except ValueError:
                print("❌ Error: Ingresa un ID válido")
                
        elif opcion == "7":
            print("\n🔍 HISTORIAL POR VEHÍCULO")
            try:
                vehiculo_id = int(input("ID del vehículo: "))
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
                    
            except ValueError:
                print("❌ Error: Ingresa un ID válido")
                
        elif opcion == "8":
            print("\n🔍 BUSCAR ORDEN POR ID")
            try:
                orden_id = int(input("ID de la orden: "))
                # Aquí podríamos agregar una función específica para buscar órdenes
                # Por ahora usamos la validación existente
                if taller.orden_existe(orden_id):
                    print(f"✅ La orden #{orden_id} existe en el sistema")
                    # Podríamos mostrar detalles básicos de la orden
                else:
                    print(f"❌ La orden #{orden_id} no existe")
            except ValueError:
                print("❌ Error: Ingresa un ID válido")
        
        # ✏️ EDITAR Y ACTUALIZAR
        elif opcion == "9":
            print("\n✏️ EDITAR CLIENTE")
            try:
                cliente_id = int(input("ID del cliente a editar: "))
                nuevo_nombre = input("Nuevo nombre: ")
                nuevo_telefono = input("Nuevo teléfono (opcional): ")
                
                resultado = taller.editar_cliente(cliente_id, nuevo_nombre, nuevo_telefono or None)
                print(resultado)
            except ValueError:
                print("❌ Error: Ingresa un ID válido")
                
        elif opcion == "10":
            print("\n✏️ EDITAR EMPLEADO")
            try:
                empleado_id = int(input("ID del empleado a editar: "))
                nuevo_nombre = input("Nuevo nombre: ")
                nuevo_telefono = input("Nuevo teléfono (opcional): ")
                
                resultado = taller.editar_empleado(empleado_id, nuevo_nombre, nuevo_telefono or None)
                print(resultado)
            except ValueError:
                print("❌ Error: Ingresa un ID válido")
                
        elif opcion == "11":
            print("\n✏️ EDITAR ORDEN")
            try:
                orden_id = int(input("ID de la orden a editar: "))
                print("\n¿Qué deseas editar? (dejar en blanco para no cambiar)")
                nueva_desc = input("Nueva descripción: ") or None
                nuevo_precio = input("Nuevo precio total: ") or None
                nuevo_precio = float(nuevo_precio) if nuevo_precio else None
                nuevo_tipo = input("Nuevo tipo de servicio: ") or None
                nuevo_km = input("Nuevo kilometraje: ") or None
                nuevo_km = float(nuevo_km) if nuevo_km else None
                
                resultado = taller.editar_orden(orden_id, nueva_desc, nuevo_precio, nuevo_tipo, nuevo_km)
                print(resultado)
            except ValueError:
                print("❌ Error: Ingresa valores válidos")
        
        # 📊 REPORTES Y ANÁLISIS
        elif opcion == "12":
            print("\n📊 REPORTES Y ANÁLISIS")
            print("  1. 📈 Reporte Semanal")
            print("  2. 📅 Reporte Mensual") 
            print("  3. 🗓️ Reporte Anual")
            print("  4. 🔮 Predicción Temporadas Altas")
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
                
                if reporte['rentabilidad_servicios']:
                    print(f"\n  💵 RENTABILIDAD POR SERVICIO:")
                    for servicio in reporte['rentabilidad_servicios']:
                        print(f"    • {servicio[0]}: ${servicio[3]:.2f} margen promedio")
                        
            elif sub_opcion == "4":
                prediccion = taller.prediccion_temporadas()
                print(f"\n🔮 PREDICCIÓN TEMPORADAS ALTAS:")
                if prediccion['meses_altos']:
                    print("  📈 Meses con mayor actividad histórica:")
                    for mes in prediccion['meses_altos']:
                        nombre_mes = datetime(2024, int(mes[0]), 1).strftime('%B')
                        print(f"    • {nombre_mes}: {mes[1]} trabajos - ${mes[2]:,.2f} ingresos")
                else:
                    print("  ℹ️ No hay suficiente datos históricos para predicciones")
            else:
                print("❌ Opción no válida")
                
        elif opcion == "0":
            print("\n👋 ¡Gracias por usar el Sistema de Gestión del Taller SEYMO!")
            print("¡Hasta pronto! 🚗💨")
            break
        else:
            print("❌ Opción no válida. Por favor, selecciona una opción del menú.")

if __name__ == "__main__":
    menu_principal()
