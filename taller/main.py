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
from typing import Dict, List
import calendar
#Database
from database.database_manager import DatabaseManager
#Utils
from utils.validator import Validator
#Managers
from managers.cliente_manager import ClienteManager
from managers.vehiculo_manager import VehiculoManager
from managers.empleado_manager import EmpleadoManager
from managers.orden_manager import OrdenManager

# Apago las advertencias que no me interesan
warnings.filterwarnings('ignore')

# ============================================================================
# FUNCIÓN PARA CREAR CARPETAS
# ============================================================================
def crear_estructura_carpetas():
    """Esta función crea las carpetas que necesita el programa para funcionar"""
    try:
        # Defino las carpetas que necesito
        carpetas = ['database', 'database/backups', 'reportes', 'graficas', 'reportes_historicos']
        
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

print("Estructura de carpetas lista")

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
            print(f" Error calculando km mensual: {e}")
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
                print(f" Error procesando intervalo: {e}")
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
                print(f" Error procesando vehículo {placa}: {e}")
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
# CLASE PRINCIPAL DEL TALLER (ACTUALIZADA)
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
            self.reportes = ReportManager(self.db)  # VERSIÓN MEJORADA CON REPORTES HISTÓRICOS
            self.proyeccion = ModuloProyeccionCrecimiento(self.db)  # NUEVO MÓDULO
            self.recordatorios = RecordatoriosInteligentesMejorados(self.db)
            
            print(" Sistema Taller SEYMO listo")
            print(" Módulo de Proyección de Crecimiento activado")
            print(" Reportes históricos disponibles")
            
        except Exception as e:
            print(f" Error iniciando el sistema: {e}")
            raise

