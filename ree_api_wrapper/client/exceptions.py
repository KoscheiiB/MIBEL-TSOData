class REEAPIError(Exception):
    """Base exception for REE API errors"""
    def __init__(self, message: str, status_code: int = None, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

class REEConnectionError(REEAPIError):
    """Connection-related errors"""
    pass

class REEValidationError(REEAPIError):
    """Input validation errors"""
    pass

class REEDataError(REEAPIError):
    """Data processing errors"""
    pass