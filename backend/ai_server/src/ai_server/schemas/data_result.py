from ai_server.schemas.base_schema import BaseSchema


class DataResult(BaseSchema):
    """
    Schema for a data result.
    This schema can be extended with additional fields as needed.
    """
    result: any = None
