"""
Memory Management Utilities
Garbage collection, memory optimization, and conflict resolution
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class RetentionPolicy:
    """Memory retention policy configuration"""
    default_ttl_days: int = 365
    archive_after_days: int = 180
    delete_after_days: int = 730
    min_access_count: int = 0  # Delete if not accessed at least this many times
    min_size_bytes: int = 0  # Only apply to memories larger than this


class MemoryGarbageCollector:
    """Manages memory cleanup and archival"""
    
    def __init__(self, retention_policy: RetentionPolicy = None):
        """
        Initialize garbage collector
        
        Args:
            retention_policy: Policy for memory retention
        """
        self.policy = retention_policy or RetentionPolicy()
        self.archived: List[Dict[str, Any]] = []
        self.deleted: List[Dict[str, Any]] = []
    
    def analyze_memory(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze memory for garbage collection
        
        Returns:
            Analysis with recommendation: "keep", "archive", or "delete"
        """
        created_at = memory.get("created_at")
        access_count = memory.get("access_count", 0)
        size = len(json.dumps(memory))
        
        if created_at:
            try:
                created = datetime.fromisoformat(created_at)
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                
                now = datetime.now(timezone.utc)
                age_days = (now - created).days
                
                # Check deletion criteria
                if age_days > self.policy.delete_after_days:
                    if access_count < self.policy.min_access_count:
                        return {
                            "recommendation": "delete",
                            "reasons": [
                                f"Age: {age_days} days (threshold: {self.policy.delete_after_days})",
                                f"Access count: {access_count} (minimum: {self.policy.min_access_count})",
                            ],
                            "age_days": age_days,
                            "size": size,
                        }
                
                # Check archival criteria
                if age_days > self.policy.archive_after_days and size > self.policy.min_size_bytes:
                    return {
                        "recommendation": "archive",
                        "reasons": [
                            f"Age: {age_days} days (threshold: {self.policy.archive_after_days})",
                            f"Size: {size} bytes (minimum: {self.policy.min_size_bytes})",
                        ],
                        "age_days": age_days,
                        "size": size,
                    }
                
                return {
                    "recommendation": "keep",
                    "age_days": age_days,
                    "size": size,
                    "access_count": access_count,
                }
            except Exception as e:
                logger.error(f"Error analyzing memory: {e}")
                return {"recommendation": "keep", "error": str(e)}
        
        return {"recommendation": "keep"}
    
    def collect_garbage(
        self,
        memories: List[Dict[str, Any]],
        delete_handler: Callable = None,
        archive_handler: Callable = None,
    ) -> Dict[str, Any]:
        """
        Run garbage collection on memory list
        
        Args:
            memories: List of memories to process
            delete_handler: Callback for deleting memories
            archive_handler: Callback for archiving memories
            
        Returns:
            Statistics on what was collected
        """
        stats = {
            "total_analyzed": len(memories),
            "kept": 0,
            "archived": 0,
            "deleted": 0,
            "errors": 0,
        }
        
        for memory in memories:
            try:
                analysis = self.analyze_memory(memory)
                recommendation = analysis.get("recommendation", "keep")
                
                if recommendation == "delete":
                    if delete_handler:
                        delete_handler(memory)
                    self.deleted.append(memory)
                    stats["deleted"] += 1
                    logger.info(f"Deleted memory: {memory.get('id')}")
                
                elif recommendation == "archive":
                    if archive_handler:
                        archive_handler(memory)
                    self.archived.append(memory)
                    stats["archived"] += 1
                    logger.info(f"Archived memory: {memory.get('id')}")
                
                else:
                    stats["kept"] += 1
            
            except Exception as e:
                logger.error(f"Error processing memory: {e}")
                stats["errors"] += 1
        
        logger.info(f"Garbage collection complete: {stats}")
        return stats
    
    def export_archived(self, format: str = "json") -> str:
        """Export archived memories"""
        if format == "json":
            return json.dumps(self.archived, indent=2, default=str)
        else:
            return str(self.archived)


