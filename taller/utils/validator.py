from datetime import datetime, timedelta
from typing import Optional

class Validator:
    """Esta clase valida que los datos ingresados sean correctos"""
    
    @staticmethod
    def validar_numero(valor: str, tipo: str = "entero") -> Optional[float]:
        """Valida que un valor sea un número"""
        try:
            if not valor.strip():
                return None
            if tipo == "entero":
                return int(valor)
            elif tipo == "decimal":
                return float(valor)
            else:
                return valor
        except ValueError:
            return None
    
    @staticmethod
    def validar_telefono(telefono: str) -> Optional[str]:
        """Valida que un teléfono tenga solo números y longitud correcta"""
        if telefono is None or telefono.strip() == "":
            return None
        
        # Quito todo lo que no sea número
        telefono_limpio = ''.join(filter(str.isdigit, telefono))
        
        # El teléfono debe tener entre 7 y 15 dígitos
        if len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
            return None
        
        return telefono_limpio
    
    @staticmethod
    def validar_nit(nit: str) -> Optional[str]:
        """Valida que el NIT tenga formato correcto"""
        if nit is None or nit.strip() == "":
            return None
        
        # Permito números, letras, guiones y espacios
        nit_limpio = ''.join(filter(lambda c: c.isalnum() or c in '- ', nit))
        
        # El NIT debe tener entre 3 y 20 caracteres
        if len(nit_limpio) < 3 or len(nit_limpio) > 20:
            return None
        
        return nit_limpio
    
    @staticmethod
    def validar_fecha(fecha_str: str, permitir_futuro: bool = True, permitir_pasado: bool = True) -> Optional[datetime.date]:
        """Valida que una fecha sea correcta"""
        try:
            if not fecha_str.strip():
                return None
                
            # Si es un número, lo interpreto como días desde hoy
            if fecha_str.isdigit():
                dias = int(fecha_str)
                fecha = datetime.now() + timedelta(days=dias)
            else:
                # Si es texto, lo convierto a fecha
                # Intentar diferentes formatos
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y'):
                    try:
                        fecha = datetime.strptime(fecha_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return None
            
            hoy = datetime.now().date()
            fecha_date = fecha.date()
            
            # La fecha debe ser razonable (después del año 2000)
            if fecha_date < datetime(2000, 1, 1).date():
                return None
            
            # No permito fechas muy futuras (más de 1 año)
            if fecha_date > hoy + timedelta(days=365):
                return None
                
            # Validaciones adicionales según parámetros
            if not permitir_futuro and fecha_date > hoy:
                return None
                
            if not permitir_pasado and fecha_date < hoy:
                return None
            
            return fecha_date
            
        except ValueError:
            return None
    
    @staticmethod
    def validar_año_vehiculo(año: int) -> bool:
        """Valida que el año del vehículo sea razonable"""
        año_actual = datetime.now().year
        # El año debe estar entre 1900 y el año actual + 2
        return 1900 <= año <= año_actual + 2