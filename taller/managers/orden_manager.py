import sqlite3
from taller.database.database_manager import DatabaseManager
from taller.utils.validator import Validator
from typing import Optional, Dict, List

class OrdenManager:
    """Gestiona todo lo relacionado con órdenes de trabajo"""
    
    def __init__(self, db_manager: DatabaseManager, validator: Validator):
        self.db = db_manager
        self.validator = validator
    
    def orden_existe(self, orden_id: int) -> bool:
        """Verifica si una orden existe"""
        cursor = self.db.execute_query('SELECT id FROM ordenes_trabajo WHERE id = ?', (orden_id,))
        return cursor.fetchone() is not None
    
    def _calcular_precio_final(self,
                           costo_repuestos: float,
                           costo_mano_obra: float) -> float:
         return costo_repuestos + costo_mano_obra
    
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
                     descripcion_trabajo: str, tipo_servicio: str, servicios: List[int], horas_trabajadas: float,
                     costo_repuestos: float, costo_mano_obra: float, kilometraje: float,
                     unidad_kilometraje: str = 'km', fecha_fin: Optional[str] = None) -> str:
        """Agrega una nueva orden de trabajo"""
        
        # Valido la fecha de finalización
        if not fecha_fin:
            return " Error: La fecha de finalización es obligatoria."
        
        fecha_fin_validada = self.validator.validar_fecha(fecha_fin, permitir_futuro=False, permitir_pasado=True)
        if fecha_fin_validada is None:
            return " Error: Fecha de finalización inválida. Debe ser una fecha pasada o presente válida."
        
        # Calculo el precio total
        precio_final = self._calcular_precio_final(costo_repuestos, costo_mano_obra)
        
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
            for servicio_id in servicios:
                self.db.execute_query(
                    '''
                    INSERT INTO orden_servicios
                    (orden_id, servicio_id)
                    VALUES (?, ?)
                    ''',
                    (
                        numero_orden,
                        servicio_id
                    )
                )
            self.db.commit()
            return f" Orden #{numero_orden} agregada - Total: Q{precio_final:.2f} - Fecha: {fecha_fin_validada}"
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                return f" Error: La orden #{numero_orden} ya existe."
            return f" Error al agregar orden: {e}"
    
    def editar_orden(self, orden_id: int, descripcion_trabajo: str, tipo_servicio: str, 
                    horas_trabajadas: float, costo_repuestos: float, costo_mano_obra: float,
                    precio_final: float, kilometraje: float, unidad_kilometraje: str,
                    fecha_fin: str) -> str:
        """Edita una orden de trabajo existente"""
        try:
            # Valido la fecha de finalización
            fecha_fin_validada = self.validator.validar_fecha(fecha_fin, permitir_futuro=False, permitir_pasado=True)
            if fecha_fin_validada is None:
                return " Error: Fecha de finalización inválida. Debe ser una fecha pasada o presente válida."
            
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
            return f" Orden #{orden_id} actualizada correctamente"
        except Exception as e:
            return f" Error al editar orden: {e}"
    
    def eliminar_orden(self, orden_id: int) -> str:
        """Elimina una orden de trabajo"""
        try:
            # Verifico si la orden existe
            if not self.orden_existe(orden_id):
                return " Error: La orden no existe"
            
            # Obtengo información de la orden antes de eliminarla
            detalles = self.obtener_detalles_orden(orden_id)
            if not detalles:
                return " Error: No se pudieron obtener los detalles de la orden"
            
            # Elimino la orden
            self.db.execute_query('DELETE FROM ordenes_trabajo WHERE id = ?', (orden_id,))
            self.db.commit()
            
            return (f" Orden #{orden_id} eliminada exitosamente.\n"
                   f"   Cliente: {detalles['cliente_nombre']}\n"
                   f"   Vehículo: {detalles['vehiculo_marca']} {detalles['vehiculo_modelo']}\n"
                   f"   Total reembolsado: Q{detalles['precio_final']:.2f}")
            
        except sqlite3.Error as e:
            self.db.rollback()
            return f" Error al eliminar orden: {e}"