class ConflictResolver:
    """Resolves conflicts from concurrent memory updates"""
    
    @staticmethod
    def resolve_last_write_wins(
        current: Dict[str, Any],
        incoming: Dict[str, Any],
        field: str = "updated_at",
    ) -> Dict[str, Any]:
        """Last-write-wins strategy"""
        current_time = current.get(field)
        incoming_time = incoming.get(field)
        
        try:
            if isinstance(current_time, str):
                current_time = datetime.fromisoformat(current_time)
            if isinstance(incoming_time, str):
                incoming_time = datetime.fromisoformat(incoming_time)
            
            if incoming_time > current_time:
                logger.info("Conflict resolved: incoming update wins (LWW)")
                return incoming
        except Exception as e:
            logger.error(f"Error comparing timestamps: {e}")
        
        logger.info("Conflict resolved: current version wins (LWW)")
        return current
    
    @staticmethod
    def resolve_merge(
        current: Dict[str, Any],
        incoming: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merge strategy - combines non-conflicting fields"""
        merged = current.copy()
        
        for key, value in incoming.items():
            if key not in merged:
                # New field, add it
                merged[key] = value
            elif key == "tags" and isinstance(value, list) and isinstance(merged[key], list):
                # Merge tags
                merged[key] = list(set(merged[key] + value))
            elif key == "metadata" and isinstance(value, dict) and isinstance(merged[key], dict):
                # Merge metadata
                merged_metadata = merged[key].copy()
                merged_metadata.update(value)
                merged[key] = merged_metadata
            # For other fields, keep current (incoming would overwrite)
        
        logger.info("Conflict resolved: merge strategy")
        return merged
    
    @staticmethod
    def resolve_custom(
        current: Dict[str, Any],
        incoming: Dict[str, Any],
        resolver_func: Callable,
    ) -> Dict[str, Any]:
        """Custom resolver function"""
        try:
            result = resolver_func(current, incoming)
            logger.info("Conflict resolved: custom resolver")
            return result
        except Exception as e:
            logger.error(f"Error in custom resolver: {e}")
            return current
    
    @staticmethod
    def detect_conflict(
        version1: Dict[str, Any],
        version2: Dict[str, Any],
    ) -> bool:
        """Detect if two memory versions conflict"""
        # Simple conflict detection: if content differs and both are newer than original
        v1_content = version1.get("content")
        v2_content = version2.get("content")
        
        if v1_content != v2_content:
            v1_time = version1.get("updated_at")
            v2_time = version2.get("updated_at")
            
            # If both were updated, there's a conflict
            if v1_time and v2_time:
                return True
        
        return False


class MemoryOptimizer:
    """Optimize memory usage and database performance"""
    
    @staticmethod
    def estimate_size(memory: Dict[str, Any]) -> int:
        """Estimate memory size in bytes"""
        try:
            return len(json.dumps(memory).encode('utf-8'))
        except Exception:
            return 0
    
    @staticmethod
    def calculate_compression_ratio(
        original_size: int,
        compressed_size: int,
    ) -> float:
        """Calculate compression ratio"""
        if original_size == 0:
            return 0.0
        return (1 - compressed_size / original_size) * 100
    
    @staticmethod
    def optimize_memory(memory: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize memory content"""
        optimized = memory.copy()
        
        # Remove unnecessary fields
        to_remove = [f for f in optimized if f.startswith("_")]
        for field in to_remove:
            del optimized[field]
        
        # Compress large text fields
        if "content" in optimized:
            content = optimized["content"]
            if isinstance(content, str) and len(content) > 10000:
                # Mark that this should be compressed
                optimized["_needs_compression"] = True
        
        return optimized


def detect_duplicates(
    memories: List[Dict[str, Any]],
    threshold: float = 0.95,
) -> List[tuple]:
    """
    Detect potentially duplicate memories using simple similarity
    
    Args:
        memories: Memories to check
        threshold: Similarity threshold (0-1)
        
    Returns:
        List of (memory1, memory2, similarity) tuples
    """
    duplicates = []
    
    for i, mem1 in enumerate(memories):
        for mem2 in memories[i+1:]:
            # Simple content-based similarity
            content1 = mem1.get("content", "").lower()
            content2 = mem2.get("content", "").lower()
            
            if not content1 or not content2:
                continue
            
            # Very basic similarity check (character overlap)
            common = sum(1 for c in content1 if c in content2)
            if common > 0:
                similarity = common / max(len(content1), len(content2))
                
                if similarity >= threshold:
                    duplicates.append((mem1, mem2, similarity))
    
    return duplicates
