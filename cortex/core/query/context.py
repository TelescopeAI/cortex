from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import Field, validator
from cortex.core.types.telescope import TSModel
from cortex.core.consumers.db.service import ConsumerCRUD
from cortex.core.consumers.db.group_service import ConsumerGroupCRUD


class ContextType:
    """Enum-like class for context types"""
    CONSUMER = "C"
    CONSUMER_GROUP = "CG"
    CONSUMER_IN_GROUP = "CCG"


class MetricContext(TSModel):
    """
    Represents a metric execution context with type and unique identifier.
    Handles parsing of context_id format: <TYPE>_<UNIQUEID> or <TYPE>_<ID1>_<ID2>
    """
    
    context_id: str
    context_type: str = Field(description="Type identifier (C, CG, CCG)")
    primary_id: UUID = Field(description="Primary unique identifier")
    secondary_id: Optional[UUID] = Field(None, description="Secondary unique identifier (for CCG type)")
    
    @validator('context_id')
    def validate_context_id(cls, v):
        """Validate context_id format"""
        if not v:
            raise ValueError("context_id cannot be empty")
        
        parts = v.split('_')
        if len(parts) < 2:
            raise ValueError("context_id must be in format <TYPE>_<UNIQUEID> or <TYPE>_<ID1>_<ID2>")
        
        context_type = parts[0]
        if context_type not in [ContextType.CONSUMER, ContextType.CONSUMER_GROUP, ContextType.CONSUMER_IN_GROUP]:
            raise ValueError(f"Invalid context type: {context_type}. Must be one of: C, CG, CCG")
        
        # Validate UUID format for IDs
        try:
            if context_type == ContextType.CONSUMER_IN_GROUP:
                if len(parts) != 3:
                    raise ValueError("CCG context_id must be in format CCG_<CONSUMER_ID>_<GROUP_ID>")
                UUID(parts[1])  # consumer_id
                UUID(parts[2])  # group_id
            else:
                if len(parts) != 2:
                    raise ValueError(f"{context_type} context_id must be in format {context_type}_<UNIQUEID>")
                UUID(parts[1])  # single_id
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"Invalid UUID format in context_id: {v}")
            raise e
        
        return v
    
    @classmethod
    def parse(cls, context_id: str) -> 'MetricContext':
        """
        Parse a context_id string into a MetricContext object.
        
        Args:
            context_id: String in format <TYPE>_<UNIQUEID> or <TYPE>_<ID1>_<ID2>
            
        Returns:
            MetricContext object with parsed components
        """
        parts = context_id.split('_')
        context_type = parts[0]
        
        if context_type == ContextType.CONSUMER_IN_GROUP:
            return cls(
                context_id=context_id,
                context_type=context_type,
                primary_id=UUID(parts[1]),  # consumer_id
                secondary_id=UUID(parts[2])  # group_id
            )
        else:
            return cls(
                context_id=context_id,
                context_type=context_type,
                primary_id=UUID(parts[1])  # single_id
            )
    
    def get_consumer_properties(self) -> Optional[Dict[str, Any]]:
        """
        Get consumer properties based on context type.
        
        Returns:
            Dictionary of consumer properties or None if not found
        """
        try:
            if self.context_type == ContextType.CONSUMER:
                # Direct consumer lookup
                consumer = ConsumerCRUD.get_consumer(self.primary_id)
                return consumer.properties if consumer else None
                
            elif self.context_type == ContextType.CONSUMER_GROUP:
                # Use the group's own properties directly
                group = ConsumerGroupCRUD.get_consumer_group(self.primary_id)
                return group.properties if group else None
                
            elif self.context_type == ContextType.CONSUMER_IN_GROUP:
                # Get specific consumer from specific group
                consumer = ConsumerCRUD.get_consumer(self.primary_id)
                if consumer:
                    # Verify consumer is in the specified group
                    groups = ConsumerGroupCRUD.get_groups_for_consumer(self.primary_id)
                    group_ids = [str(g.id) for g in groups]
                    if str(self.secondary_id) in group_ids:
                        return consumer.properties
                return None
                
        except Exception as e:
            print(f"Error getting consumer properties for context {self.context_id}: {e}")
            return None
        
        return None
    
    def get_context_summary(self) -> str:
        """
        Get a human-readable summary of the context.
        
        Returns:
            String description of the context
        """
        if self.context_type == ContextType.CONSUMER:
            return f"Consumer: {self.primary_id}"
        elif self.context_type == ContextType.CONSUMER_GROUP:
            return f"Consumer Group: {self.primary_id}"
        elif self.context_type == ContextType.CONSUMER_IN_GROUP:
            return f"Consumer {self.primary_id} in Group {self.secondary_id}"
        else:
            return f"Unknown Context: {self.context_id}" 