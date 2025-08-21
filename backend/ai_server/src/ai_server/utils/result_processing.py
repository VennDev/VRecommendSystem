from typing import List, Dict, Any
import pandas as pd


def rename_columns(data: Dict[str, Any], column_mapping: str) -> Dict[str, Any]:
    """
    Rename keys in a dictionary based on a column mapping string.

    Args:
        data: Dictionary containing data to be renamed.
        column_mapping: String with comma-separated key pairs for renaming,
                        e.g., "old_key1:new_key1,old_key2:new_key2".

    Returns:
        Dict[str, Any]: Dictionary with renamed keys.

    Example:
        >>> data = {'id': 1, 'name': 'John', 'age': 30}
        >>> column_mapping = "id->user_id,name->full_name"
        >>> renamed_data = rename_columns(data, column_mapping)
        >>> print(renamed_data)
        {'user_id': 1, 'full_name': 'John', 'age': 30}
    """
    if not column_mapping:
        return data

    mapping = dict(pair.split("->") for pair in column_mapping.split(","))
    return {mapping.get(k, k): v for k, v in data.items()}


def list_dict_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert List[Dict[str, Any]] to pandas DataFrame

    Args:
        data: List of dictionaries containing data

    Returns:
        pd.DataFrame: DataFrame created from input data

    Example:
        >>> data = [{'id': 1, 'name': 'John', 'age': 30}, {'id': 2, 'name': 'Jane', 'age': 25}]
        >>> df = list_dict_to_dataframe(data)
        >>> print(df)
           id  name  age
        0   1  John   30
        1   2  Jane   25
    """
    if not data:
        return pd.DataFrame()

    return pd.DataFrame(data)


def dict_to_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert Dict[str, Any] to pandas DataFrame

    Args:
        data: Dictionary containing data

    Returns:
        pd.DataFrame: DataFrame created from input data

    Example:
        >>> data = {'id': [1, 2], 'name': ['John', 'Jane'], 'age': [30, 25]}
        >>> df = dict_to_dataframe(data)
        >>> print(df)
           id  name  age
        0   1  John   30
        1   2  Jane   25
    """
    if not data:
        return pd.DataFrame()

    return pd.DataFrame.from_dict(data, orient="index").T
