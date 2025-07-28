"""Deduplication utilities for Steam Manifest Tool."""

from typing import List, Tuple, Optional, Dict


def remove_duplicates(
    tuples: List[Tuple[int, Optional[str]]]
) -> List[Tuple[int, Optional[str]]]:
    """Remove duplicate repository records, prioritizing records with keys.
    
    Args:
        tuples: List of (depot_id, depot_key) tuples
        
    Returns:
        Deduplicated list with priority to records containing keys
    """
    result_dict: Dict[int, Tuple[int, Optional[str]]] = {}
    
    for depot_id, depot_key in tuples:
        # If key doesn't exist or current record has a key while stored doesn't
        if (depot_id not in result_dict or 
            (result_dict[depot_id][1] is None and depot_key is not None)):
            result_dict[depot_id] = (depot_id, depot_key)
    
    return list(result_dict.values())