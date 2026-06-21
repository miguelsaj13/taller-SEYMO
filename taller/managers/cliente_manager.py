import sqlite3
from tkinter import messagebox
from taller.database.database_manager import DatabaseManager
from taller.utils.validator import Validator
from typing import Optional, Dict, List, Tuple

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
            print(f" Cliente '{nombre}' agregado con ID: {cursor.lastrowid}")
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
            return f" Cliente ID {cliente_id} actualizado"
        except sqlite3.IntegrityError as e:
            if "telefono" in str(e):
                return " Error: Ya existe un cliente con ese teléfono"
            elif "nit" in str(e):
                return " Error: Ya existe un cliente con ese NIT"
            else:
                return " Error en la base de datos"
    
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
        
        # Obtengo las órdenes de trabajo de los vehículos del cliente
        cursor = self.db.execute_query('''
            SELECT o.id, o.fecha_fin, o.tipo_servicio, o.precio_final,
                   v.marca, v.modelo, v.placa
            FROM ordenes_trabajo o
            JOIN vehiculos v ON o.vehiculo_id = v.id
            WHERE v.cliente_id = ?
            ORDER BY o.fecha_fin DESC
            LIMIT 10
        ''', (cliente_id,))
        ordenes_recientes = cursor.fetchall()
        
        return {
            'cliente': cliente_info,
            'vehiculos': vehiculos,
            'ordenes_recientes': ordenes_recientes
        }
    
    def nit_existe(self, nit: str) -> bool:
        """Verifica si un NIT ya existe"""
        if not nit:
            return False
        cursor = self.db.execute_query('SELECT id FROM clientes WHERE nit = ?', (nit,))
        return cursor.fetchone() is not None
    
    def eliminar_cliente(self, cliente_id: int) -> str:
        """Elimina un cliente y todos sus vehículos y órdenes relacionadas"""
        try:
            # Primero verifico si el cliente existe
            if not self.cliente_existe(cliente_id):
                return " Error: El cliente no existe"
            
            # Obtengo información del cliente antes de eliminarlo
            cursor = self.db.execute_query('SELECT nombre FROM clientes WHERE id = ?', (cliente_id,))
            cliente_info = cursor.fetchone()
            nombre_cliente = cliente_info[0] if cliente_info else "Desconocido"
            
            # Cuento cuántos vehículos tiene el cliente
            cursor = self.db.execute_query('SELECT COUNT(*) FROM vehiculos WHERE cliente_id = ?', (cliente_id,))
            cantidad_vehiculos = cursor.fetchone()[0]
            
            # Cuento cuántas órdenes tienen los vehículos de este cliente
            cursor = self.db.execute_query('''
                SELECT COUNT(*) FROM ordenes_trabajo 
                WHERE vehiculo_id IN (SELECT id FROM vehiculos WHERE cliente_id = ?)
            ''', (cliente_id,))
            cantidad_ordenes = cursor.fetchone()[0]
            
            # Pido confirmación
            confirmacion = messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Está seguro de eliminar al cliente '{nombre_cliente}'?\n\n"
                f"Se eliminarán:\n"
                f"• El cliente: {nombre_cliente}\n"
                f"• Vehículos: {cantidad_vehiculos}\n"
                f"• Órdenes de trabajo: {cantidad_ordenes}\n\n"
                f" Esta acción NO se puede deshacer."
            )
            
            if not confirmacion:
                return " Eliminación cancelada por el usuario"
            
            # Elimino el cliente (las claves foráneas eliminarán en cascada)
            self.db.execute_query('DELETE FROM clientes WHERE id = ?', (cliente_id,))
            self.db.commit()
            
            return (f" Cliente '{nombre_cliente}' eliminado exitosamente.\n"
                   f"   Se eliminaron {cantidad_vehiculos} vehículos y {cantidad_ordenes} órdenes de trabajo.")
            
        except sqlite3.Error as e:
            self.db.conn.rollback()
            return f" Error al eliminar cliente: {e}"