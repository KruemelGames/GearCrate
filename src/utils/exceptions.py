"""
Custom exception classes for GearCrate
Provides specific exception types for better error handling
"""


class GearCrateException(Exception):
    """Base exception for all GearCrate-specific errors"""
    pass


class DatabaseError(GearCrateException):
    """Database operation failed"""
    pass


class CacheError(GearCrateException):
    """Cache operation failed"""
    pass


class ScraperError(GearCrateException):
    """Web scraping operation failed"""
    pass


class ConfigError(GearCrateException):
    """Configuration file error"""
    pass


class ImageProcessingError(GearCrateException):
    """Image processing or manipulation failed"""
    pass


class ItemNotFoundError(DatabaseError):
    """Requested item not found in database"""
    pass


class ItemAlreadyExistsError(DatabaseError):
    """Item with this name already exists"""
    pass