# ============================================================================
# INTERFAZ GRÁFICA - VENTANA PRINCIPAL (ACTUALIZADA)
# ============================================================================
class TallerSEYMOGUI:
    """Esta clase maneja la ventana principal del programa - VERSIÓN ACTUALIZADA"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Taller SEYMO - Sistema de Gestión MEJORADO")
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
            text=" TALLER SEYMO - SISTEMA DE GESTIÓN MEJORADO",
            font=("Arial", 20, "bold"),
            bg=self.primary_color,
            fg="white"
        ).pack()
        
        tk.Label(
            title_frame,
            text="Gestión Integral con Reportes Históricos y Proyección de Crecimiento",
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
            text=" Cargando estadísticas...",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#2c3e50",
            fg="white",
            font=("Arial", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_main_buttons(self, parent):
        """Creo los botones principales del menú - VERSIÓN ACTUALIZADA"""
        # Primera fila de botones
        row1_frame = tk.Frame(parent, bg=self.primary_color)
        row1_frame.pack(fill=tk.X, pady=5)
        
        # Defino los botones de la primera fila
        buttons_row1 = [
            (" Nuevo Cliente", self.registrar_cliente),
            (" Nuevo Vehículo", self.registrar_vehiculo),
            (" Nuevo Empleado", self.registrar_empleado),
            (" Nueva Orden", self.nueva_orden),
            (" Buscar Cliente", self.buscar_cliente),
            (" Reportes", self.menu_reportes_mejorado),  
            (" Proyección", self.menu_proyeccion)
        ]
        
        # Creo cada botón de la primera fila
        for i, (text, command) in enumerate(buttons_row1):
            btn = tk.Button(
                row1_frame,
                text=text,
                command=command,
                font=("Arial", 10, "bold"),
                bg=self.secondary_color if "Reportes" in text or "Proyección" in text else self.secondary_color,
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
            (" Historial Vehículo", self.historial_vehiculo),
            (" Editar Cliente", self.editar_cliente),
            (" Editar Vehículo", self.editar_vehiculo),
            (" Editar Empleado", self.editar_empleado),
            (" Editar Orden", self.editar_orden),
            (" Recordatorios", self.recordatorios_inteligentes_mejorados),
            (" Eliminar", self.menu_eliminar),
            (" Históricos", self.menu_reportes_historicos),  
            (" Salir", self.salir)
        ]
        
        # Creo cada botón de la segunda fila
        for i, (text, command) in enumerate(buttons_row2):
            btn = tk.Button(
                row2_frame,
                text=text,
                command=command,
                font=("Arial", 10, "bold"),
                bg=self.warning_color if "Editar" in text else 
                   self.danger_color if "Eliminar" in text or "Salir" in text else
                   "#9b59b6" if "Históricos" in text else  # Color especial para históricos
                   self.secondary_color,
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
    
    # ==========================================================================
    # NUEVAS FUNCIONALIDADES: REPORTES HISTÓRICOS
    # ==========================================================================
    
    def menu_reportes_historicos(self):
        """Muestra el menú de reportes históricos por año"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Reportes Históricos por Año")
        dialog.geometry("600x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Obtener años disponibles
        años_disponibles = self.taller.reportes.obtener_años_disponibles()
        
        if not años_disponibles:
            messagebox.showinfo("Información", "No hay datos históricos disponibles")
            dialog.destroy()
            return
        
        # Título
        ttk.Label(dialog, text=" REPORTES HISTÓRICOS POR AÑO", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Seleccione uno o más años para analizar:", 
                 font=("Arial", 10)).pack(pady=10)
        
        # Frame para lista de años
        frame_años = ttk.LabelFrame(dialog, text="Años Disponibles")
        frame_años.pack(pady=15, padx=20, fill=tk.BOTH, expand=True)
        
        # Lista de años con selección múltiple
        listbox_años = tk.Listbox(frame_años, selectmode=tk.MULTIPLE, height=10, font=("Arial", 11))
        scrollbar = ttk.Scrollbar(frame_años)
        listbox_años.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox_años.yview)
        
        # Agregar años a la lista
        for año in sorted(años_disponibles, reverse=True):
            listbox_años.insert(tk.END, f" Año {año}")
        
        listbox_años.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Botones de acción
        frame_botones = tk.Frame(dialog)
        frame_botones.pack(pady=20)
        
        def generar_reporte_año_especifico():
            """Genera reporte para un año específico"""
            selecciones = listbox_años.curselection()
            if not selecciones:
                messagebox.showwarning("Advertencia", "Seleccione al menos un año")
                return
            
            if len(selecciones) > 1:
                messagebox.showwarning("Advertencia", "Seleccione solo un año para reporte específico")
                return
            
            año = años_disponibles[selecciones[0]]
            dialog.destroy()
            self.generar_reporte_año_completo(año)
        
        def generar_comparativa_años():
            """Genera comparativa entre múltiples años"""
            selecciones = listbox_años.curselection()
            if len(selecciones) < 2:
                messagebox.showwarning("Advertencia", "Seleccione al menos 2 años para comparar")
                return
            
            años_seleccionados = [años_disponibles[i] for i in selecciones]
            dialog.destroy()
            self.generar_comparativa_años(años_seleccionados)
        
        def generar_tendencia_historica():
            """Genera análisis de tendencia histórica"""
            selecciones = listbox_años.curselection()
            if len(selecciones) < 3:
                messagebox.showwarning("Advertencia", "Seleccione al menos 3 años para análisis de tendencia")
                return
            
            años_seleccionados = [años_disponibles[i] for i in selecciones]
            dialog.destroy()
            self.generar_tendencia_historica(años_seleccionados)
        
        # Crear botones
        tk.Button(frame_botones, text=" Reporte Año Específico", 
                 command=generar_reporte_año_especifico,
                 bg="#3498db", fg="white", padx=15, pady=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_botones, text=" Comparar Años", 
                 command=generar_comparativa_años,
                 bg="#2ecc71", fg="white", padx=15, pady=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_botones, text=" Tendencia Histórica", 
                 command=generar_tendencia_historica,
                 bg="#9b59b6", fg="white", padx=15, pady=10).pack(side=tk.LEFT, padx=5)
        
        # Información adicional
        ttk.Label(dialog, 
                 text=" Los reportes históricos permiten analizar el crecimiento y tendencias del taller",
                 font=("Arial", 9)).pack(pady=10)
    
    def generar_reporte_año_completo(self, año: int):
        """Genera y muestra un reporte completo para un año específico"""
        try:
            # Generar reporte del año
            reporte_año = self.taller.reportes.reporte_año_especifico(año)
            
            # Mostrar reporte en el área principal
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*80}\n")
            self.result_text.insert(tk.END, f" REPORTE ANUAL {año}\n")
            self.result_text.insert(tk.END, f"{'='*80}\n\n")
            
            # Estadísticas principales
            self.result_text.insert(tk.END, " ESTADÍSTICAS FINANCIERAS:\n")
            self.result_text.insert(tk.END, f"   • Ingresos totales: Q{reporte_año['ingresos_totales']:,.2f}\n")
            self.result_text.insert(tk.END, f"   • Ganancias netas: Q{reporte_año['ganancias_netas']:,.2f}\n")
            self.result_text.insert(tk.END, f"   • Costo de repuestos: Q{reporte_año['costo_repuestos']:,.2f}\n")
            self.result_text.insert(tk.END, f"   • Margen de ganancia: {(reporte_año['ganancias_netas']/reporte_año['ingresos_totales']*100):.1f}%\n")
            self.result_text.insert(tk.END, f"   • Trabajos realizados: {reporte_año['trabajos_totales']}\n")
            self.result_text.insert(tk.END, f"   • Horas trabajadas: {reporte_año['horas_totales']:.1f}\n")
            self.result_text.insert(tk.END, f"   • Ingreso promedio por trabajo: Q{reporte_año['promedio_ingreso_por_trabajo']:.2f}\n")
            self.result_text.insert(tk.END, f"   • Ganancia promedio por trabajo: Q{reporte_año['promedio_ganancias_por_trabajo']:.2f}\n")
            self.result_text.insert(tk.END, f"   • Horas promedio por trabajo: {reporte_año['promedio_horas_por_trabajo']:.1f}\n\n")
            
            # Servicios más populares
            if reporte_año['servicios_populares']:
                self.result_text.insert(tk.END, " SERVICIOS MÁS POPULARES:\n")
                for servicio, cantidad, total in reporte_año['servicios_populares'][:5]:
                    self.result_text.insert(tk.END, f"   • {servicio}: {cantidad} trabajos (Q{total:,.2f})\n")
                self.result_text.insert(tk.END, "\n")
            
            # Clientes más frecuentes
            if reporte_año['clientes_frecuentes']:
                self.result_text.insert(tk.END, " CLIENTES MÁS FRECUENTES:\n")
                for cliente, visitas, gasto in reporte_año['clientes_frecuentes'][:5]:
                    self.result_text.insert(tk.END, f"   • {cliente}: {visitas} visitas (Gasto: Q{gasto:,.2f})\n")
                self.result_text.insert(tk.END, "\n")
            
            # Empleados más productivos
            if reporte_año['empleados_productivos']:
                self.result_text.insert(tk.END, " EMPLEADOS MÁS PRODUCTIVOS:\n")
                for empleado, trabajos, ingresos in reporte_año['empleados_productivos'][:5]:
                    self.result_text.insert(tk.END, f"   • {empleado}: {trabajos} trabajos (Q{ingresos:,.2f})\n")
                self.result_text.insert(tk.END, "\n")
            
            # Ganancias por mes
            if reporte_año['ganancias_por_mes']:
                self.result_text.insert(tk.END, " GANANCIAS POR MES:\n")
                total_meses = 0
                for mes_num, ganancia, trabajos in reporte_año['ganancias_por_mes']:
                    nombre_mes = calendar.month_name[int(mes_num)]
                    self.result_text.insert(tk.END, f"   • {nombre_mes}: Q{ganancia:,.2f} ({trabajos} trabajos)\n")
                    total_meses += 1
                
                if total_meses > 0:
                    promedio_mensual = reporte_año['ganancias_totales'] / total_meses
                    self.result_text.insert(tk.END, f"   • Promedio mensual: Q{promedio_mensual:,.2f}\n")
                self.result_text.insert(tk.END, "\n")
            
            # Preguntar si desea gráficas
            respuesta = messagebox.askyesno("Generar Gráficas", 
                f"¿Desea generar gráficas para el año {año}?")
            
            if respuesta:
                try:
                    # Gráfica de ganancias mensuales
                    fig1 = self.taller.reportes.crear_grafica_ganancias_mensuales_año(reporte_año)
                    if fig1:
                        self.mostrar_grafica(fig1, f"Ganancias Mensuales {año}")
                    
                    # Gráfica de servicios populares
                    fig2 = self.taller.reportes.crear_grafica_servicios_populares_año(reporte_año)
                    if fig2:
                        self.mostrar_grafica(fig2, f"Servicios Populares {año}")
                    
                    # Gráfica de marcas frecuentes
                    fig3 = self.taller.reportes.crear_grafica_marcas_frecuentes_año(reporte_año)
                    if fig3:
                        self.mostrar_grafica(fig3, f"Marcas Frecuentes {año}")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudieron generar todas las gráficas: {e}")
            
            # Opción para guardar reporte
            respuesta_guardar = messagebox.askyesno("Guardar Reporte", 
                f"¿Desea guardar el reporte del año {año} en un archivo?")
            
            if respuesta_guardar:
                nombre_archivo = f"reportes_historicos/reporte_anual_{año}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                self.guardar_reporte_texto(reporte_año, nombre_archivo)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte: {e}")

    def generar_comparativa_años(self, años: List[int]):
        """Genera comparativa entre múltiples años"""
        try:
            # Generar comparativa
            comparativa = self.taller.reportes.reporte_comparativa_años(años)
        
        # Mostrar comparativa
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*80}\n")
            self.result_text.insert(tk.END, f" COMPARATIVA FINANCIERA ENTRE AÑOS\n")
            self.result_text.insert(tk.END, f"{'='*80}\n\n")
        
        # Datos por año
            for año in sorted(años):
                datos = comparativa['datos_por_año'][año]
                self.result_text.insert(tk.END, f" AÑO {año}:\n")
                self.result_text.insert(tk.END, f"   • Ingresos totales: Q{datos.get('ingresos', datos.get('ganancias', 0)):,.2f}\n")
                self.result_text.insert(tk.END, f"   • Ganancias netas: Q{datos.get('ganancias_netas', 0):,.2f}\n")
                self.result_text.insert(tk.END, f"   • Trabajos: {datos['trabajos']}\n")
                self.result_text.insert(tk.END, f"   • Clientes únicos: {datos['clientes_unicos']}\n")
                self.result_text.insert(tk.END, f"   • Ingreso promedio: Q{datos.get('promedio_ingreso', datos.get('promedio_ticket', 0)):.2f}\n")
                self.result_text.insert(tk.END, f"   • Ganancia promedio: Q{datos.get('promedio_ganancias', 0):,.2f}\n")
            
                if datos['mejor_mes']:
                    self.result_text.insert(tk.END, f"   • Mejor mes: {datos['mejor_mes']['nombre_mes']} (Q{datos['mejor_mes']['ganancias']:,.2f})\n")
            
            # Calcular margen si hay datos
                ingresos = datos.get('ingresos', datos.get('ganancias', 0))
                if ingresos > 0:
                    margen = (datos.get('ganancias_netas', 0) / ingresos) * 100
                    self.result_text.insert(tk.END, f"   • Margen de ganancia: {margen:.1f}%\n")
            
                self.result_text.insert(tk.END, "\n")
        
        # Crecimiento entre años
            if comparativa['crecimiento']:
                self.result_text.insert(tk.END, " CRECIMIENTO ENTRE AÑOS:\n")
                for periodo, datos_crecimiento in comparativa['crecimiento'].items():
                    self.result_text.insert(tk.END, f"   • {periodo}: {datos_crecimiento['crecimiento_ganancias']:.1f}% ")
                
                if datos_crecimiento['crecimiento_ganancias'] > 0:
                    self.result_text.insert(tk.END, "\n")
                else:
                    self.result_text.insert(tk.END, "\n")
                
                self.result_text.insert(tk.END, f"     Aumento trabajos: {datos_crecimiento['aumento_trabajos']}\n")
                self.result_text.insert(tk.END, f"     Aumento clientes: {datos_crecimiento['aumento_clientes']}\n")
            self.result_text.insert(tk.END, "\n")
        
        # Análisis de tendencia financiera
            self.result_text.insert(tk.END, " ANÁLISIS DE TENDENCIA FINANCIERA:\n")
        
            ingresos_por_año = [comparativa['datos_por_año'][a].get('ingresos', 
                                comparativa['datos_por_año'][a].get('ganancias', 0)) 
                                for a in sorted(años)]
            ganancias_por_año = [comparativa['datos_por_año'][a].get('ganancias_netas', 0) 
                                for a in sorted(años)]
        
            if len(ingresos_por_año) >= 2:
            # Crecimiento de ingresos
                crecimiento_ingresos = ((ingresos_por_año[-1] - ingresos_por_año[0]) / 
                                       ingresos_por_año[0]) * 100 if ingresos_por_año[0] > 0 else 0
            
            # Crecimiento de ganancias
                crecimiento_ganancias = ((ganancias_por_año[-1] - ganancias_por_año[0]) / 
                                        ganancias_por_año[0]) * 100 if ganancias_por_año[0] > 0 else 0
            
                self.result_text.insert(tk.END, f"   • Crecimiento ingresos totales: {crecimiento_ingresos:.1f}%\n")
                self.result_text.insert(tk.END, f"   • Crecimiento ganancias netas: {crecimiento_ganancias:.1f}%\n")
            
            # Análisis de eficiencia
                if ingresos_por_año[-1] > 0:
                    margen_inicial = (ganancias_por_año[0] / ingresos_por_año[0]) * 100 if ingresos_por_año[0] > 0 else 0
                    margen_final = (ganancias_por_año[-1] / ingresos_por_año[-1]) * 100 if ingresos_por_año[-1] > 0 else 0
                    mejora_margen = margen_final - margen_inicial
                
                    self.result_text.insert(tk.END, f"   • Mejora en margen: {mejora_margen:+.1f}%\n")
            
            # Interpretación
                self.result_text.insert(tk.END, "\n INTERPRETACIÓN:\n")
            
                if crecimiento_ganancias > crecimiento_ingresos:
                    self.result_text.insert(tk.END, "    EFICIENCIA MEJORANDO\n")
                    self.result_text.insert(tk.END, "   Las ganancias crecen más rápido que los ingresos\n")
                elif crecimiento_ganancias > 0:
                    self.result_text.insert(tk.END, "    CRECIMIENTO SALUDABLE\n")
                    self.result_text.insert(tk.END, "   Ingresos y ganancias creciendo\n")
                else:
                    self.result_text.insert(tk.END, "    REVISIÓN NECESARIA\n")
                    self.result_text.insert(tk.END, "   Evaluar costos y precios\n")
        
        # Preguntar por gráfica
            respuesta = messagebox.askyesno("Generar Gráfica", "¿Desea generar gráfica comparativa?")
        
            if respuesta:
                try:
                    fig = self.taller.reportes.crear_grafica_comparativa_años(comparativa)
                    if fig:
                        self.mostrar_grafica(fig, f"Comparativa Años {min(años)}-{max(años)}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo generar la gráfica: {e}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar la comparativa: {e}")
    
    def generar_tendencia_historica(self, años: List[int]):
        """Genera análisis de tendencia histórica"""
        try:
            # Generar comparativa primero
            comparativa = self.taller.reportes.reporte_comparativa_años(años)
            
            # Mostrar análisis de tendencia
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*80}\n")
            self.result_text.insert(tk.END, f" ANÁLISIS DE TENDENCIA HISTÓRICA\n")
            self.result_text.insert(tk.END, f"{'='*80}\n\n")
            
            # Calcular tendencia lineal
            años_ordenados = sorted(años)
            ingresos = [comparativa['datos_por_año'][a].get('ingresos', comparativa['datos_por_año'][a].get('ganancias', 0)) for a in años_ordenados]
            ganancias_netas = [comparativa['datos_por_año'][a].get('ganancias_netas', 0) for a in años_ordenados]
            if len(ingresos) >= 3:
                # Calcular regresión lineal simple
                x = np.arange(len(años_ordenados))
                y_ingresos = np.array(ingresos)
                y_ganancias = np.array(ganancias_netas)
                
                # Coeficiente de correlación
                correlacion_ingresos = np.corrcoef(x, y_ingresos)[0, 1] if len(ingresos) > 1 else 0
                correlacion_ganancias = np.corrcoef(x, y_ganancias)[0, 1] if len(ganancias_netas) > 1 else 0
                
                # Tendencia
                z_ingresos = np.polyfit(x, y_ingresos, 1)
                z_ganancias = np.polyfit(x, y_ganancias, 1)

                pendiente_ingresos = z_ingresos[0]
                pendiente_ganancias = z_ganancias[0]
                
                tendencia_ingresos = (pendiente_ingresos / np.mean(y_ingresos)) * 100 if np.mean(y_ingresos) > 0 else 0
                tendencia_ganancias = (pendiente_ganancias / np.mean(y_ganancias)) * 100 if np.mean(y_ganancias) > 0 else 0

                self.result_text.insert(tk.END, " ANÁLISIS ESTADÍSTICO:\n")
                self.result_text.insert(tk.END, f"   • Correlación año-ingresos: {correlacion_ingresos:.3f}\n")
                self.result_text.insert(tk.END, f"   • Correlación año-ganancias: {correlacion_ganancias:.3f}\n")
                self.result_text.insert(tk.END, f"   • Tendencia ingresos anual: {tendencia_ingresos:.1f}%\n")
                self.result_text.insert(tk.END, f"   • Tendencia ganancias anual: {tendencia_ganancias:.1f}%\n")
                self.result_text.insert(tk.END, f"   • Variabilidad ingresos: {np.std(ingresos)/np.mean(ingresos)*100:.1f}%\n")
                self.result_text.insert(tk.END, f"   • Variabilidad ganancias: {np.std(ganancias_netas)/np.mean(ganancias_netas)*100:.1f}%\n\n")

                # Interpretación
                self.result_text.insert(tk.END, " INTERPRETACIÓN FINANCIERA:\n")
                
                if abs(correlacion_ingresos) > 0.7:
                    if correlacion_ingresos > 0:
                        self.result_text.insert(tk.END, "   •  FUERTE TENDENCIA POSITIVA EN INGRESOS\n")
                    else:
                        self.result_text.insert(tk.END, "   •  FUERTE TENDENCIA NEGATIVA EN INGRESOS\n")
                elif abs(correlacion_ingresos) > 0.3:
                    if correlacion_ingresos > 0:
                        self.result_text.insert(tk.END, "   •   TENDENCIA MODERADA EN INGRESOS\n")
                    else:
                        self.result_text.insert(tk.END, "   •   TENDENCIA MODERADA EN INGRESOS\n")
                else:
                    self.result_text.insert(tk.END, "   •   TENDENCIA DÉBIL EN INGRESOS\n")
                
                if tendencia_ganancias > tendencia_ingresos:
                    self.result_text.insert(tk.END, "   •  EFICIENCIA MEJORANDO\n")
                    self.result_text.insert(tk.END, "     Las ganancias crecen más rápido que los ingresos\n")
                elif tendencia_ganancias > 0:
                    self.result_text.insert(tk.END, "   •  CRECIMIENTO PARALELO\n")
                    self.result_text.insert(tk.END, "     Ingresos y ganancias crecen similarmente\n")
                else:
                    self.result_text.insert(tk.END, "   •  EFICIENCIA DISMINUYENDO\n")
                    self.result_text.insert(tk.END, "     Evaluar costos y estructura de precios\n")
            
                self.result_text.insert(tk.END, "\n")
            
            self.result_text.insert(tk.END, " ANÁLISIS DE EFICIENCIA FINANCIERA:\n")
        
            margenes = []
            for año in años_ordenados:
                ingresos_año = comparativa['datos_por_año'][año].get('ingresos', comparativa['datos_por_año'][año].get('ganancias', 0))
                ganancias_año = comparativa['datos_por_año'][año].get('ganancias_netas', 0)
            
                if ingresos_año > 0:
                    margen = (ganancias_año / ingresos_año) * 100
                    margenes.append(margen)
                    self.result_text.insert(tk.END, f"   • {año}: Margen = {margen:.1f}%\n")
            if len(margenes) >= 2:
                mejora_margen = margenes[-1] - margenes[0]
                self.result_text.insert(tk.END, f"   • Mejora total en margen: {mejora_margen:+.1f}%\n")
            
                if mejora_margen > 2:
                    self.result_text.insert(tk.END, "      Excelente mejora en eficiencia\n")
                elif mejora_margen > 0:
                    self.result_text.insert(tk.END, "      Mejora moderada en eficiencia\n")
                else:
                    self.result_text.insert(tk.END, "      Eficiencia disminuyendo - revisar costos\n")
        
        # Recomendaciones basadas en tendencia
            self.result_text.insert(tk.END, "\n RECOMENDACIONES ESTRATÉGICAS:\n")
        
            if len(ganancias_netas) >= 2:
                crecimiento_total_ganancias = ((ganancias_netas[-1] - ganancias_netas[0]) / ganancias_netas[0]) * 100 if ganancias_netas[0] > 0 else 0
            
                if crecimiento_total_ganancias > 50:
                    self.result_text.insert(tk.END, "   1.  Crecimiento excelente - Mantener estrategias\n")
                    self.result_text.insert(tk.END, "   2.  Considerar reinversión de utilidades\n")
                    self.result_text.insert(tk.END, "   3.  Evaluar expansión del negocio\n")
                elif crecimiento_total_ganancias > 20:
                    self.result_text.insert(tk.END, "   1.  Crecimiento saludable - Optimizar procesos\n")
                    self.result_text.insert(tk.END, "   2.  Fortalecer programas de fidelización\n")
                    self.result_text.insert(tk.END, "   3.  Mejorar eficiencia operativa\n")
                elif crecimiento_total_ganancias > 0:
                    self.result_text.insert(tk.END, "   1.   Crecimiento lento - Revisar estrategias\n")
                    self.result_text.insert(tk.END, "   2.  Analizar competencia y precios\n")
                    self.result_text.insert(tk.END, "   3.  Implementar nuevas tácticas de marketing\n")
                else:
                    self.result_text.insert(tk.END, "   1.  Crecimiento negativo - Acción inmediata\n")
                    self.result_text.insert(tk.END, "   2.  Revisar costos y precios urgentemente\n")
                    self.result_text.insert(tk.END, "   3.  Analizar causas de la disminución\n")
        
        # Proyección para el próximo año
            self.result_text.insert(tk.END, "\n PROYECCIÓN PARA EL PRÓXIMO AÑO:\n")
        
            if len(ganancias_netas) >= 2:
                crecimiento_promedio_ganancias = ((ganancias_netas[-1] - ganancias_netas[0]) / ganancias_netas[0]) * 100 / (len(ganancias_netas) - 1)
                proyeccion_ganancias = ganancias_netas[-1] * (1 + crecimiento_promedio_ganancias/100)
            
                crecimiento_promedio_ingresos = ((ingresos[-1] - ingresos[0]) / ingresos[0]) * 100 / (len(ingresos) - 1)
                proyeccion_ingresos = ingresos[-1] * (1 + crecimiento_promedio_ingresos/100)
            
                self.result_text.insert(tk.END, f"   • Ingresos proyectados: Q{proyeccion_ingresos:,.2f}\n")
                self.result_text.insert(tk.END, f"   • Ganancias proyectadas: Q{proyeccion_ganancias:,.2f}\n")
                self.result_text.insert(tk.END, f"   • Crecimiento esperado: {crecimiento_promedio_ganancias:.1f}%\n")
                self.result_text.insert(tk.END, f"   • Trabajos estimados: {comparativa['datos_por_año'][max(años)]['trabajos'] * (1 + crecimiento_promedio_ganancias/100):.0f}\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el análisis de tendencia: {e}")
    
    def guardar_reporte_texto(self, reporte: Dict, nombre_archivo: str):
        """Guarda un reporte en un archivo de texto"""
        try:
            contenido = f"Reporte Anual {reporte['año']}\n"
            contenido += "="*50 + "\n\n"
            contenido += f"Ganancias totales: Q{reporte['ganancias_totales']:,.2f}\n"
            contenido += f"Trabajos realizados: {reporte['trabajos_totales']}\n"
            contenido += f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            messagebox.showinfo("Reporte guardado", f"Reporte guardado en:\n{nombre_archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el reporte: {e}")
    
    # ==========================================================================
    # NUEVAS FUNCIONALIDADES: PROYECCIÓN DE CRECIMIENTO
    # ==========================================================================
    
    def menu_proyeccion(self):
        """Muestra el menú de proyección de crecimiento"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Módulo de Proyección de Crecimiento")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Título
        ttk.Label(dialog, text=" MÓDULO DE PROYECCIÓN DE CRECIMIENTO", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Análisis predictivo y planificación estratégica", 
                 font=("Arial", 10)).pack(pady=10)
        
        # Frame para opciones
        frame_opciones = tk.Frame(dialog)
        frame_opciones.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # Botones de las funcionalidades
        tk.Button(frame_opciones, text=" Proyección Avanzada", 
                 command=self.generar_proyeccion_avanzada,
                 bg="#9b59b6", fg="white", padx=20, pady=15,
                 font=("Arial", 11, "bold")).pack(pady=10, fill=tk.X)
        
        tk.Button(frame_opciones, text=" Análisis de Tendencia", 
                 command=self.analizar_tendencia_historica_gui,
                 bg="#3498db", fg="white", padx=20, pady=15,
                 font=("Arial", 11, "bold")).pack(pady=10, fill=tk.X)
        
        tk.Button(frame_opciones, text=" Predicción de Demanda", 
                 command=self.predecir_demanda_mensual_gui,
                 bg="#2ecc71", fg="white", padx=20, pady=15,
                 font=("Arial", 11, "bold")).pack(pady=10, fill=tk.X)
        
        tk.Button(frame_opciones, text=" Optimización de Recursos", 
                 command=self.analizar_optimizacion_recursos_gui,
                 bg="#e67e22", fg="white", padx=20, pady=15,
                 font=("Arial", 11, "bold")).pack(pady=10, fill=tk.X)
        
        tk.Button(frame_opciones, text=" Plan Estratégico", 
                 command=self.generar_plan_estrategico_gui,
                 bg="#e74c3c", fg="white", padx=20, pady=15,
                 font=("Arial", 11, "bold")).pack(pady=10, fill=tk.X)
        
        # Información
        ttk.Label(dialog, 
                 text=" Este módulo utiliza datos históricos para predecir tendencias futuras\n"
                      "y generar recomendaciones estratégicas para el crecimiento del taller",
                 font=("Arial", 9), justify="center").pack(pady=20)
    
    def generar_proyeccion_avanzada(self):
        """Genera proyección de crecimiento avanzada"""
        try:
            # Obtener años de historia
            años_historia = simpledialog.askinteger(
                "Años de Historia", 
                "¿Cuántos años de historia desea analizar? (2-5):",
                minvalue=2, maxvalue=5, initialvalue=3
            )
            
            if not años_historia:
                return
            
            # Mostrar mensaje de procesamiento
            self.show_message(" Generando proyección avanzada...\nPor favor espere...")
            self.root.update()
            
            # Generar proyección
            proyeccion = self.taller.reportes.proyeccion_crecimiento_avanzada(años_historia)
            
            if not proyeccion:
                messagebox.showinfo("Información", "No hay suficientes datos históricos para generar proyección")
                return
            
            # Mostrar informe
            informe = self.taller.reportes.crear_informe_proyeccion_completo(proyeccion)
            self.clear_results()
            self.result_text.insert(tk.END, informe)
            
            # Preguntar por gráfica
            respuesta = messagebox.askyesno("Generar Gráfica", 
                "¿Desea generar gráfica de proyección?")
            
            if respuesta:
                try:
                    fig = self.taller.reportes.crear_grafica_proyeccion_avanzada(proyeccion)
                    if fig:
                        self.mostrar_grafica(fig, "Proyección de Crecimiento Avanzada")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo generar la gráfica: {e}")
            
            # Preguntar por guardar informe
            respuesta_guardar = messagebox.askyesno("Guardar Informe", 
                "¿Desea guardar el informe de proyección en un archivo?")
            
            if respuesta_guardar:
                resultado = self.taller.reportes.guardar_informe_proyeccion(proyeccion)
                self.show_message(resultado)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar la proyección: {e}")
    
    def analizar_tendencia_historica_gui(self):
        """Interfaz para análisis de tendencia histórica"""
        try:
            años_atras = simpledialog.askinteger(
                "Período de Análisis", 
                "¿Cuántos años hacia atrás desea analizar? (2-10):",
                minvalue=2, maxvalue=10, initialvalue=5
            )
            
            if not años_atras:
                return
            
            # Generar análisis
            datos = self.taller.proyeccion.analizar_tendencia_historica(años_atras)
            
            if not datos:
                messagebox.showinfo("Información", "No hay suficientes datos para el análisis")
                return
            
            # Mostrar resultados
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*80}\n")
            self.result_text.insert(tk.END, " ANÁLISIS DE TENDENCIA HISTÓRICA\n")
            self.result_text.insert(tk.END, f"{'='*80}\n\n")
            
            for año, info in sorted(datos.items()):
                self.result_text.insert(tk.END, f" AÑO {año}:\n")
                self.result_text.insert(tk.END, f"   • Ganancias: Q{info['ganancias']:,.2f}\n")
                self.result_text.insert(tk.END, f"   • Trabajos: {info['trabajos']}\n")
                self.result_text.insert(tk.END, f"   • Clientes únicos: {info['clientes_unicos']}\n")
                self.result_text.insert(tk.END, f"   • Ticket promedio: Q{info['ticket_promedio']:.2f}\n\n")
            
            # Calcular crecimiento
            if len(datos) >= 2:
                años_ordenados = sorted(datos.keys())
                ganancias_inicial = datos[años_ordenados[0]]['ganancias']
                ganancias_final = datos[años_ordenados[-1]]['ganancias']
                
                if ganancias_inicial > 0:
                    crecimiento_total = ((ganancias_final - ganancias_inicial) / ganancias_inicial) * 100
                    crecimiento_anual = crecimiento_total / (len(datos) - 1)
                    
                    self.result_text.insert(tk.END, " RESUMEN DE CRECIMIENTO:\n")
                    self.result_text.insert(tk.END, f"   • Período analizado: {len(datos)} años\n")
                    self.result_text.insert(tk.END, f"   • Crecimiento total: {crecimiento_total:.1f}%\n")
                    self.result_text.insert(tk.END, f"   • Crecimiento anual promedio: {crecimiento_anual:.1f}%\n")
                    
                    # Interpretación
                    self.result_text.insert(tk.END, "\n INTERPRETACIÓN:\n")
                    if crecimiento_anual > 15:
                        self.result_text.insert(tk.END, "    CRECIMIENTO ACELERADO\n")
                        self.result_text.insert(tk.END, "   Excelente desempeño. Mantener estrategias.\n")
                    elif crecimiento_anual > 8:
                        self.result_text.insert(tk.END, "    CRECIMIENTO SALUDABLE\n")
                        self.result_text.insert(tk.END, "   Buen desempeño. Buscar oportunidades de mejora.\n")
                    elif crecimiento_anual > 0:
                        self.result_text.insert(tk.END, "     CRECIMIENTO MODERADO\n")
                        self.result_text.insert(tk.END, "   Crecimiento estable. Evaluar nuevas estrategias.\n")
                    else:
                        self.result_text.insert(tk.END, "     DECRECIMIENTO\n")
                        self.result_text.insert(tk.END, "   Evaluar urgentemente operaciones y estrategias.\n")
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el análisis: {e}")
    
    def predecir_demanda_mensual_gui(self):
        """Interfaz para predicción de demanda mensual"""
        try:
            año = simpledialog.askinteger(
                "Año a Predecir", 
                "¿Para qué año desea predecir la demanda?",
                minvalue=datetime.now().year, 
                maxvalue=datetime.now().year + 5,
                initialvalue=datetime.now().year + 1
            )
            
            if not año:
                return
            
            # Generar predicción
            prediccion = self.taller.proyeccion.predecir_demanda_mensual(año)
            
            if not prediccion:
                messagebox.showinfo("Información", "No hay suficientes datos para predecir la demanda")
                return
            
            # Mostrar resultados
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*80}\n")
            self.result_text.insert(tk.END, f" PREDICCIÓN DE DEMANDA MENSUAL - AÑO {año}\n")
            self.result_text.insert(tk.END, f"{'='*80}\n\n")
            
            total_proyectado = 0
            for mes_num in range(1, 13):
                if mes_num in prediccion:
                    data = prediccion[mes_num]
                    self.result_text.insert(tk.END, f"{data['mes']}:\n")
                    self.result_text.insert(tk.END, f"   • Proyección: Q{data['proyeccion']:,.2f}\n")
                    self.result_text.insert(tk.END, f"   • Rango probable: Q{data['rango_min']:,.2f} - Q{data['rango_max']:,.2f}\n")
                    self.result_text.insert(tk.END, f"   • Confianza: {data['confianza']:.0f}%\n")
                    self.result_text.insert(tk.END, "\n")
                    
                    total_proyectado += data['proyeccion']
            
            self.result_text.insert(tk.END, f" TOTAL PROYECTADO ANUAL: Q{total_proyectado:,.2f}\n\n")
            
            # Recomendaciones
            self.result_text.insert(tk.END, " RECOMENDACIONES OPERATIVAS:\n")
            
            # Identificar meses altos y bajos
            meses_altos = sorted([(mes_num, data) for mes_num, data in prediccion.items()], 
                                key=lambda x: x[1]['proyeccion'], reverse=True)[:3]
            meses_bajos = sorted([(mes_num, data) for mes_num, data in prediccion.items()], 
                                key=lambda x: x[1]['proyeccion'])[:3]
            
            if meses_altos:
                self.result_text.insert(tk.END, "   • Preparar para temporada alta:\n")
                for mes_num, data in meses_altos:
                    self.result_text.insert(tk.END, f"     - {data['mes']}: Aumentar inventario y personal\n")
            
            if meses_bajos:
                self.result_text.insert(tk.END, "   • Estrategias para temporada baja:\n")
                for mes_num, data in meses_bajos:
                    self.result_text.insert(tk.END, f"     - {data['mes']}: Ofrecer promociones especiales\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar la predicción: {e}")
    
    def analizar_optimizacion_recursos_gui(self):
        """Interfaz para análisis de optimización de recursos"""
        try:
            # Generar análisis
            resultado = self.taller.proyeccion.analizar_optimizacion_recursos()
            
            if not resultado or not resultado['productividad_empleados']:
                messagebox.showinfo("Información", "No hay suficientes datos de empleados para el análisis")
                return
            
            # Mostrar resultados
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*80}\n")
            self.result_text.insert(tk.END, " ANÁLISIS DE OPTIMIZACIÓN DE RECURSOS\n")
            self.result_text.insert(tk.END, f"{'='*80}\n\n")
            
            # Productividad por empleado
            self.result_text.insert(tk.END, " PRODUCTIVIDAD POR EMPLEADO (últimos 90 días):\n\n")
            
            for emp in resultado['productividad_empleados']:
                self.result_text.insert(tk.END, f" {emp['empleado']}:\n")
                self.result_text.insert(tk.END, f"   • Productividad/hora: Q{emp['productividad_hora']:.2f}\n")
                self.result_text.insert(tk.END, f"   • Eficiencia: {emp['eficiencia']:.1%}\n")
                self.result_text.insert(tk.END, f"   • Horas trabajadas: {emp['horas_trabajadas']:.1f}\n")
                self.result_text.insert(tk.END, f"   • Ingresos generados: Q{emp['ingresos_generados']:,.2f}\n")
                
                # Evaluación de desempeño
                promedio_productividad = sum(e['productividad_hora'] for e in resultado['productividad_empleados']) / len(resultado['productividad_empleados'])
                if emp['productividad_hora'] > promedio_productividad * 1.2:
                    self.result_text.insert(tk.END, "   •  DESEMPEÑO: EXCELENTE\n")
                elif emp['productividad_hora'] > promedio_productividad * 0.8:
                    self.result_text.insert(tk.END, "   •  DESEMPEÑO: ADECUADO\n")
                else:
                    self.result_text.insert(tk.END, "   •   DESEMPEÑO: MEJORABLE\n")
                
                self.result_text.insert(tk.END, "\n")
            
            # Estadísticas generales
            self.result_text.insert(tk.END, " ESTADÍSTICAS GENERALES:\n")
            total_horas = sum(e['horas_trabajadas'] for e in resultado['productividad_empleados'])
            total_ingresos = sum(e['ingresos_generados'] for e in resultado['productividad_empleados'])
            productividad_promedio = total_ingresos / total_horas if total_horas > 0 else 0
            
            self.result_text.insert(tk.END, f"   • Total empleados analizados: {resultado['total_empleados_analizados']}\n")
            self.result_text.insert(tk.END, f"   • Horas totales trabajadas: {total_horas:.1f}\n")
            self.result_text.insert(tk.END, f"   • Ingresos totales generados: Q{total_ingresos:,.2f}\n")
            self.result_text.insert(tk.END, f"   • Productividad promedio/hora: Q{productividad_promedio:.2f}\n\n")
            
            # Recomendaciones
            if resultado['recomendaciones_optimizacion']:
                self.result_text.insert(tk.END, " RECOMENDACIONES DE OPTIMIZACIÓN:\n")
                for i, recomendacion in enumerate(resultado['recomendaciones_optimizacion'], 1):
                    self.result_text.insert(tk.END, f"   {i}. {recomendacion}\n")
            else:
                self.result_text.insert(tk.END, " El equipo muestra una productividad balanceada\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el análisis: {e}")
    
    def generar_plan_estrategico_gui(self):
        """Interfaz para generar plan estratégico"""
        try:
            años_proyeccion = simpledialog.askinteger(
                "Horizonte del Plan", 
                "¿Cuántos años desea proyectar en el plan estratégico? (1-5):",
                minvalue=1, maxvalue=5, initialvalue=3
            )
            
            if not años_proyeccion:
                return
            
            # Generar plan
            self.show_message(" Generando plan estratégico...\nPor favor espere...")
            self.root.update()
            
            plan = self.taller.proyeccion.generar_plan_crecimiento_estrategico(años_proyeccion)
            
            if not plan:
                messagebox.showinfo("Información", "No hay suficientes datos para generar el plan estratégico")
                return
            
            # Mostrar plan
            self.clear_results()
            self.result_text.insert(tk.END, f"\n{'='*80}\n")
            self.result_text.insert(tk.END, " PLAN ESTRATÉGICO DE CRECIMIENTO\n")
            self.result_text.insert(tk.END, f"{'='*80}\n\n")
            
            self.result_text.insert(tk.END, f" Fecha de generación: {plan['fecha_generacion']}\n")
            self.result_text.insert(tk.END, f" Horizonte del plan: {plan['horizonte_plan']} años\n")
            self.result_text.insert(tk.END, f" Inversión recomendada: Q{plan['inversion_recomendada']:,.2f}\n\n")
            
            # Objetivos estratégicos
            self.result_text.insert(tk.END, " OBJETIVOS ESTRATÉGICOS:\n")
            self.result_text.insert(tk.END, f"{'─'*40}\n")
            
            self.result_text.insert(tk.END, " Inmediatos (0-6 meses):\n")
            for objetivo in plan['objetivos_estrategicos']['inmediatos']:
                self.result_text.insert(tk.END, f"   • {objetivo}\n")
            self.result_text.insert(tk.END, "\n")
            
            self.result_text.insert(tk.END, " Mediano Plazo (6-18 meses):\n")
            for objetivo in plan['objetivos_estrategicos']['mediano_plazo']:
                self.result_text.insert(tk.END, f"   • {objetivo}\n")
            self.result_text.insert(tk.END, "\n")
            
            self.result_text.insert(tk.END, " Largo Plazo (18+ meses):\n")
            for objetivo in plan['objetivos_estrategicos']['largo_plazo']:
                self.result_text.insert(tk.END, f"   • {objetivo}\n")
            self.result_text.insert(tk.END, "\n")
            
            # Plan de implementación
            self.result_text.insert(tk.END, " PLAN DE IMPLEMENTACIÓN:\n")
            self.result_text.insert(tk.END, f"{'─'*40}\n")
            
            for trimestre, acciones in plan['plan_implementacion'].items():
                self.result_text.insert(tk.END, f"{trimestre.replace('_', ' ').title()}:\n")
                for accion in acciones:
                    self.result_text.insert(tk.END, f"   • {accion}\n")
                self.result_text.insert(tk.END, "\n")
            
            # Métricas de seguimiento
            self.result_text.insert(tk.END, " MÉTRICAS DE SEGUIMIENTO:\n")
            self.result_text.insert(tk.END, f"{'─'*40}\n")
            
            for categoria, metricas in plan['metricas_seguimiento'].items():
                self.result_text.insert(tk.END, f"{categoria.title()}:\n")
                for metrica in metricas:
                    self.result_text.insert(tk.END, f"   • {metrica}\n")
                self.result_text.insert(tk.END, "\n")
            
            # Resumen de proyección
            if plan['proyeccion_base']:
                self.result_text.insert(tk.END, " RESUMEN DE PROYECCIÓN BASE:\n")
                self.result_text.insert(tk.END, f"{'─'*40}\n")
                self.result_text.insert(tk.END, f"   • Año base: {plan['proyeccion_base']['año_base']}\n")
                self.result_text.insert(tk.END, f"   • Ganancias base: Q{plan['proyeccion_base']['ganancias_base']:,.2f}\n")
                self.result_text.insert(tk.END, f"   • Crecimiento promedio: {plan['proyeccion_base']['crecimiento_promedio_anual']:.1f}%\n")
                self.result_text.insert(tk.END, "\n")
            
            # Opción para guardar
            respuesta = messagebox.askyesno("Guardar Plan", 
                "¿Desea guardar el plan estratégico en un archivo?")
            
            if respuesta:
                nombre_archivo = f"reportes_historicos/plan_estrategico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                self.guardar_plan_estrategico(plan, nombre_archivo)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el plan estratégico: {e}")
    
    def guardar_plan_estrategico(self, plan: Dict, nombre_archivo: str):
        """Guarda el plan estratégico en un archivo"""
        try:
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write(f"PLAN ESTRATÉGICO DE CRECIMIENTO - TALLER SEYMO\n")
                f.write("="*60 + "\n\n")
                f.write(f"Fecha: {plan['fecha_generacion']}\n")
                f.write(f"Horizonte: {plan['horizonte_plan']} años\n\n")
                
                f.write("OBJETIVOS ESTRATÉGICOS:\n")
                f.write("-"*40 + "\n")
                for categoria, objetivos in plan['objetivos_estrategicos'].items():
                    f.write(f"\n{categoria.replace('_', ' ').title()}:\n")
                    for obj in objetivos:
                        f.write(f"  • {obj}\n")
                
                f.write("\nPLAN DE IMPLEMENTACIÓN:\n")
                f.write("-"*40 + "\n")
                for trimestre, acciones in plan['plan_implementacion'].items():
                    f.write(f"\n{trimestre.replace('_', ' ').title()}:\n")
                    for accion in acciones:
                        f.write(f"  • {accion}\n")
                
                f.write("\nMÉTRICAS DE SEGUIMIENTO:\n")
                f.write("-"*40 + "\n")
                for categoria, metricas in plan['metricas_seguimiento'].items():
                    f.write(f"\n{categoria.title()}:\n")
                    for metrica in metricas:
                        f.write(f"  • {metrica}\n")
            
            messagebox.showinfo("Plan guardado", f"Plan guardado en:\n{nombre_archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el plan: {e}")
    
    # ==========================================================================
    # FUNCIONES ORIGINALES (MANTENIDAS PARA COMPATIBILIDAD)
    # ==========================================================================
    
    def menu_reportes_mejorado(self):
        """Muestra el menú de reportes mejorado"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Reportes Avanzados")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
    
        def generar_reporte_con_graficas(periodo):
            """Genera un reporte completo con todas las gráficas"""
            try:
            # Generar reporte del período
                reporte = self.taller.reportes.reporte_periodo(periodo)
            
            # Muestro el reporte en el área de resultados
                self.clear_results()
                self.result_text.insert(tk.END, f"\n{'='*60}\n")
                self.result_text.insert(tk.END, f" REPORTE {periodo.upper()}\n")
                self.result_text.insert(tk.END, f"{'='*60}\n\n")
            
            # Fecha del período
                self.result_text.insert(tk.END, f" Período: {reporte['fecha_inicio']} al {datetime.now().date()}\n\n")
            
            # Métricas principales
                self.result_text.insert(tk.END, f" Ganancias totales: Q{reporte.get('ingresos_totales', reporte.get('ganancias', 0)):,.2f}\n")
                self.result_text.insert(tk.END, f" Ganancias netas: Q{reporte.get('ganancias_netas', 0):,.2f}\n")
                self.result_text.insert(tk.END, f" Horas trabajadas: {reporte.get('horas_trabajadas', reporte.get('horas_totales', 0)):.1f}\n")
                self.result_text.insert(tk.END, f" Trabajos completados: {reporte.get('trabajos_completados', reporte.get('trabajos_totales', 0))}\n")
                self.result_text.insert(tk.END, f" Costo repuestos: Q{reporte.get('costo_repuestos', 0):,.2f}\n\n")
            
            # Servicios más populares
                if 'servicios_populares' in reporte and reporte['servicios_populares']:
                    self.result_text.insert(tk.END, f" SERVICIOS MÁS POPULARES:\n")
                    for servicio in reporte['servicios_populares']:
                        if len(servicio) >= 3:
                            servicio_nombre, cantidad, total = servicio
                            self.result_text.insert(tk.END, f"   • {servicio_nombre}: {cantidad} trabajos (Q{total:.2f})\n")
                        elif len(servicio) == 2:
                            servicio_nombre, cantidad = servicio
                            self.result_text.insert(tk.END, f"   • {servicio_nombre}: {cantidad} trabajos\n")
                    self.result_text.insert(tk.END, "\n")
            
            # Empleados más productivos
                if 'empleados_productivos' in reporte and reporte['empleados_productivos']:
                    self.result_text.insert(tk.END, f" EMPLEADOS MÁS PRODUCTIVOS:\n")
                    for empleado in reporte['empleados_productivos']:
                        if len(empleado) >= 3:
                            nombre, trabajos, ingresos = empleado
                            self.result_text.insert(tk.END, f"   • {nombre}: {trabajos} trabajos (Q{ingresos:.2f})\n")
                    self.result_text.insert(tk.END, "\n")
            
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
                    
                        messagebox.showinfo("Gráficas generadas", "Las gráficas han sido generadas exitosamente.")
                    
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudieron generar todas las gráficas: {e}")
        
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo generar el reporte: {e}")
    
        def generar_reporte_clientes():
            """Genera reporte de clientes con gráficas"""
            try:
                reporte_clientes = self.taller.reportes.reporte_clientes()
            
            # Muestro el reporte
                self.clear_results()
                self.result_text.insert(tk.END, f"\n{'='*60}\n")
                self.result_text.insert(tk.END, " REPORTE DE CLIENTES\n")
                self.result_text.insert(tk.END, f"{'='*60}\n\n")
                self.result_text.insert(tk.END, f" Total de clientes: {reporte_clientes['total_clientes']}\n\n")
            
                if reporte_clientes['clientes_frecuentes']:
                    self.result_text.insert(tk.END, " CLIENTES MÁS FRECUENTES:\n")
                    for cliente in reporte_clientes['clientes_frecuentes'][:10]:  # Top 10
                        if len(cliente) >= 3:
                            nombre, ordenes, gasto_total = cliente
                            self.result_text.insert(tk.END, f"   • {nombre}: {ordenes} órdenes (Gasto total: Q{gasto_total:.2f})\n")
                        elif len(cliente) == 2:
                            nombre, ordenes = cliente
                            self.result_text.insert(tk.END, f"   • {nombre}: {ordenes} órdenes\n")
            
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
        
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo generar el reporte de clientes: {e}")
    
        def generar_reporte_empleados():
            """Genera reporte de empleados con gráficas"""
            try:
                reporte_empleados = self.taller.reportes.reporte_empleados()
            
            # Muestro el reporte
                self.clear_results()
                self.result_text.insert(tk.END, f"\n{'='*60}\n")
                self.result_text.insert(tk.END, " REPORTE DE EMPLEADOS\n")
                self.result_text.insert(tk.END, f"{'='*60}\n\n")
                self.result_text.insert(tk.END, f" Total de empleados: {reporte_empleados['total_empleados']}\n\n")
            
                if reporte_empleados['empleados']:
                    self.result_text.insert(tk.END, " PRODUCTIVIDAD DE EMPLEADOS:\n")
                    for empleado in reporte_empleados['empleados']:
                        if len(empleado) >= 6:
                            nombre, total_ordenes, total_horas, total_ingresos, promedio_por_orden, ultimo_trabajo = empleado
                            self.result_text.insert(tk.END, f"\n   {nombre}:\n")
                            self.result_text.insert(tk.END, f"     • Órdenes: {total_ordenes or 0}\n")
                            self.result_text.insert(tk.END, f"     • Horas trabajadas: {total_horas or 0:.1f}\n")
                            self.result_text.insert(tk.END, f"     • Ingresos generados: Q{total_ingresos or 0:.2f}\n")
                            if promedio_por_orden:
                                self.result_text.insert(tk.END, f"     • Promedio por orden: Q{promedio_por_orden:.2f}\n")
                            if ultimo_trabajo:
                                self.result_text.insert(tk.END, f"     • Último trabajo: {ultimo_trabajo}\n")
            
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
        
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo generar el reporte de empleados: {e}")
    
        def mostrar_proyeccion_simple():
            """Muestra proyecciones de crecimiento simple con gráfica"""
            try:
                proyeccion = self.taller.reportes.proyeccion_crecimiento_avanzada(años_historia=2)
            
                if not proyeccion:
                    messagebox.showinfo("Información", "No hay suficientes datos históricos (se necesitan al menos 2 años) para generar proyecciones")
                    return
            
            # Muestro las proyecciones
                self.clear_results()
                self.result_text.insert(tk.END, f"\n{'='*60}\n")
                self.result_text.insert(tk.END, " PROYECCIÓN DE CRECIMIENTO\n")
                self.result_text.insert(tk.END, f"{'='*60}\n\n")
            
            # Mostrar datos históricos
                if 'datos_historicos' in proyeccion and proyeccion['datos_historicos']:
                    self.result_text.insert(tk.END, " DATOS HISTÓRICOS:\n")
                    for año, datos in proyeccion['datos_historicos'].items():
                        self.result_text.insert(tk.END, f"   Año {año}: Q{datos['ganancias_totales']:,.2f}\n")
                    self.result_text.insert(tk.END, "\n")
            
            # Mostrar el crecimiento promedio
                self.result_text.insert(tk.END, f" Crecimiento promedio anual: {proyeccion.get('crecimiento_promedio_anual', 0):.1f}%\n")
            
            # Mostrar proyecciones futuras
                if 'proyecciones' in proyeccion and proyeccion['proyecciones']:
                    self.result_text.insert(tk.END, f"\n PROYECCIONES FUTURAS:\n")
                    for año, datos in proyeccion['proyecciones'].items():
                        self.result_text.insert(tk.END, f"   Año {año}: Q{datos['ganancia_anual_proyectada']:,.2f}\n")
            
                dialog.destroy()
            
            # Preguntar por gráfica
                respuesta = messagebox.askyesno("Gráfica de Proyección", 
                    "¿Desea generar una gráfica de la proyección de crecimiento?")
            
                if respuesta:
                    try:
                        fig = self.taller.reportes.crear_grafica_proyeccion_avanzada(proyeccion)
                        if fig:
                            self.mostrar_grafica(fig, "Proyección de Crecimiento")
                    
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo generar la gráfica: {e}")
        
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo generar la proyección: {e}")
    
    # Creo los elementos del menú de reportes
        ttk.Label(dialog, text=" REPORTES AVANZADOS", font=("Arial", 14, "bold")).pack(pady=20)
    
    # Sección de reportes por período
        ttk.Label(dialog, text=" Reportes por Período:", font=("Arial", 11, "bold")).pack(pady=10, anchor="w")
    
        frame_periodo = tk.Frame(dialog)
        frame_periodo.pack(pady=10, padx=20, fill=tk.X)
    
        ttk.Button(frame_periodo, text=" Reporte Semanal", 
              command=lambda: generar_reporte_con_graficas('semana')).pack(pady=5, fill=tk.X)
        ttk.Button(frame_periodo, text=" Reporte Mensual", 
              command=lambda: generar_reporte_con_graficas('mes')).pack(pady=5, fill=tk.X)
        ttk.Button(frame_periodo, text=" Reporte Anual", 
              command=lambda: generar_reporte_con_graficas('año')).pack(pady=5, fill=tk.X)
    
    # Línea divisoria
        tk.Frame(dialog, height=2, bg="gray").pack(fill=tk.X, padx=20, pady=10)
    
    # Sección de reportes específicos
        ttk.Label(dialog, text=" Reportes Específicos:", font=("Arial", 11, "bold")).pack(pady=10, anchor="w")
    
        frame_especificos = tk.Frame(dialog)
        frame_especificos.pack(pady=10, padx=20, fill=tk.X)
    
        ttk.Button(frame_especificos, text=" Reporte de Clientes", 
              command=generar_reporte_clientes).pack(pady=5, fill=tk.X)
        ttk.Button(frame_especificos, text=" Reporte de Empleados", 
              command=generar_reporte_empleados).pack(pady=5, fill=tk.X)
    
    # Línea divisoria
        tk.Frame(dialog, height=2, bg="gray").pack(fill=tk.X, padx=20, pady=10)
    
    # Sección de proyecciones
        ttk.Label(dialog, text=" Análisis Predictivo:", font=("Arial", 11, "bold")).pack(pady=10, anchor="w")
    
        frame_proyecciones = tk.Frame(dialog)
        frame_proyecciones.pack(pady=10, padx=20, fill=tk.X)
    
        ttk.Button(frame_proyecciones, text=" Proyección de Crecimiento", 
              command=mostrar_proyeccion_simple).pack(pady=5, fill=tk.X)
    
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
        
        tk.Button(graph_dialog, text=" Guardar Gráfica", command=guardar_grafica,
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
            
            # Obtengo años de datos históricos
            años_disponibles = self.taller.reportes.obtener_años_disponibles()
            
            # Creo el texto para la barra de estado con emojis y datos
            texto_estadisticas = (
                f" Clientes: {total_clientes} | "
                f" Vehículos: {total_vehiculos} | "
                f" Órdenes: {total_ordenes} | "
                f" Histórico: {len(años_disponibles)} años | "
                f" Sistema mejorado activo"
            )
            
            # Actualizo la barra de estado
            self.status_bar.config(text=texto_estadisticas)
            
            # Programo la próxima actualización en 30 segundos
            self.root.after(30000, self.actualizar_estadisticas)
            
        except Exception as e:
            # Si hay algún error, muestro un mensaje simple
            self.status_bar.config(text=" Sistema Taller SEYMO MEJORADO | © 2025")
            # Reintento en 60 segundos
            self.root.after(60000, self.actualizar_estadisticas)
    
    # Las demás funciones originales (registrar_cliente, registrar_vehiculo, etc.)
    # se mantienen igual que en la versión anterior...
    
    # ==========================================================================
    # FUNCIONES PRINCIPALES DEL PROGRAMA (ORIGINALES)
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
                self.show_message(f" Cliente registrado exitosamente\nID: {cliente_id}")
                dialog.destroy()  # Cierro la ventana
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Creo los elementos de la ventana
        ttk.Label(dialog, text=" REGISTRAR NUEVO CLIENTE", font=("Arial", 12, "bold")).pack(pady=20)
        
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
                    messagebox.showerror("Error", "El año es obligatoria")
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
        ttk.Label(dialog, text=" REGISTRAR NUEVO VEHÍCULO", font=("Arial", 12, "bold")).pack(pady=10)
        
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
        ttk.Label(dialog, text=" REGISTRAR NUEVO EMPLEADO", font=("Arial", 12, "bold")).pack(pady=20)
        
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
        tk.Label(main_content, text=" NUEVA ORDEN DE TRABAJO", 
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
                resultados_text.insert(tk.END, " No se encontraron clientes")
                return
            
            # Muestro cada cliente encontrado
            for cliente in clientes:
                resultados_text.insert(tk.END, f"\n{'═'*60}\n")
                resultados_text.insert(tk.END, f" ID: {cliente[0]}\n")
                resultados_text.insert(tk.END, f" Nombre: {cliente[1]}\n")
                resultados_text.insert(tk.END, f" Teléfono: {cliente[2] or 'No tiene'}\n")
                resultados_text.insert(tk.END, f" NIT: {cliente[3] or 'No tiene'}\n")
                
                # Muestro los vehículos del cliente
                vehiculos = self.taller.vehiculos.obtener_vehiculos_cliente(cliente[0])
                if vehiculos:
                    resultados_text.insert(tk.END, f"\n VEHÍCULOS ({len(vehiculos)}):\n")
                    for vehiculo in vehiculos:
                        resultados_text.insert(tk.END, f"   • {vehiculo[1]} {vehiculo[2]} {vehiculo[3]} - Placa: {vehiculo[4]}\n")
                else:
                    resultados_text.insert(tk.END, "\n Este cliente no tiene vehículos registrados.\n")
            
            resultados_text.insert(tk.END, f"\n{'═'*60}\n")
        
        # Creo los elementos de la ventana
        ttk.Label(dialog, text=" BUSCAR CLIENTE", font=("Arial", 12, "bold")).pack(pady=10)
        
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
                resultados_text.insert(tk.END, " Ingrese una placa para buscar")
                return
            
            # Busco el vehículo por placa
            cursor = self.taller.db.execute_query(
                'SELECT id FROM vehiculos WHERE placa = ?', 
                (placa,)
            )
            resultado = cursor.fetchone()
            
            if not resultado:
                resultados_text.insert(tk.END, f" No se encontró vehículo con placa: {placa}")
                return
            
            vehiculo_id = resultado[0]
            
            # Obtengo los detalles del vehículo
            detalles = self.taller.vehiculos.detalles_vehiculo(vehiculo_id)
            
            if not detalles:
                resultados_text.insert(tk.END, f" Error al obtener detalles del vehículo")
                return
            
            vehiculo_info, ordenes = detalles['vehiculo'], detalles['ordenes']
            
            # Muestro la información del vehículo
            resultados_text.insert(tk.END, f"\n{'═'*60}\n")
            resultados_text.insert(tk.END, f" DETALLES DEL VEHÍCULO\n")
            resultados_text.insert(tk.END, f"{'═'*60}\n\n")
            resultados_text.insert(tk.END, f" Marca: {vehiculo_info[0]}\n")
            resultados_text.insert(tk.END, f" Modelo: {vehiculo_info[1]}\n")
            resultados_text.insert(tk.END, f" Año: {vehiculo_info[2]}\n")
            resultados_text.insert(tk.END, f"  Placa: {vehiculo_info[3]}\n")
            resultados_text.insert(tk.END, f" Color: {vehiculo_info[4] or 'No especificado'}\n")
            resultados_text.insert(tk.END, f" Cliente: {vehiculo_info[5]}\n")
            resultados_text.insert(tk.END, f" Teléfono: {vehiculo_info[6] or 'No tiene'}\n")
            resultados_text.insert(tk.END, f" NIT: {vehiculo_info[7] or 'No tiene'}\n")
            
            # Muestro el historial de órdenes
            if ordenes:
                resultados_text.insert(tk.END, f"\n{'═'*60}\n")
                resultados_text.insert(tk.END, f" HISTORIAL DE ÓRDENES ({len(ordenes)})\n")
                resultados_text.insert(tk.END, f"{'═'*60}\n\n")
                
                for orden in ordenes:
                    resultados_text.insert(tk.END, f" ORDEN #{orden[0]}\n")
                    resultados_text.insert(tk.END, f"    Fecha: {orden[1] or 'Sin fecha'}\n")
                    resultados_text.insert(tk.END, f"    Servicio: {orden[3]}\n")
                    resultados_text.insert(tk.END, f"    Precio: Q{orden[4]:.2f}\n")
                    resultados_text.insert(tk.END, f"     Kilometraje: {orden[5]} {orden[6]}\n")
                    resultados_text.insert(tk.END, f"    Empleado: {orden[7] or 'No asignado'}\n")
                    resultados_text.insert(tk.END, f"    Descripción: {orden[2][:100]}...\n")
                    resultados_text.insert(tk.END, f"{'─'*50}\n")
            else:
                resultados_text.insert(tk.END, f"\n Este vehículo no tiene órdenes de trabajo registradas.\n")
        
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
        ttk.Label(dialog, text=" HISTORIAL DE VEHÍCULO", font=("Arial", 12, "bold")).pack(pady=10)
        
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
        ttk.Label(dialog, text=" EDITAR CLIENTE", font=("Arial", 12, "bold")).pack(pady=10)
        
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
    def editar_vehiculo(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Vehículo")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.grab_set()
        vehiculo_id_var = tk.StringVar()
        marca_var = tk.StringVar()
        modelo_var = tk.StringVar()
        año_var = tk.StringVar()
        placa_var = tk.StringVar()
        color_var = tk.StringVar()
        cliente_info_var = tk.StringVar(value="No seleccionado")
        def buscar__por_cliente():
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
            def seleccionar_cliente():
                seleccion = listbox.curselection()
                if not seleccion:
                    return
                
                texto = listbox.get(seleccion[0])
                cliente_id = int(texto.split("ID: ")[1].split(" |")[0])
                cliente_nombre = texto.split("| ")[1].split(" |")[0]
                search_dialog.destroy()
                mostrar_vehiculo_cliente(cliente_id, cliente_nombre)                
                    
            ttk.Button(search_dialog, text="Buscar", command=perform_search).pack(pady=5)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            ttk.Button(search_dialog, text="Seleccionar cliente", command=seleccionar_cliente).pack(pady=10)
        def mostrar_vehiculo_cliente(cliente_id, cliente_nombre):
            vehiculos = self.taller.vehiculos.obtener_vehiculos_cliente(cliente_id)
            if not vehiculos:
                messagebox.showinfo("Información", f"El cliente '{cliente_nombre}' no tiene vehículos registrados")
                return
            vehiculo_dialog = tk.Toplevel(dialog)
            vehiculo_dialog.title(f"Seleccionar Vehículo - {cliente_nombre}")
            vehiculo_dialog.geometry("600x500")
        
            ttk.Label(vehiculo_dialog, text=f"Vehículos de {cliente_nombre}:").pack(pady=10)
        
            listbox = tk.Listbox(vehiculo_dialog, width=70, height=20)
            scrollbar = ttk.Scrollbar(vehiculo_dialog)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
        
            # Mostrar todos los vehículos del cliente
            for vehiculo in vehiculos:
                id_veh, marca, modelo, año, placa, color = vehiculo
                listbox.insert(tk.END,
                    f"ID: {id_veh} | {marca} {modelo} {año} | "
                    f"Placa: {placa} | Color: {color or 'No especificado'}")
            def seleccionar_vehiculo():
                seleccion = listbox.curselection()
                if seleccion:
                    texto = listbox.get(seleccion[0])
                    vehiculo_id = int(texto.split("ID: ")[1].split(" |")[0])
                
                # Extraer información del vehículo del texto
                    partes = texto.split(" | ")
                    marca_modelo = partes[1]
                    placa_texto = partes[2].replace("Placa: ", "")
                
                # Actualizar variables
                    vehiculo_id_var.set(str(vehiculo_id))
                    cliente_id_var.set(str(cliente_id))
                    cliente_info_var.set(f"{cliente_nombre} (ID: {cliente_id})")
                
                # Cargar datos completos del vehículo
                    cargar_datos_vehiculo(vehiculo_id)
                
                    vehiculo_dialog.destroy()
            def cargar_datos_vehiculo(vehiculo_id):
                detalles = self.taller.vehiculos.detalles_vehiculo(vehiculo_id)
                if detalles:
                    vehiculo_info = detalles['vehiculo']
                    marca_var.set(vehiculo_info[0])
                    modelo_var.set(vehiculo_info[1])
                    año_var.set(str(vehiculo_info[2]))
                    placa_var.set(vehiculo_info[3])
                    color_var.set(vehiculo_info[4] or "")
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            ttk.Button(vehiculo_dialog, text="Seleccionar Vehículo", command=seleccionar_vehiculo).pack(pady=10)
        
        def guardar():
            try:
                if not vehiculo_id_var.get().strip():
                    messagebox.showerror("Error", "Debe seleccionar un vehículo")
                    return
            
                vehiculo_id = int(vehiculo_id_var.get())
            
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
                año = int(año_var.get())
                if not self.taller.validator.validar_año_vehiculo(año):
                    messagebox.showerror("Error", "Año del vehículo inválido")
                    return
            
                if not placa_var.get().strip():
                    messagebox.showerror("Error", "La placa es obligatoria")
                    return
            
                placa = placa_var.get().strip().upper()
            
                cursor = self.taller.db.execute_query(
                    'SELECT id FROM vehiculos WHERE placa = ? AND id != ?',
                    (placa, vehiculo_id)
                )
                if cursor.fetchone():
                    messagebox.showerror("Error", f"Ya existe otro vehículo con la placa {placa}")
                    return
                resultado = self.taller.vehiculos.editar_vehiculo(
                    vehiculo_id,
                   marca_var.get().strip(),
                    modelo_var.get().strip(),
                    año,
                    placa,
                    color_var.get().strip() or None
                )
                self.show_message(resultado)
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", f"Dato inválido: {e}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Label(dialog, text=" EDITAR VEHÍCULO", font=("Arial", 12, "bold")).pack(pady=10)
        ttk.Label(dialog, text="Primero busque el cliente, luego seleccione el vehículo", font=("Arial", 9)).pack(pady=5)
        ttk.Button(dialog, text="1. Buscar por Cliente", command=buscar__por_cliente, style="Accent.TButton").pack(pady=10)
        ttk.Label(dialog, text="Cliente seleccionado:").pack(pady=5)
        ttk.Entry(dialog, textvariable=cliente_info_var, width=50, state='readonly').pack(pady=5)
    
        ttk.Label(dialog, text="ID Vehículo:").pack(pady=5)
        ttk.Entry(dialog, textvariable=vehiculo_id_var, width=40, state='readonly').pack(pady=5)
    
    
        frame_campos = ttk.LabelFrame(dialog, text="Datos del Vehículo")
        frame_campos.pack(pady=10, padx=20, fill=tk.X)
    
        ttk.Label(frame_campos, text="Marca:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame_campos, textvariable=marca_var, width=30).grid(row=0, column=1, padx=5, pady=5)
    
        ttk.Label(frame_campos, text="Modelo:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame_campos, textvariable=modelo_var, width=30).grid(row=1, column=1, padx=5, pady=5)
    
        ttk.Label(frame_campos, text="Año:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame_campos, textvariable=año_var, width=30).grid(row=2, column=1, padx=5, pady=5)
    
        ttk.Label(frame_campos, text="Placa:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame_campos, textvariable=placa_var, width=30).grid(row=3, column=1, padx=5, pady=5)
    
        ttk.Label(frame_campos, text="Color (opcional):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame_campos, textvariable=color_var, width=30).grid(row=4, column=1, padx=5, pady=5)
    
        frame_botones = tk.Frame(dialog)
        frame_botones.pack(pady=10)
    
        ttk.Button(frame_botones, text="Guardar Cambios", command=guardar).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
        style = ttk.Style()
        style.configure("Accent.TButton", background="#3498db", foreground="white", font=("Arial", 10, "bold"))

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
        ttk.Label(dialog, text=" EDITAR EMPLEADO", font=("Arial", 12, "bold")).pack(pady=10)
        
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
        ttk.Label(dialog, text=" EDITAR ORDEN DE TRABAJO", font=("Arial", 12, "bold")).pack(pady=10)
        
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
    
    def menu_eliminar(self):
        """Muestra el menú de opciones para eliminar"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Eliminar Registros")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Título
        ttk.Label(dialog, text=" ELIMINAR REGISTROS", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        ttk.Label(dialog, text="Seleccione qué tipo de registro desea eliminar:", 
                 font=("Arial", 10)).pack(pady=10)
        
        # Frame para los botones
        frame_botones = tk.Frame(dialog)
        frame_botones.pack(pady=30, padx=20, fill=tk.BOTH, expand=True)
        
        # Botones para eliminar
        tk.Button(frame_botones, text=" Eliminar Cliente", 
                 command=self.eliminar_cliente,
                 bg="#e74c3c", fg="white", padx=20, pady=15,
                 font=("Arial", 11, "bold")).pack(pady=10, fill=tk.X)
        
        tk.Button(frame_botones, text=" Eliminar Vehículo", 
                 command=self.eliminar_vehiculo,
                 bg="#e74c3c", fg="white", padx=20, pady=15,
                 font=("Arial", 11, "bold")).pack(pady=10, fill=tk.X)
        
        tk.Button(frame_botones, text=" Eliminar Orden", 
                 command=self.eliminar_orden,
                 bg="#e74c3c", fg="white", padx=20, pady=15,
                 font=("Arial", 11, "bold")).pack(pady=10, fill=tk.X)
        
        tk.Button(frame_botones, text=" Eliminar Empleado", 
                 command=self.eliminar_empleado,
                 bg="#e74c3c", fg="white", padx=20, pady=15,
                 font=("Arial", 11, "bold")).pack(pady=10, fill=tk.X)
        
        # Información de advertencia
        ttk.Label(dialog, text=" ADVERTENCIA: Las eliminaciones NO se pueden deshacer", 
                 font=("Arial", 9, "bold"), foreground="#e74c3c").pack(pady=20)
    
    def eliminar_cliente(self):
        """Muestra una ventana para eliminar un cliente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Eliminar Cliente")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variable para buscar cliente
        search_var = tk.StringVar()
        resultados_text = scrolledtext.ScrolledText(dialog, height=20, width=70)
        
        def buscar_cliente():
            """Busca clientes para eliminar"""
            resultados_text.delete(1.0, tk.END)
            clientes = self.taller.clientes.buscar_cliente_por_nombre(search_var.get())
            
            if not clientes:
                resultados_text.insert(tk.END, " No se encontraron clientes")
                return
            
            # Muestro cada cliente encontrado
            for cliente in clientes:
                resultados_text.insert(tk.END, f"\n{'═'*60}\n")
                resultados_text.insert(tk.END, f" ID: {cliente[0]}\n")
                resultados_text.insert(tk.END, f" Nombre: {cliente[1]}\n")
                resultados_text.insert(tk.END, f" Teléfono: {cliente[2] or 'No tiene'}\n")
                resultados_text.insert(tk.END, f" NIT: {cliente[3] or 'No tiene'}\n")
                
                # Muestro los vehículos del cliente
                vehiculos = self.taller.vehiculos.obtener_vehiculos_cliente(cliente[0])
                if vehiculos:
                    resultados_text.insert(tk.END, f"\n VEHÍCULOS ({len(vehiculos)}):\n")
                    for vehiculo in vehiculos:
                        resultados_text.insert(tk.END, f"   • {vehiculo[1]} {vehiculo[2]} {vehiculo[3]} - Placa: {vehiculo[4]}\n")
                else:
                    resultados_text.insert(tk.END, "\n Este cliente no tiene vehículos registrados.\n")
            
            resultados_text.insert(tk.END, f"\n{'═'*60}\n")
        
        def eliminar_seleccionado():
            """Elimina el cliente seleccionado"""
            try:
                # Pido el ID del cliente a eliminar
                cliente_id_str = simpledialog.askstring("Eliminar Cliente", "Ingrese el ID del cliente a eliminar:")
                if not cliente_id_str:
                    return
                
                cliente_id = int(cliente_id_str)
                
                # Elimino el cliente
                resultado = self.taller.clientes.eliminar_cliente(cliente_id)
                self.show_message(resultado)
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "El ID debe ser un número válido")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Creo los elementos de la ventana
        ttk.Label(dialog, text=" ELIMINAR CLIENTE", font=("Arial", 12, "bold")).pack(pady=10)
        
        ttk.Label(dialog, text="Buscar cliente por nombre:").pack(pady=5)
        ttk.Entry(dialog, textvariable=search_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Buscar", command=buscar_cliente).pack(pady=10)
        
        resultados_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        ttk.Button(dialog, text="Eliminar Cliente por ID", command=eliminar_seleccionado,
                  style="Danger.TButton").pack(pady=10)
    
    def eliminar_vehiculo(self):
        """Muestra una ventana para eliminar un vehículo"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Eliminar Vehículo")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variable para buscar vehículo
        placa_var = tk.StringVar()
        resultados_text = scrolledtext.ScrolledText(dialog, height=20, width=70)
        
        def buscar_por_placa():
            """Busca vehículos por placa"""
            resultados_text.delete(1.0, tk.END)
            placa = placa_var.get().strip().upper()
            
            if not placa:
                resultados_text.insert(tk.END, " Ingrese una placa para buscar")
                return
            
            # Busco el vehículo por placa
            cursor = self.taller.db.execute_query(
                'SELECT id FROM vehiculos WHERE placa = ?', 
                (placa,)
            )
            resultado = cursor.fetchone()
            
            if not resultado:
                resultados_text.insert(tk.END, f" No se encontró vehículo con placa: {placa}")
                return
            
            vehiculo_id = resultado[0]
            
            # Obtengo los detalles del vehículo
            detalles = self.taller.vehiculos.detalles_vehiculo(vehiculo_id)
            
            if not detalles:
                resultados_text.insert(tk.END, f" Error al obtener detalles del vehículo")
                return
            
            vehiculo_info, ordenes = detalles['vehiculo'], detalles['ordenes']
            
            # Muestro la información del vehículo
            resultados_text.insert(tk.END, f"\n{'═'*60}\n")
            resultados_text.insert(tk.END, f" DETALLES DEL VEHÍCULO\n")
            resultados_text.insert(tk.END, f"{'═'*60}\n\n")
            resultados_text.insert(tk.END, f" Marca: {vehiculo_info[0]}\n")
            resultados_text.insert(tk.END, f" Modelo: {vehiculo_info[1]}\n")
            resultados_text.insert(tk.END, f" Año: {vehiculo_info[2]}\n")
            resultados_text.insert(tk.END, f"  Placa: {vehiculo_info[3]}\n")
            resultados_text.insert(tk.END, f" Color: {vehiculo_info[4] or 'No especificado'}\n")
            resultados_text.insert(tk.END, f" Cliente: {vehiculo_info[5]}\n")
            resultados_text.insert(tk.END, f" Teléfono: {vehiculo_info[6] or 'No tiene'}\n")
            resultados_text.insert(tk.END, f" NIT: {vehiculo_info[7] or 'No tiene'}\n")
            resultados_text.insert(tk.END, f" ID Vehículo: {vehiculo_info[8]}\n")
            
            # Muestro el historial de órdenes
            if ordenes:
                resultados_text.insert(tk.END, f"\n ÓRDENES ASOCIADAS ({len(ordenes)}):\n")
                for orden in ordenes[:5]:  # Muestro solo las primeras 5
                    resultados_text.insert(tk.END, f"   • Orden #{orden[0]} - {orden[3]} - Q{orden[4]:.2f}\n")
                if len(ordenes) > 5:
                    resultados_text.insert(tk.END, f"   ... y {len(ordenes)-5} más\n")
            else:
                resultados_text.insert(tk.END, f"\n Este vehículo no tiene órdenes de trabajo registradas.\n")
        
        def eliminar_seleccionado():
            """Elimina el vehículo seleccionado"""
            try:
                # Pido el ID del vehículo a eliminar
                vehiculo_id_str = simpledialog.askstring("Eliminar Vehículo", "Ingrese el ID del vehículo a eliminar:")
                if not vehiculo_id_str:
                    return
                
                vehiculo_id = int(vehiculo_id_str)
                
                # Elimino el vehículo
                resultado = self.taller.vehiculos.eliminar_vehiculo(vehiculo_id)
                self.show_message(resultado)
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "El ID debe ser un número válido")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Creo los elementos de la ventana
        ttk.Label(dialog, text=" ELIMINAR VEHÍCULO", font=("Arial", 12, "bold")).pack(pady=10)
        
        ttk.Label(dialog, text="Buscar vehículo por placa:").pack(pady=5)
        ttk.Entry(dialog, textvariable=placa_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Buscar", command=buscar_por_placa).pack(pady=10)
        
        resultados_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        ttk.Button(dialog, text="Eliminar Vehículo por ID", command=eliminar_seleccionado,
                  style="Danger.TButton").pack(pady=10)
    
    def eliminar_orden(self):
        """Muestra una ventana para eliminar una orden"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Eliminar Orden de Trabajo")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variable para buscar orden
        orden_id_var = tk.StringVar()
        resultados_text = scrolledtext.ScrolledText(dialog, height=20, width=70)
        
        def buscar_orden():
            """Busca órdenes por número"""
            resultados_text.delete(1.0, tk.END)
            orden_id = orden_id_var.get().strip()
            
            if not orden_id:
                resultados_text.insert(tk.END, " Ingrese un número de orden para buscar")
                return
            
            try:
                orden_id_int = int(orden_id)
            except ValueError:
                resultados_text.insert(tk.END, " El número de orden debe ser un número")
                return
            
            # Verifico si la orden existe
            if not self.taller.ordenes.orden_existe(orden_id_int):
                resultados_text.insert(tk.END, f" No se encontró la orden #{orden_id}")
                return
            
            # Obtengo los detalles de la orden
            detalles = self.taller.ordenes.obtener_detalles_orden(orden_id_int)
            if not detalles:
                resultados_text.insert(tk.END, f" Error al obtener detalles de la orden")
                return
            
            # Muestro la información de la orden
            resultados_text.insert(tk.END, f"\n{'═'*60}\n")
            resultados_text.insert(tk.END, f" DETALLES DE LA ORDEN #{detalles['id']}\n")
            resultados_text.insert(tk.END, f"{'═'*60}\n\n")
            resultados_text.insert(tk.END, f" Fecha: {detalles['fecha_fin']}\n")
            resultados_text.insert(tk.END, f" Tipo de servicio: {detalles['tipo_servicio']}\n")
            resultados_text.insert(tk.END, f" Descripción: {detalles['descripcion_trabajo'][:100]}...\n")
            resultados_text.insert(tk.END, f" Precio total: Q{detalles['precio_final']:.2f}\n")
            resultados_text.insert(tk.END, f"  Horas trabajadas: {detalles['horas_trabajadas']}\n")
            resultados_text.insert(tk.END, f"  Kilometraje: {detalles['kilometraje']} {detalles['unidad_kilometraje']}\n\n")
            
            resultados_text.insert(tk.END, f" VEHÍCULO:\n")
            resultados_text.insert(tk.END, f"   • {detalles['vehiculo_marca']} {detalles['vehiculo_modelo']} {detalles['vehiculo_año']}\n")
            resultados_text.insert(tk.END, f"   • Placa: {detalles['vehiculo_placa']}\n\n")
            
            resultados_text.insert(tk.END, f" CLIENTE:\n")
            resultados_text.insert(tk.END, f"   • Nombre: {detalles['cliente_nombre']}\n")
            resultados_text.insert(tk.END, f"   • Teléfono: {detalles['cliente_telefono'] or 'No tiene'}\n")
            resultados_text.insert(tk.END, f"   • NIT: {detalles['cliente_nit'] or 'No tiene'}\n\n")
            
            resultados_text.insert(tk.END, f" EMPLEADO:\n")
            resultados_text.insert(tk.END, f"   • {detalles['empleado_nombre'] or 'No asignado'}\n")
        
        def eliminar_seleccionado():
            """Elimina la orden seleccionada"""
            try:
                orden_id = orden_id_var.get().strip()
                if not orden_id:
                    messagebox.showerror("Error", "Ingrese un número de orden")
                    return
                
                orden_id_int = int(orden_id)
                
                # Elimino la orden
                resultado = self.taller.ordenes.eliminar_orden(orden_id_int)
                self.show_message(resultado)
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "El número de orden debe ser un número válido")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Creo los elementos de la ventana
        ttk.Label(dialog, text=" ELIMINAR ORDEN DE TRABAJO", font=("Arial", 12, "bold")).pack(pady=10)
        
        ttk.Label(dialog, text="Número de orden:").pack(pady=5)
        ttk.Entry(dialog, textvariable=orden_id_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Buscar Orden", command=buscar_orden).pack(pady=10)
        
        resultados_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        ttk.Button(dialog, text="Eliminar Orden", command=eliminar_seleccionado,
                  style="Danger.TButton").pack(pady=10)
    
    def eliminar_empleado(self):
        """Muestra una ventana para eliminar un empleado"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Eliminar Empleado")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variable para buscar empleado
        search_var = tk.StringVar()
        resultados_text = scrolledtext.ScrolledText(dialog, height=20, width=70)
        
        def buscar_empleado():
            """Busca empleados"""
            resultados_text.delete(1.0, tk.END)
            empleados = self.taller.empleados.listar_empleados()
            
            if not empleados:
                resultados_text.insert(tk.END, " No hay empleados registrados")
                return
            
            # Filtro por nombre si se especificó
            empleados_filtrados = empleados
            if search_var.get().strip():
                termino = search_var.get().strip().lower()
                empleados_filtrados = [e for e in empleados if termino in e[1].lower()]
            
            if not empleados_filtrados:
                resultados_text.insert(tk.END, f" No se encontraron empleados con '{search_var.get()}'")
                return
            
            # Muestro cada empleado encontrado
            for empleado in empleados_filtrados:
                resultados_text.insert(tk.END, f"\n{'═'*60}\n")
                resultados_text.insert(tk.END, f" ID: {empleado[0]}\n")
                resultados_text.insert(tk.END, f" Nombre: {empleado[1]}\n")
                resultados_text.insert(tk.END, f" Teléfono: {empleado[2]}\n")
                
                # Cuento cuántas órdenes tiene asignadas
                cursor = self.taller.db.execute_query('SELECT COUNT(*) FROM ordenes_trabajo WHERE empleado_id = ?', (empleado[0],))
                cantidad_ordenes = cursor.fetchone()[0]
                resultados_text.insert(tk.END, f" Órdenes asignadas: {cantidad_ordenes}\n")
            
            resultados_text.insert(tk.END, f"\n{'═'*60}\n")
        
        def eliminar_seleccionado():
            """Elimina el empleado seleccionado"""
            try:
                # Pido el ID del empleado a eliminar
                empleado_id_str = simpledialog.askstring("Eliminar Empleado", "Ingrese el ID del empleado a eliminar:")
                if not empleado_id_str:
                    return
                
                empleado_id = int(empleado_id_str)
                
                # Elimino el empleado
                resultado = self.taller.empleados.eliminar_empleado(empleado_id)
                self.show_message(resultado)
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "El ID debe ser un número válido")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Creo los elementos de la ventana
        ttk.Label(dialog, text=" ELIMINAR EMPLEADO", font=("Arial", 12, "bold")).pack(pady=10)
        
        ttk.Label(dialog, text="Buscar empleado por nombre (opcional):").pack(pady=5)
        ttk.Entry(dialog, textvariable=search_var, width=40).pack(pady=5)
        
        ttk.Button(dialog, text="Buscar", command=buscar_empleado).pack(pady=10)
        
        resultados_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        ttk.Button(dialog, text="Eliminar Empleado por ID", command=eliminar_seleccionado,
                  style="Danger.TButton").pack(pady=10)
    
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
        ttk.Label(dialog, text=" RECORDATORIOS INTELIGENTES MEJORADOS", 
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
            listbox_servicios.insert(tk.END, f" {servicio}")
        
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
        tk.Button(frame_botones, text=" Analizar Servicio", command=analizar_servicio,
                 bg="#3498db", fg="white", padx=15, pady=10, font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10)
        
        tk.Button(frame_botones, text=" Todos los Recordatorios", command=mostrar_todos_recordatorios,
                 bg="#9b59b6", fg="white", padx=15, pady=10, font=("Arial", 10, "bold")).grid(row=0, column=1, padx=10)
        
        tk.Button(frame_botones, text=" Reporte Analítico", command=generar_reporte_analitico,
                 bg="#2ecc71", fg="white", padx=15, pady=10, font=("Arial", 10, "bold")).grid(row=0, column=2, padx=10)
        
        # Información adicional
        ttk.Label(dialog, 
                 text=" La predicción considera: historial del vehículo, kilometraje mensual, marca y tipo de servicio",
                 font=("Arial", 9)).pack(pady=10)
    
    def mostrar_resultados_recordatorios_mejorados(self, recordatorios, tipo_servicio, margen_dias):
        """Muestra los resultados de los recordatorios mejorados"""
        self.clear_results()
        
        self.result_text.insert(tk.END, f"\n{'='*80}\n")
        self.result_text.insert(tk.END, f" RECORDATORIOS INTELIGENTES - {tipo_servicio.upper()}\n")
        self.result_text.insert(tk.END, f" Margen de predicción: {margen_dias} días\n")
        self.result_text.insert(tk.END, f" Método: Predicción multivariable (historial + kilometraje + marca)\n")
        self.result_text.insert(tk.END, f"{'='*80}\n\n")
        
        if not recordatorios:
            self.result_text.insert(tk.END, f" No hay vehículos que necesiten '{tipo_servicio}' en los próximos {margen_dias} días\n")
            self.result_text.insert(tk.END, f" ¡Excelente! Los mantenimientos están al día.\n")
            return
        
        # Mostrar estadísticas generales
        total_vehiculos = len(recordatorios)
        vencidos = sum(1 for r in recordatorios if r['dias_restantes'] < 0)
        esta_semana = sum(1 for r in recordatorios if 0 <= r['dias_restantes'] <= 7)
        este_mes = sum(1 for r in recordatorios if 8 <= r['dias_restantes'] <= 30)
        
        self.result_text.insert(tk.END, f" ESTADÍSTICAS:\n")
        self.result_text.insert(tk.END, f"   • Total de vehículos: {total_vehiculos}\n")
        self.result_text.insert(tk.END, f"   • Vencidos: {vencidos}\n")
        self.result_text.insert(tk.END, f"   • Esta semana: {esta_semana}\n")
        self.result_text.insert(tk.END, f"   • Este mes: {este_mes}\n")
        self.result_text.insert(tk.END, f"   • Confiabilidad promedio: {np.mean([r['confiabilidad'] for r in recordatorios]):.1f}%\n")
        self.result_text.insert(tk.END, "\n")
        
        # Mostrar cada recordatorio con formato mejorado
        self.result_text.insert(tk.END, f" VEHÍCULOS PRÓXIMOS A '{tipo_servicio.upper()}':\n\n")
        
        for i, recordatorio in enumerate(recordatorios, 1):
            # Determinar color según confiabilidad
            color_tag = "high_conf" if recordatorio['confiabilidad'] >= 80 else \
                       "medium_conf" if recordatorio['confiabilidad'] >= 60 else \
                       "low_conf"
            
            # Determinar ícono de urgencia
            if recordatorio['dias_restantes'] < 0:
                icono = "Alta urgencia"  # Vencido - ALTA URGENCIA
            elif recordatorio['dias_restantes'] <= 7:
                icono = "Urgencia media"   # Esta semana - Urgencia media
            elif recordatorio['dias_restantes'] <= 14:
                icono = "Próximas 2 semanas"   # Próximas 2 semanas
            else:
                icono = "Este mes"   # Este mes
            
            # Configurar etiquetas de color
            self.result_text.tag_configure("high_conf", foreground="#27ae60")  # Verde
            self.result_text.tag_configure("medium_conf", foreground="#f39c12")  # Naranja
            self.result_text.tag_configure("low_conf", foreground="#e74c3c")  # Rojo
            
            # Insertar información del vehículo
            self.result_text.insert(tk.END, f"{icono} {i}. {recordatorio['marca']} {recordatorio['modelo']} - {recordatorio['placa']}\n")
            
            # Información del cliente
            self.result_text.insert(tk.END, f"    Cliente: {recordatorio['cliente']}\n")
            if recordatorio['telefono']:
                self.result_text.insert(tk.END, f"    Teléfono: {recordatorio['telefono']}\n")
            
            # Historial
            self.result_text.insert(tk.END, f"    Último servicio: {recordatorio['ultimo_servicio']}\n")
            self.result_text.insert(tk.END, f"     Kilometraje actual: {recordatorio['km_ultimo']:.0f} km\n")
            
            # Predicción
            self.result_text.insert(tk.END, f"    Próximo estimado: {recordatorio['proximo_estimado']}\n")
            self.result_text.insert(tk.END, f"    Próximo por km: {recordatorio['proximo_km']}\n")
            
            # Estadísticas y métricas
            self.result_text.insert(tk.END, f"    Días restantes: {recordatorio['dias_restantes']}\n")
            self.result_text.insert(tk.END, f"    Km/mes promedio: {recordatorio['km_mensual_promedio']:.0f} km\n")
            self.result_text.insert(tk.END, f"    Método: {recordatorio['metodo_prediccion']}\n")
            
            # Confiabilidad con color
            confiabilidad_text = f"    Confiabilidad: {recordatorio['confiabilidad']:.1f}%\n"
            start_pos = self.result_text.index(tk.END)
            self.result_text.insert(tk.END, confiabilidad_text)
            end_pos = self.result_text.index(tk.END)
            self.result_text.tag_add(color_tag, f"{start_pos} linestart", f"{end_pos} linestart - 1 line")
            
            # Prioridad
            self.result_text.insert(tk.END, f"    Prioridad: {recordatorio['prioridad']:.1f}/100\n")
            
            # Recomendación según urgencia
            if recordatorio['dias_restantes'] < 0:
                recomendacion = " CONTACTO INMEDIATO - Servicio vencido"
            elif recordatorio['dias_restantes'] <= 7:
                recomendacion = " Contactar esta semana"
            elif recordatorio['dias_restantes'] <= 14:
                recomendacion = " Contactar en 2 semanas"
            elif recordatorio['dias_restantes'] <= 30:
                recomendacion = "  Contactar este mes"
            else:
                recomendacion = " Programar para más adelante"
            
            self.result_text.insert(tk.END, f"    Recomendación: {recomendacion}\n")
            self.result_text.insert(tk.END, "   " + "─" * 60 + "\n\n")
        
        # Recomendaciones generales
        self.result_text.insert(tk.END, f"\n RECOMENDACIONES GENERALES:\n")
        if vencidos > 0:
            self.result_text.insert(tk.END, f"   • Contactar inmediatamente a los {vencidos} cliente(s) con servicios vencidos\n")
        if esta_semana > 0:
            self.result_text.insert(tk.END, f"   • Programar citas para los {esta_semana} cliente(s) de esta semana\n")
        if este_mes > 0:
            self.result_text.insert(tk.END, f"   • Enviar recordatorios a los {este_mes} cliente(s) de este mes\n")
        
        self.result_text.insert(tk.END, f"\n La confiabilidad indica qué tan precisa es la predicción:\n")
        self.result_text.insert(tk.END, f"   •  <60%: Basada en pocos datos históricos\n")
        self.result_text.insert(tk.END, f"   •  60-79%: Basada en datos moderados\n")
        self.result_text.insert(tk.END, f"   •  80-100%: Basada en historial extenso y consistente\n")
    
    def mostrar_todos_recordatorios_resultados(self, todos_recordatorios, margen_dias):
        """Muestra todos los recordatorios agrupados por tipo de servicio"""
        self.clear_results()
        
        self.result_text.insert(tk.END, f"\n{'='*80}\n")
        self.result_text.insert(tk.END, " TODOS LOS RECORDATORIOS - VISTA GENERAL\n")
        self.result_text.insert(tk.END, f" Margen: {margen_dias} días\n")
        self.result_text.insert(tk.END, f"{'='*80}\n\n")
        
        if not todos_recordatorios:
            self.result_text.insert(tk.END, " No hay recordatorios pendientes en el período seleccionado\n")
            return
        
        # Agrupar por tipo de servicio
        recordatorios_por_servicio = {}
        for recordatorio in todos_recordatorios:
            servicio = recordatorio['tipo_servicio']
            if servicio not in recordatorios_por_servicio:
                recordatorios_por_servicio[servicio] = []
            recordatorios_por_servicio[servicio].append(recordatorio)
        
        # Mostrar resumen por servicio
        self.result_text.insert(tk.END, " RESUMEN POR TIPO DE SERVICIO:\n\n")
        
        for servicio, recordatorios in recordatorios_por_servicio.items():
            total = len(recordatorios)
            vencidos = sum(1 for r in recordatorios if r['dias_restantes'] < 0)
            conf_promedio = np.mean([r['confiabilidad'] for r in recordatorios])
            
            self.result_text.insert(tk.END, f" {servicio}:\n")
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
        self.result_text.insert(tk.END, f"\n TOP 10 MÁS URGENTES:\n\n")
        
        top_10_urgentes = sorted(todos_recordatorios, key=lambda x: x['dias_restantes'])[:10]
        
        for i, recordatorio in enumerate(top_10_urgentes, 1):
            icono = "Alerta" if recordatorio['dias_restantes'] < 0 else "Peligro"
            self.result_text.insert(tk.END, f"{icono} {i}. {recordatorio['placa']} - {recordatorio['marca']} {recordatorio['modelo']}\n")
            self.result_text.insert(tk.END, f"    {recordatorio['cliente']}\n")
            self.result_text.insert(tk.END, f"    {recordatorio['tipo_servicio']}\n")
            self.result_text.insert(tk.END, f"    {recordatorio['proximo_estimado']} ({recordatorio['dias_restantes']} días)\n")
            self.result_text.insert(tk.END, f"    Conf: {recordatorio['confiabilidad']:.1f}%\n")
            self.result_text.insert(tk.END, "   " + "─" * 50 + "\n")
        
        # Estadísticas generales
        total_vehiculos = len(todos_recordatorios)
        total_vencidos = sum(1 for r in todos_recordatorios if r['dias_restantes'] < 0)
        conf_general = np.mean([r['confiabilidad'] for r in todos_recordatorios])
        
        self.result_text.insert(tk.END, f"\n ESTADÍSTICAS GLOBALES:\n")
        self.result_text.insert(tk.END, f"   • Total de recordatorios: {total_vehiculos}\n")
        self.result_text.insert(tk.END, f"   • Servicios vencidos: {total_vencidos}\n")
        self.result_text.insert(tk.END, f"   • Confiabilidad general: {conf_general:.1f}%\n")
        self.result_text.insert(tk.END, f"   • Tipos de servicio: {len(recordatorios_por_servicio)}\n")
        
        # Recomendaciones de acción
        self.result_text.insert(tk.END, f"\n PLAN DE ACCIÓN RECOMENDADO:\n")
        
        if total_vencidos > 0:
            self.result_text.insert(tk.END, f"   1.  Contactar inmediatamente a los {total_vencidos} clientes con servicios vencidos\n")
        
        servicios_con_vencidos = [s for s, r in recordatorios_por_servicio.items() 
                                 if any(rec['dias_restantes'] < 0 for rec in r)]
        
        if servicios_con_vencidos:
            self.result_text.insert(tk.END, f"   2.  Priorizar servicios: {', '.join(servicios_con_vencidos)}\n")
        
        self.result_text.insert(tk.END, f"   3.   Programar citas con al menos 7 días de anticipación\n")
        self.result_text.insert(tk.END, f"   4.  Revisar confiabilidad antes de contactar\n")
    
    def mostrar_reporte_analitico(self, reporte, tipo_servicio):
        """Muestra un reporte analítico detallado"""
        self.clear_results()
        
        self.result_text.insert(tk.END, f"\n{'='*80}\n")
        self.result_text.insert(tk.END, f" REPORTE ANALÍTICO - {tipo_servicio.upper()}\n")
        self.result_text.insert(tk.END, f"{'='*80}\n\n")
        
        if reporte['total_vehiculos'] == 0:
            self.result_text.insert(tk.END, f" No hay vehículos con historial de '{tipo_servicio}'\n")
            self.result_text.insert(tk.END, f" El sistema no puede generar predicciones sin datos históricos\n")
            return
        
        # Información general
        self.result_text.insert(tk.END, " INFORMACIÓN GENERAL:\n")
        self.result_text.insert(tk.END, f"   • Total de vehículos analizados: {reporte['total_vehiculos']}\n")
        self.result_text.insert(tk.END, f"   • Días promedio para próximo servicio: {reporte['promedio_dias_restantes']:.1f}\n")
        self.result_text.insert(tk.END, f"   • Confiabilidad promedio: {reporte['promedio_confiabilidad']:.1f}%\n")
        self.result_text.insert(tk.END, "\n")
        
        # Distribución por urgencia
        self.result_text.insert(tk.END, " DISTRIBUCIÓN POR URGENCIA:\n")
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
            self.result_text.insert(tk.END, " PREDICCIÓN MÁS CONFIABLE:\n")
            self.result_text.insert(tk.END, f"   • Vehículo: {confiable['marca']} {confiable['modelo']} - {confiable['placa']}\n")
            self.result_text.insert(tk.END, f"   • Cliente: {confiable['cliente']}\n")
            self.result_text.insert(tk.END, f"   • Confiabilidad: {confiable['confiabilidad']:.1f}%\n")
            self.result_text.insert(tk.END, f"   • Próximo servicio: {confiable['proximo_estimado']}\n")
            self.result_text.insert(tk.END, f"   • Días restantes: {confiable['dias_restantes']}\n")
            self.result_text.insert(tk.END, "\n")
        
        # Predicción más urgente
        if reporte['prediccion_mas_urgente']:
            urgente = reporte['prediccion_mas_urgente']
            self.result_text.insert(tk.END, "  PREDICCIÓN MÁS URGENTE:\n")
            self.result_text.insert(tk.END, f"   • Vehículo: {urgente['marca']} {urgente['modelo']} - {urgente['placa']}\n")
            self.result_text.insert(tk.END, f"   • Cliente: {urgente['cliente']}\n")
            self.result_text.insert(tk.END, f"   • Días restantes: {urgente['dias_restantes']}\n")
            self.result_text.insert(tk.END, f"   • Confiabilidad: {urgente['confiabilidad']:.1f}%\n")
            self.result_text.insert(tk.END, f"   • Próximo servicio: {urgente['proximo_estimado']}\n")
            self.result_text.insert(tk.END, "\n")
        
        # Análisis de calidad de datos
        self.result_text.insert(tk.END, " ANÁLISIS DE CALIDAD DE DATOS:\n")
        
        if reporte['promedio_confiabilidad'] >= 80:
            self.result_text.insert(tk.END, "   •  EXCELENTE - Los datos históricos son extensos y consistentes\n")
            self.result_text.insert(tk.END, "   • Las predicciones son muy confiables\n")
        elif reporte['promedio_confiabilidad'] >= 60:
            self.result_text.insert(tk.END, "   •  BUENA - Datos suficientes para predicciones aceptables\n")
            self.result_text.insert(tk.END, "   • Se recomienda validar con el cliente\n")
        else:
            self.result_text.insert(tk.END, "   •  LIMITADA - Pocos datos históricos disponibles\n")
            self.result_text.insert(tk.END, "   • Las predicciones son estimaciones básicas\n")
        
        # Recomendaciones de negocio
        self.result_text.insert(tk.END, "\n RECOMENDACIONES DE NEGOCIO:\n")
        
        if categorias['vencidos'] > 0:
            self.result_text.insert(tk.END, f"   1.  Contactar URGENTEMENTE a los {categorias['vencidos']} clientes con servicios vencidos\n")
            self.result_text.insert(tk.END, f"      • Ofrecer descuento por retraso\n")
            self.result_text.insert(tk.END, f"      • Programar cita inmediata\n")
        
        if categorias['esta_semana'] > 0:
            self.result_text.insert(tk.END, f"   2.  Llamar a los {categorias['esta_semana']} clientes de esta semana\n")
            self.result_text.insert(tk.END, f"      • Confirmar disponibilidad\n")
            self.result_text.insert(tk.END, f"      • Ofrecer horarios convenientes\n")
        
        if categorias['proximas_2_semanas'] + categorias['este_mes'] > 0:
            total_proximos = categorias['proximas_2_semanas'] + categorias['este_mes']
            self.result_text.insert(tk.END, f"   3.  Enviar recordatorios a los {total_proximos} clientes del mes\n")
            self.result_text.insert(tk.END, f"      • Email o mensaje de texto\n")
            self.result_text.insert(tk.END, f"      • Incluir opción para agendar online\n")
        
        # Sugerencias para mejorar datos
        self.result_text.insert(tk.END, "\n PARA MEJORAR LAS PREDICCIONES:\n")
        self.result_text.insert(tk.END, f"   • Registrar siempre el kilometraje en cada orden\n")
        self.result_text.insert(tk.END, f"   • Especificar claramente el tipo de servicio\n")
        self.result_text.insert(tk.END, f"   • Actualizar datos de contacto de clientes\n")
    
    def salir(self):
        """Cierra el programa"""
        if messagebox.askyesno("Salir", "¿Está seguro que desea salir del sistema?"):
            self.root.destroy()

# INICIO DEL PROGRAMA

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