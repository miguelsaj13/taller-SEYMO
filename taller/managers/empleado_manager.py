import sqlite3
from tkinter import messagebox
from taller.database.database_manager import DatabaseManager
from taller.utils.validator import Validator
from typing import List, Tuple

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
            return f" Empleado '{nombre}' agregado (ID: {cursor.lastrowid})"
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
            return f" Empleado ID {empleado_id} actualizado"
        except sqlite3.IntegrityError:
            return " Error: Ya existe un empleado con ese teléfono"
    
    def eliminar_empleado(self, empleado_id: int) -> str:
        """Elimina un empleado"""
        try:
            # Verifico si el empleado existe
            if not self.empleado_existe(empleado_id):
                return " Error: El empleado no existe"
            
            # Obtengo información del empleado antes de eliminarlo
            cursor = self.db.execute_query('SELECT nombre, telefono FROM empleados WHERE id = ?', (empleado_id,))
            empleado_info = cursor.fetchone()
            
            # Cuento cuántas órdenes tiene asignadas el empleado
            cursor = self.db.execute_query('SELECT COUNT(*) FROM ordenes_trabajo WHERE empleado_id = ?', (empleado_id,))
            cantidad_ordenes = cursor.fetchone()[0]
            
            # Pido confirmación
            confirmacion = messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Está seguro de eliminar al empleado '{empleado_info[0]}'?\n\n"
                f"Teléfono: {empleado_info[1]}\n"
                f"Órdenes asignadas: {cantidad_ordenes}\n\n"
                f" Esta acción NO se puede deshacer.\n"
                f"Nota: Las órdenes asignadas a este empleado quedarán sin empleado asignado."
            )
            
            if not confirmacion:
                return " Eliminación cancelada por el usuario"
            
            # Primero actualizo las órdenes para que no tengan empleado asignado
            self.db.execute_query('UPDATE ordenes_trabajo SET empleado_id = NULL WHERE empleado_id = ?', (empleado_id,))
            
            # Luego elimino el empleado
            self.db.execute_query('DELETE FROM empleados WHERE id = ?', (empleado_id,))
            self.db.commit()
            
            return (f" Empleado '{empleado_info[0]}' eliminado exitosamente.\n"
                   f"   Se actualizaron {cantidad_ordenes} órdenes para quitar la asignación.")
            
        except sqlite3.Error as e:
            self.db.conn.rollback()
            return f" Error al eliminar empleado: {e}"