"""Service-layer error carrying a machine code, surfaced via the DRF envelope."""


class ServiceError(Exception):
    def __init__(self, message, code="service_error", status=400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
