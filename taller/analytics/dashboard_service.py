from taller.database.database_manager import DatabaseManager
from analytics.recordatorios_service import RecordatoriosService
from datetime import datetime
"""
DashboardService

Se encarga de obtener toda la información que la
pantalla principal necesita mostrar.

Su única responsabilidad es proporcionar información
resumida del estado actual del taller.
"""
class DashboardService:

    def __init__(self, db: DatabaseManager, recordatorios_service: RecordatoriosService):
        self.db = db
        self.recordatorios_service = recordatorios_service

    def obtener_ganancia_mes(self):
        """
        Devuelve la ganancia neta del mes actual.
        En este sistema la ganancia neta corresponde
        a la suma de la mano de obra.
        """

        query = '''
            SELECT SUM(costo_mano_obra)
            FROM ordenes_trabajo
            WHERE strftime('%Y-%m', fecha_fin)
                  = strftime('%Y-%m', 'now')
        '''

        cursor = self.db.execute_query(query)
        resultado = cursor.fetchone()

        return resultado[0] if resultado[0] is not None else 0

    def obtener_ordenes_mes(self):
        """
        Devuelve la cantidad de órdenes
        registradas durante el mes actual.
        """

        query = '''
            SELECT COUNT(*)
            FROM ordenes_trabajo
            WHERE strftime('%Y-%m', fecha_fin)
                  = strftime('%Y-%m', 'now')
        '''

        cursor = self.db.execute_query(query)
        resultado = cursor.fetchone()

        return resultado[0] if resultado[0] is not None else 0

    def obtener_servicios_frecuentes(self, limite=5):
        """
        Devuelve los servicios más frecuentes.
        """

        query = '''
            SELECT
                s.nombre,
                COUNT(*) as cantidad
            FROM servicios s
            JOIN orden_servicios os
            ON s.id = os.servicio_id
            GROUP BY s.id
            ORDER BY cantidad DESC
            LIMIT ?
        '''

        cursor = self.db.execute_query(query, (limite,))

        return [
            {
                "servicio": fila[0],
                "cantidad": fila[1]
            }
            for fila in cursor.fetchall()
        ]

    def obtener_recordatorios(self):
        """
        Delega el cálculo de recordatorios
        al servicio especializado.
        """

        return self.recordatorios_service.obtener_todos_recordatorios()

    def obtener_dashboard(self):
        """
        Devuelve toda la información que
        necesita mostrar el dashboard.
        """

        return {
            "ganancia_mes": self.obtener_ganancia_mes(),
            "ordenes_mes": self.obtener_ordenes_mes(),
            "servicios_frecuentes": self.obtener_servicios_frecuentes(),
            "recordatorios": self.obtener_recordatorios(),
            "ultima_actualizacion": datetime.now()
        }