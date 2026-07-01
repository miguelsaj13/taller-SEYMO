import sqlite3
from taller.database.database_manager import DatabaseManager
from taller.utils.validator import Validator
from typing import Optional, Dict, List, Tuple

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
            return f" Vehículo {marca} {modelo} agregado (ID: {cursor.lastrowid})"
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
            SELECT v.marca, v.modelo, v.año, v.placa, v.color, c.nombre, c.telefono, c.nit, c.id as cliente_id
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
            return f" Vehículo ID {vehiculo_id} actualizado"
        except sqlite3.IntegrityError:
            raise Exception("Ya existe un vehículo con esa placa")
    
    def eliminar_vehiculo(self, vehiculo_id: int) -> str:
        """Elimina un vehículo y todas sus órdenes de trabajo"""
        try:
            # Verifico si el vehículo existe
            if not self.vehiculo_existe(vehiculo_id):
                return " Error: El vehículo no existe"
            
            # Obtengo información del vehículo antes de eliminarlo
            cursor = self.db.execute_query('''
                SELECT v.marca, v.modelo, v.placa, c.nombre 
                FROM vehiculos v
                JOIN clientes c ON v.cliente_id = c.id
                WHERE v.id = ?
            ''', (vehiculo_id,))
            vehiculo_info = cursor.fetchone()
            
            if not vehiculo_info:
                return " Error: No se pudo obtener información del vehículo"
            
            marca, modelo, placa, nombre_cliente = vehiculo_info
            
            # Cuento cuántas órdenes tiene el vehículo
            cursor = self.db.execute_query('SELECT COUNT(*) FROM ordenes_trabajo WHERE vehiculo_id = ?', (vehiculo_id,))
            cantidad_ordenes = cursor.fetchone()[0]
            
            # Elimino el vehículo (las claves foráneas eliminarán las órdenes en cascada)
            self.db.execute_query('DELETE FROM vehiculos WHERE id = ?', (vehiculo_id,))
            self.db.commit()
            
            return (f" Vehículo {marca} {modelo} - {placa} eliminado exitosamente.\n"
                   f"   Se eliminaron {cantidad_ordenes} órdenes de trabajo asociadas.")
            
        except sqlite3.Error as e:
            self.db.rollback()
            return f" Error al eliminar vehículo: {e}"