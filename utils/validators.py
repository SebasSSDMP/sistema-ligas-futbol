import re
from datetime import datetime
from typing import Optional
from core.exceptions import ValidationError


def validar_nombre_texto(valor: str, campo: str, min_long: int = 2, max_long: int = 100) -> str:
    if not valor or not valor.strip():
        raise ValidationError(campo, "No puede estar vacío")
    
    valor = valor.strip()
    
    if len(valor) < min_long:
        raise ValidationError(campo, f"Debe tener al menos {min_long} caracteres")
    
    if len(valor) > max_long:
        raise ValidationError(campo, f"Debe tener máximo {max_long} caracteres")
    
    return valor


def validar_fecha(valor: str, campo: str, formato: str = "%Y-%m-%d") -> datetime:
    if not valor or not valor.strip():
        raise ValidationError(campo, "No puede estar vacía")
    
    try:
        return datetime.strptime(valor.strip(), formato)
    except ValueError:
        raise ValidationError(campo, f"Formato inválido. Use {formato}")


def validar_fecha_opcional(valor: Optional[str], campo: str, formato: str = "%Y-%m-%d") -> Optional[datetime]:
    if not valor or not valor.strip():
        return None
    
    try:
        return datetime.strptime(valor.strip(), formato)
    except ValueError:
        raise ValidationError(campo, f"Formato inválido. Use {formato}")


def validar_numero(valor: any, campo: str, min_val: int = None, max_val: int = None) -> int:
    try:
        numero = int(valor)
    except (ValueError, TypeError):
        raise ValidationError(campo, "Debe ser un número entero")
    
    if min_val is not None and numero < min_val:
        raise ValidationError(campo, f"Debe ser mayor o igual a {min_val}")
    
    if max_val is not None and numero > max_val:
        raise ValidationError(campo, f"Debe ser menor o igual a {max_val}")
    
    return numero


def validar_id(valor: any, campo: str) -> int:
    return validar_numero(valor, campo, min_val=1)


def validar_pais(valor: str) -> str:
    if not valor or not valor.strip():
        return "Sin especificar"
    return valor.strip()


def validar_texto_opcional(valor: Optional[str], campo: str, max_long: int = 200) -> Optional[str]:
    if not valor or not valor.strip():
        return None
    
    valor = valor.strip()
    
    if len(valor) > max_long:
        raise ValidationError(campo, f"Debe tener máximo {max_long} caracteres")
    
    return valor
