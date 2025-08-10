from typing import List, Dict, Any
import pandas as pd


def rename_columns(data: List[Dict[str, Any]], column_mapping: str) -> List[Dict[str, Any]]:
    """
    Rename columns in a list of dictionaries using the syntax name_a->name_b

    Args:
        data: List of dictionaries containing data from database
        column_mapping: Mapping string in format "old_name->new_name,old_name2->new_name2"

    Returns:
        List[Dict[str, Any]]: Data with renamed columns

    Example:
        >>> data = [{'id': 1, 'full_name': 'John Doe'}, {'id': 2, 'full_name': 'Jane Smith'}]
        >>> result = rename_columns(data, "id->user_id,full_name->name")
        >>> print(result)
        [{'user_id': 1, 'name': 'John Doe'}, {'user_id': 2, 'name': 'Jane Smith'}]
    """
    if not data or not column_mapping:
        return data

    # Parse column mapping string
    mappings = {}
    for mapping in column_mapping.split(','):
        mapping = mapping.strip()
        if '->' in mapping:
            old_name, new_name = mapping.split('->', 1)
            mappings[old_name.strip()] = new_name.strip()

    # Apply column renaming
    renamed_data = []
    for row in data:
        new_row = {}
        for old_key, value in row.items():
            new_key = mappings.get(old_key, old_key)
            new_row[new_key] = value
        renamed_data.append(new_row)

    return renamed_data


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
