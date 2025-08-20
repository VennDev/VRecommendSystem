from pydantic import BaseModel


class BaseSchema(BaseModel):
    """
    Base schema class that all other schemas should inherit from.
    This class can be extended with common fields or methods if needed.
    """
