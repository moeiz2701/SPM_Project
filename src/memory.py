"""
Memory Manager for Loyalty AI Agent
Implements short-term (in-memory cache) and long-term (persistent JSON) memory architecture
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import OrderedDict

try:
    from src.logger import get_logger
except ImportError:
    from logger import get_logger


class MemoryManager:
    """
    Manages short-term and long-term memory for the agent.
    
    - Short-term: In-memory cache for active session data (LRU cache)
    - Long-term: JSON file storage for historical customer interactions
    """
    
    def __init__(self, 
                 memory_dir: str = "data/memory",
                 short_term_capacity: int = 1000,
                 long_term_file: str = "long_term_memory.json"):
        """
        Initialize Memory Manager
        
        Args:
            memory_dir: Directory for storing long-term memory files
            short_term_capacity: Maximum number of items in short-term cache
            long_term_file: Filename for long-term memory storage
        """
        self.logger = get_logger(__name__)
        
        # Short-term memory (LRU cache using OrderedDict)
        self.short_term_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.short_term_capacity = short_term_capacity
        
        # Long-term memory setup
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.long_term_file_path = self.memory_dir / long_term_file
        
        # Initialize long-term memory structure
        self.long_term_memory: Dict[str, List[Dict[str, Any]]] = {}
        self._load_long_term_memory()
        
        self.logger.info(f"Memory Manager initialized - Cache capacity: {short_term_capacity}")
        self.logger.info(f"Long-term memory file: {self.long_term_file_path}")
    
    # ==================== Short-Term Memory (Cache) ====================
    
    def store_short_term(self, customer_id: str, data: Dict[str, Any]) -> None:
        """
        Store data in short-term memory (in-memory cache)
        Uses LRU eviction when capacity is reached
        
        Args:
            customer_id: Customer identifier
            data: Data to store
        """
        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # If key exists, move to end (most recently used)
            if customer_id in self.short_term_cache:
                self.short_term_cache.move_to_end(customer_id)
            
            # Add new entry
            self.short_term_cache[customer_id] = data
            
            # Evict oldest entry if capacity exceeded
            if len(self.short_term_cache) > self.short_term_capacity:
                oldest_key = next(iter(self.short_term_cache))
                evicted = self.short_term_cache.pop(oldest_key)
                self.logger.debug(f"Evicted {oldest_key} from short-term cache (LRU)")
            
            self.logger.debug(f"Stored {customer_id} in short-term memory")
            
        except Exception as e:
            self.logger.error(f"Error storing short-term memory for {customer_id}: {str(e)}")
    
    def get_short_term(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from short-term memory
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Cached data or None if not found
        """
        try:
            if customer_id in self.short_term_cache:
                # Move to end (mark as recently accessed)
                self.short_term_cache.move_to_end(customer_id)
                self.logger.debug(f"Cache hit for {customer_id}")
                return self.short_term_cache[customer_id]
            
            self.logger.debug(f"Cache miss for {customer_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving short-term memory for {customer_id}: {str(e)}")
            return None
    
    def get_all_short_term(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all entries from short-term cache
        
        Returns:
            Dictionary of all cached data
        """
        return dict(self.short_term_cache)
    
    def clear_short_term(self) -> None:
        """Clear all short-term memory"""
        count = len(self.short_term_cache)
        self.short_term_cache.clear()
        self.logger.info(f"Cleared {count} entries from short-term cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the short-term cache
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "current_size": len(self.short_term_cache),
            "capacity": self.short_term_capacity,
            "utilization_percent": round(len(self.short_term_cache) / self.short_term_capacity * 100, 2)
        }
    
    # ==================== Long-Term Memory (Persistent) ====================
    
    def _load_long_term_memory(self) -> None:
        """Load long-term memory from JSON file"""
        try:
            if self.long_term_file_path.exists():
                with open(self.long_term_file_path, 'r', encoding='utf-8') as f:
                    self.long_term_memory = json.load(f)
                
                customer_count = len(self.long_term_memory)
                total_entries = sum(len(entries) for entries in self.long_term_memory.values())
                self.logger.info(f"Loaded long-term memory: {customer_count} customers, {total_entries} entries")
            else:
                self.long_term_memory = {}
                self.logger.info("No existing long-term memory file found. Starting fresh.")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding long-term memory JSON: {str(e)}")
            self.long_term_memory = {}
        except Exception as e:
            self.logger.error(f"Error loading long-term memory: {str(e)}")
            self.long_term_memory = {}
    
    def _save_long_term_memory(self) -> None:
        """Save long-term memory to JSON file"""
        try:
            with open(self.long_term_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.long_term_memory, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Saved long-term memory to {self.long_term_file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving long-term memory: {str(e)}")
    
    def store_long_term(self, customer_id: str, data: Dict[str, Any]) -> None:
        """
        Store data in long-term memory (persistent JSON storage)
        Appends to customer's history
        
        Args:
            customer_id: Customer identifier
            data: Data to store
        """
        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # Create entry list for customer if not exists
            if customer_id not in self.long_term_memory:
                self.long_term_memory[customer_id] = []
            
            # Append to customer's history
            self.long_term_memory[customer_id].append(data)
            
            # Save to file
            self._save_long_term_memory()
            
            self.logger.debug(f"Stored {customer_id} in long-term memory")
            
        except Exception as e:
            self.logger.error(f"Error storing long-term memory for {customer_id}: {str(e)}")
    
    def get_long_term_history(self, customer_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve customer's history from long-term memory
        
        Args:
            customer_id: Customer identifier
            limit: Optional limit on number of entries to return (most recent first)
            
        Returns:
            List of historical entries
        """
        try:
            if customer_id in self.long_term_memory:
                history = self.long_term_memory[customer_id]
                
                # Return most recent entries if limit specified
                if limit and limit > 0:
                    return history[-limit:]
                
                return history
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error retrieving long-term history for {customer_id}: {str(e)}")
            return []
    
    def get_all_long_term(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all long-term memory
        
        Returns:
            Dictionary of all customer histories
        """
        return self.long_term_memory
    
    def clear_long_term(self, customer_id: Optional[str] = None) -> None:
        """
        Clear long-term memory
        
        Args:
            customer_id: If provided, clear only this customer's history.
                        If None, clear all long-term memory.
        """
        try:
            if customer_id:
                if customer_id in self.long_term_memory:
                    del self.long_term_memory[customer_id]
                    self._save_long_term_memory()
                    self.logger.info(f"Cleared long-term memory for {customer_id}")
            else:
                self.long_term_memory.clear()
                self._save_long_term_memory()
                self.logger.info("Cleared all long-term memory")
                
        except Exception as e:
            self.logger.error(f"Error clearing long-term memory: {str(e)}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about memory usage
        
        Returns:
            Dictionary with memory statistics
        """
        try:
            # Short-term stats
            cache_stats = self.get_cache_stats()
            
            # Long-term stats
            total_customers = len(self.long_term_memory)
            total_entries = sum(len(entries) for entries in self.long_term_memory.values())
            avg_entries_per_customer = round(total_entries / total_customers, 2) if total_customers > 0 else 0
            
            # File size
            file_size_bytes = self.long_term_file_path.stat().st_size if self.long_term_file_path.exists() else 0
            file_size_kb = round(file_size_bytes / 1024, 2)
            
            return {
                "short_term": cache_stats,
                "long_term": {
                    "total_customers": total_customers,
                    "total_entries": total_entries,
                    "avg_entries_per_customer": avg_entries_per_customer,
                    "file_size_kb": file_size_kb,
                    "file_path": str(self.long_term_file_path)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating memory stats: {str(e)}")
            return {}
    
    # ==================== Utility Methods ====================
    
    def persist_all(self) -> None:
        """
        Persist all short-term memory to long-term storage
        Useful for graceful shutdown
        """
        try:
            count = 0
            for customer_id, data in self.short_term_cache.items():
                self.store_long_term(customer_id, data.copy())
                count += 1
            
            if count > 0:
                self.logger.info(f"Persisted {count} entries from short-term to long-term memory")
            
        except Exception as e:
            self.logger.error(f"Error persisting short-term memory: {str(e)}")
    
    def cleanup_old_entries(self, days_old: int = 90) -> int:
        """
        Remove entries older than specified days from long-term memory
        
        Args:
            days_old: Remove entries older than this many days
            
        Returns:
            Number of entries removed
        """
        try:
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            removed_count = 0
            
            for customer_id in list(self.long_term_memory.keys()):
                entries = self.long_term_memory[customer_id]
                
                # Filter out old entries
                filtered_entries = []
                for entry in entries:
                    try:
                        entry_time = datetime.fromisoformat(entry['timestamp']).timestamp()
                        if entry_time >= cutoff_date:
                            filtered_entries.append(entry)
                        else:
                            removed_count += 1
                    except (KeyError, ValueError):
                        # Keep entry if timestamp invalid
                        filtered_entries.append(entry)
                
                # Update or remove customer entry
                if filtered_entries:
                    self.long_term_memory[customer_id] = filtered_entries
                else:
                    del self.long_term_memory[customer_id]
            
            if removed_count > 0:
                self._save_long_term_memory()
                self.logger.info(f"Cleaned up {removed_count} entries older than {days_old} days")
            
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old entries: {str(e)}")
            return 0


# ==================== Example Usage ====================

if __name__ == "__main__":
    """Test the Memory Manager"""
    print("\n" + "=" * 60)
    print("Memory Manager Test")
    print("=" * 60 + "\n")
    
    # Initialize
    memory = MemoryManager(short_term_capacity=5)
    
    # Test short-term memory
    print("Testing Short-Term Memory (Cache):")
    print("-" * 60)
    
    for i in range(7):
        customer_id = f"CUST_{i:03d}"
        data = {
            "customer_id": customer_id,
            "action": "test",
            "value": i * 100
        }
        memory.store_short_term(customer_id, data)
        print(f"Stored: {customer_id}")
    
    print(f"\nCache Stats: {memory.get_cache_stats()}")
    print(f"Cache Contents: {len(memory.get_all_short_term())} entries")
    
    # Test long-term memory
    print("\n\nTesting Long-Term Memory (Persistent):")
    print("-" * 60)
    
    for i in range(3):
        customer_id = f"CUST_{i:03d}"
        data = {
            "customer_id": customer_id,
            "recommendation": f"Reward_{i}",
            "retention": 0.85 + (i * 0.05)
        }
        memory.store_long_term(customer_id, data)
        print(f"Stored: {customer_id}")
    
    # Retrieve history
    history = memory.get_long_term_history("CUST_001")
    print(f"\nHistory for CUST_001: {len(history)} entries")
    
    # Stats
    print("\n\nMemory Statistics:")
    print("-" * 60)
    stats = memory.get_memory_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60 + "\n")
