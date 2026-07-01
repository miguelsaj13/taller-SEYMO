from typing import List, Dict, Optional
import sqlite3
from taller.database.database_manager import DatabaseManager

class ServicioManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _normalizar_nombre(self, nombre: str) -> str:
        """
        Limpia el nombre del servicio antes de guardarlo.
        Elimina espacios al inicio/final y espacios repetidos.
        """

        # Eliminar espacios al inicio y al final
        nombre = nombre.strip()

        # Eliminar espacios dobles
        nombre = " ".join(nombre.split())

        return nombre
    

    def listar_servicios(self) -> List[Dict]:
        """
        Obtiene todos los servicios activos ordenados alfabéticamente.
        Devuelve una lista de diccionarios.
        """

        cursor = self.db.execute_query(
            '''
            SELECT id, nombre
            FROM servicios
            WHERE activo = 1
            ORDER BY nombre
            '''
        )

        return [
            {
                "id": fila[0],
                "nombre": fila[1]
            }
            for fila in cursor.fetchall()
        ]
    
    def servicio_existe(self, nombre: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si ya existe un servicio con ese nombre.
        Si excluir_id se proporciona, ignora ese servicio durante la búsqueda.
        """

        nombre = self._normalizar_nombre(nombre)

        if excluir_id is None:

            cursor = self.db.execute_query(
                '''
                SELECT id
                FROM servicios
                WHERE LOWER(nombre) = LOWER(?)
                ''',
                (nombre,)
            )
        
        else:
            
            cursor = self.db.execute_query(
                '''
                SELECT id
                FROM servicios
                WHERE LOWER(nombre) = LOWER(?)
                AND id != ?
                ''',
                (nombre, excluir_id)
            )

        return cursor.fetchone() is not None
    
    def agregar_servicio(self, nombre: str) -> int:
        """
        Agrega un nuevo servicio al catálogo.
        Devuelve el ID del servicio creado.
        """

        # Normalizar el nombre
        nombre = self._normalizar_nombre(nombre)

        # Verificar que no esté vacío
        if not nombre:
            raise ValueError("El nombre del servicio no puede estar vacío.")

        # Verificar que no exista
        if self.servicio_existe(nombre):
            raise ValueError("Ese servicio ya existe.")

        try:

            cursor = self.db.execute_query(
                '''
                INSERT INTO servicios(nombre)
                VALUES (?)
                ''',
                (nombre,)
            )

            self.db.commit()

            return cursor.lastrowid

        except sqlite3.Error:
            self.db.rollback()
            raise

    def editar_servicio(self, servicio_id: int, nuevo_nombre: str) -> bool:
        """
        Edita el nombre de un servicio existente.
        """

        # Normalizar el nombre
        nuevo_nombre = self._normalizar_nombre(nuevo_nombre)

        # Verificar que no esté vacío
        if not nuevo_nombre:
            raise ValueError("El nombre del servicio no puede estar vacío.")

        # Verificar que el servicio exista
        cursor = self.db.execute_query(
            '''
            SELECT id
            FROM servicios
            WHERE id = ?
            ''',
            (servicio_id,)
        )

        if cursor.fetchone() is None:
            raise ValueError("El servicio no existe.")

        # Verificar que no exista otro servicio con ese nombre
        if self.servicio_existe(
            nuevo_nombre,
            excluir_id=servicio_id
        ):
            raise ValueError("Ya existe otro servicio con ese nombre.")

        try:

            self.db.execute_query(
                '''
                UPDATE servicios
                SET nombre = ?
                WHERE id = ?
                ''',
                (nuevo_nombre, servicio_id)
            )

            self.db.commit()

            return True

        except sqlite3.Error:
            self.db.rollback()
            raise