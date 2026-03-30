class DatabaseException(Exception):
    def __init__(self, message: str = "Error en la base de datos", details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

    def __str__(self):
        return f"Error de validación en '{self.field}': {self.message}"


class ResourceNotFoundError(Exception):
    def __init__(self, resource: str, identifier):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} con ID {identifier} no encontrado")

    def __str__(self):
        return f"{self.resource} con ID {self.identifier} no encontrado"


class DuplicateResourceError(Exception):
    def __init__(self, resource: str, identifier):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} '{identifier}' ya existe")

    def __str__(self):
        return f"{self.resource} '{self.identifier}' ya existe"


class ConfigurationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Error de configuración: {message}")
