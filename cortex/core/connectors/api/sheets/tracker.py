from typing import Dict, Optional
from datetime import datetime
import hashlib


class CortexRefreshTracker:
    """Tracks sheet/table state for refresh detection"""
    
    def __init__(self):
        """Initialize refresh tracker"""
        self.table_hashes: Dict[str, str] = {}
        self.last_synced: Optional[str] = None
    
    def update_table_hash(self, table_name: str, content_hash: str) -> None:
        """
        Update the hash for a table
        
        Args:
            table_name: Name of the table
            content_hash: Hash of the table's current content
        """
        self.table_hashes[table_name] = content_hash
        self.last_synced = datetime.utcnow().isoformat()
    
    def needs_refresh(self, table_name: str, current_hash: str) -> bool:
        """
        Check if a table needs refreshing
        
        Args:
            table_name: Name of the table
            current_hash: Current hash of the table's content
            
        Returns:
            True if the hash has changed, False otherwise
        """
        if table_name not in self.table_hashes:
            # New table, doesn't need refresh
            return False
        
        return self.table_hashes[table_name] != current_hash
    
    def get_state(self) -> Dict:
        """
        Get the current tracking state (for storage in config)
        
        Returns:
            Dictionary with table hashes and last synced timestamp
        """
        return {
            "table_hashes": self.table_hashes,
            "last_synced": self.last_synced,
        }
    
    def restore_state(self, state: Dict) -> None:
        """
        Restore tracking state from config
        
        Args:
            state: Dictionary with table hashes and last synced timestamp
        """
        self.table_hashes = state.get("table_hashes", {})
        self.last_synced = state.get("last_synced")
    
    def get_tables_to_refresh(self, current_hashes: Dict[str, str]) -> list:
        """
        Get list of tables that need refreshing
        
        Args:
            current_hashes: Dictionary mapping table names to their current hashes
            
        Returns:
            List of table names that have changed
        """
        tables_to_refresh = []
        
        for table_name, current_hash in current_hashes.items():
            if self.needs_refresh(table_name, current_hash):
                tables_to_refresh.append(table_name)
        
        return tables_to_refresh
