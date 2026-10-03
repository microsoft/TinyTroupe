"""
Distributed Caching System for TinyTroupe Enterprise Scale
Created by Ollie (Optimizer) & Devon (DevOps) - RovoDev Multi-Agent Team

MASSIVE SCALE caching for 10,000+ concurrent agents!
"""

import asyncio
import redis.asyncio as redis
import json
import pickle
import hashlib
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import threading
from enum import Enum

logger = logging.getLogger("tinytroupe.distributed_cache")

class CacheStrategy(Enum):
    """Cache distribution strategies"""
    CONSISTENT_HASHING = "consistent_hashing"
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    GEOGRAPHIC = "geographic"

@dataclass
class CacheNode:
    """Distributed cache node configuration"""
    host: str
    port: int
    region: str = "default"
    weight: int = 1
    max_connections: int = 100
    health_check_interval: int = 30

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    network_errors: int = 0
    avg_response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    connection_count: int = 0

class DistributedCacheCluster:
    """
    Enterprise-grade distributed caching cluster
    Ollie's Speed Machine: LUDICROUS caching performance!
    """
    
    def __init__(self, nodes: List[CacheNode], strategy: CacheStrategy = CacheStrategy.CONSISTENT_HASHING):
        self.nodes = nodes
        self.strategy = strategy
        self.connections: Dict[str, redis.Redis] = {}
        self.node_metrics: Dict[str, CacheMetrics] = {}
        self.hash_ring: Dict[int, str] = {}
        
        # Performance tracking
        self.global_metrics = CacheMetrics()
        self._lock = threading.RLock()
        
        # Health monitoring
        self.health_check_enabled = True
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Initialize cluster
        asyncio.create_task(self._initialize_cluster())
    
    async def _initialize_cluster(self):
        """Initialize distributed cache cluster"""
        logger.info(f"Initializing distributed cache cluster with {len(self.nodes)} nodes")
        
        # Create connections to all nodes
        for node in self.nodes:
            node_id = f"{node.host}:{node.port}"
            try:
                connection = redis.Redis(
                    host=node.host,
                    port=node.port,
                    max_connections=node.max_connections,
                    decode_responses=False,  # Handle binary data
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                
                # Test connection
                await connection.ping()
                
                self.connections[node_id] = connection
                self.node_metrics[node_id] = CacheMetrics()
                
                logger.info(f"Connected to cache node: {node_id}")
                
            except Exception as e:
                logger.error(f"Failed to connect to cache node {node_id}: {e}")
        
        # Build consistent hash ring
        if self.strategy == CacheStrategy.CONSISTENT_HASHING:
            self._build_hash_ring()
        
        # Start health monitoring
        if self.health_check_enabled:
            self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    def _build_hash_ring(self):
        """Build consistent hash ring for cache distribution"""
        self.hash_ring = {}
        
        # Create virtual nodes for better distribution
        virtual_nodes_per_physical = 150
        
        for node in self.nodes:
            node_id = f"{node.host}:{node.port}"
            if node_id in self.connections:
                # Create virtual nodes based on weight
                for i in range(virtual_nodes_per_physical * node.weight):
                    virtual_key = f"{node_id}:{i}"
                    hash_value = int(hashlib.md5(virtual_key.encode()).hexdigest(), 16)
                    self.hash_ring[hash_value] = node_id
        
        logger.info(f"Built consistent hash ring with {len(self.hash_ring)} virtual nodes")
    
    def _get_node_for_key(self, key: str) -> Optional[str]:
        """Get cache node for given key using selected strategy"""
        if not self.connections:
            return None
        
        if self.strategy == CacheStrategy.CONSISTENT_HASHING:
            return self._get_node_consistent_hash(key)
        elif self.strategy == CacheStrategy.ROUND_ROBIN:
            return self._get_node_round_robin()
        elif self.strategy == CacheStrategy.LEAST_LOADED:
            return self._get_node_least_loaded()
        else:
            # Default to first available node
            return list(self.connections.keys())[0]
    
    def _get_node_consistent_hash(self, key: str) -> Optional[str]:
        """Get node using consistent hashing"""
        if not self.hash_ring:
            return list(self.connections.keys())[0] if self.connections else None
        
        key_hash = int(hashlib.md5(key.encode()).hexdigest(), 16)
        
        # Find the first node clockwise from the key hash
        for hash_value in sorted(self.hash_ring.keys()):
            if hash_value >= key_hash:
                return self.hash_ring[hash_value]
        
        # Wrap around to the first node
        return self.hash_ring[min(self.hash_ring.keys())]
    
    def _get_node_round_robin(self) -> str:
        """Get node using round-robin strategy"""
        # Simple round-robin based on current time
        node_list = list(self.connections.keys())
        index = int(time.time()) % len(node_list)
        return node_list[index]
    
    def _get_node_least_loaded(self) -> str:
        """Get least loaded node based on connection count"""
        least_loaded = min(
            self.connections.keys(),
            key=lambda node_id: self.node_metrics[node_id].connection_count
        )
        return least_loaded
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from distributed cache"""
        start_time = time.time()
        
        try:
            node_id = self._get_node_for_key(key)
            if not node_id:
                self._record_miss()
                return default
            
            connection = self.connections[node_id]
            
            # Try to get from cache
            cached_data = await connection.get(key)
            
            if cached_data is not None:
                # Deserialize data
                try:
                    value = pickle.loads(cached_data)
                    self._record_hit(node_id, time.time() - start_time)
                    return value
                except Exception as e:
                    logger.error(f"Failed to deserialize cached data for key {key}: {e}")
                    self._record_miss()
                    return default
            else:
                self._record_miss()
                return default
                
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._record_network_error()
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in distributed cache"""
        try:
            node_id = self._get_node_for_key(key)
            if not node_id:
                return False
            
            connection = self.connections[node_id]
            
            # Serialize data
            try:
                serialized_data = pickle.dumps(value)
            except Exception as e:
                logger.error(f"Failed to serialize data for key {key}: {e}")
                return False
            
            # Set in cache with optional TTL
            if ttl:
                success = await connection.setex(key, ttl, serialized_data)
            else:
                success = await connection.set(key, serialized_data)
            
            return bool(success)
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self._record_network_error()
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from distributed cache"""
        try:
            node_id = self._get_node_for_key(key)
            if not node_id:
                return False
            
            connection = self.connections[node_id]
            deleted_count = await connection.delete(key)
            
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self._record_network_error()
            return False
    
    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Multi-get values from distributed cache"""
        results = {}
        
        # Group keys by node
        node_keys: Dict[str, List[str]] = {}
        for key in keys:
            node_id = self._get_node_for_key(key)
            if node_id:
                if node_id not in node_keys:
                    node_keys[node_id] = []
                node_keys[node_id].append(key)
        
        # Fetch from each node in parallel
        tasks = []
        for node_id, node_key_list in node_keys.items():
            task = self._mget_from_node(node_id, node_key_list)
            tasks.append(task)
        
        # Collect results
        if tasks:
            node_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in node_results:
                if isinstance(result, dict):
                    results.update(result)
        
        return results
    
    async def _mget_from_node(self, node_id: str, keys: List[str]) -> Dict[str, Any]:
        """Multi-get from specific node"""
        try:
            connection = self.connections[node_id]
            cached_values = await connection.mget(keys)
            
            results = {}
            for key, cached_data in zip(keys, cached_values):
                if cached_data is not None:
                    try:
                        value = pickle.loads(cached_data)
                        results[key] = value
                        self._record_hit(node_id, 0)  # Approximate timing
                    except Exception as e:
                        logger.error(f"Failed to deserialize cached data for key {key}: {e}")
                        self._record_miss()
                else:
                    self._record_miss()
            
            return results
            
        except Exception as e:
            logger.error(f"Multi-get error from node {node_id}: {e}")
            self._record_network_error()
            return {}
    
    async def mset(self, key_value_pairs: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Multi-set values in distributed cache"""
        # Group by node
        node_data: Dict[str, Dict[str, Any]] = {}
        for key, value in key_value_pairs.items():
            node_id = self._get_node_for_key(key)
            if node_id:
                if node_id not in node_data:
                    node_data[node_id] = {}
                node_data[node_id][key] = value
        
        # Set on each node in parallel
        tasks = []
        for node_id, data in node_data.items():
            task = self._mset_to_node(node_id, data, ttl)
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return all(isinstance(r, bool) and r for r in results)
        
        return False
    
    async def _mset_to_node(self, node_id: str, key_value_pairs: Dict[str, Any], 
                           ttl: Optional[int] = None) -> bool:
        """Multi-set to specific node"""
        try:
            connection = self.connections[node_id]
            
            # Serialize all values
            serialized_pairs = {}
            for key, value in key_value_pairs.items():
                try:
                    serialized_pairs[key] = pickle.dumps(value)
                except Exception as e:
                    logger.error(f"Failed to serialize data for key {key}: {e}")
                    return False
            
            # Use pipeline for efficiency
            pipe = connection.pipeline()
            
            if ttl:
                for key, serialized_value in serialized_pairs.items():
                    pipe.setex(key, ttl, serialized_value)
            else:
                pipe.mset(serialized_pairs)
            
            await pipe.execute()
            return True
            
        except Exception as e:
            logger.error(f"Multi-set error to node {node_id}: {e}")
            self._record_network_error()
            return False
    
    async def flush_all(self) -> bool:
        """Flush all cache nodes"""
        tasks = []
        for node_id, connection in self.connections.items():
            task = self._flush_node(node_id, connection)
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return all(isinstance(r, bool) and r for r in results)
        
        return False
    
    async def _flush_node(self, node_id: str, connection: redis.Redis) -> bool:
        """Flush specific cache node"""
        try:
            await connection.flushdb()
            logger.info(f"Flushed cache node: {node_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to flush cache node {node_id}: {e}")
            return False
    
    async def _health_check_loop(self):
        """Continuous health monitoring of cache nodes"""
        while self.health_check_enabled:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _perform_health_checks(self):
        """Perform health checks on all nodes"""
        for node_id, connection in self.connections.copy().items():
            try:
                # Simple ping test
                start_time = time.time()
                await connection.ping()
                response_time = (time.time() - start_time) * 1000
                
                # Update metrics
                metrics = self.node_metrics[node_id]
                metrics.avg_response_time_ms = (metrics.avg_response_time_ms + response_time) / 2
                
                # Get memory usage
                info = await connection.info('memory')
                metrics.memory_usage_mb = info.get('used_memory', 0) / 1024 / 1024
                
            except Exception as e:
                logger.warning(f"Health check failed for node {node_id}: {e}")
                # Consider removing unhealthy node temporarily
                # In production, implement more sophisticated failover
    
    def _record_hit(self, node_id: str, response_time: float):
        """Record cache hit metrics"""
        with self._lock:
            self.global_metrics.hits += 1
            if node_id in self.node_metrics:
                self.node_metrics[node_id].hits += 1
                # Update average response time
                current_avg = self.node_metrics[node_id].avg_response_time_ms
                self.node_metrics[node_id].avg_response_time_ms = (current_avg + response_time * 1000) / 2
    
    def _record_miss(self):
        """Record cache miss metrics"""
        with self._lock:
            self.global_metrics.misses += 1
    
    def _record_network_error(self):
        """Record network error metrics"""
        with self._lock:
            self.global_metrics.network_errors += 1
    
    def get_cluster_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cluster metrics"""
        with self._lock:
            total_requests = self.global_metrics.hits + self.global_metrics.misses
            hit_rate = (self.global_metrics.hits / total_requests * 100) if total_requests > 0 else 0
            
            node_stats = {}
            for node_id, metrics in self.node_metrics.items():
                node_total = metrics.hits + metrics.misses
                node_hit_rate = (metrics.hits / node_total * 100) if node_total > 0 else 0
                
                node_stats[node_id] = {
                    "hits": metrics.hits,
                    "misses": metrics.misses,
                    "hit_rate_percent": node_hit_rate,
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "memory_usage_mb": metrics.memory_usage_mb,
                    "evictions": metrics.evictions,
                    "network_errors": metrics.network_errors
                }
            
            return {
                "cluster_summary": {
                    "total_nodes": len(self.connections),
                    "healthy_nodes": len([n for n in self.connections.keys() if n in self.node_metrics]),
                    "strategy": self.strategy.value,
                    "total_hits": self.global_metrics.hits,
                    "total_misses": self.global_metrics.misses,
                    "hit_rate_percent": hit_rate,
                    "network_errors": self.global_metrics.network_errors
                },
                "node_metrics": node_stats
            }
    
    async def shutdown(self):
        """Gracefully shutdown the cache cluster"""
        logger.info("Shutting down distributed cache cluster")
        
        # Stop health monitoring
        self.health_check_enabled = False
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for node_id, connection in self.connections.items():
            try:
                await connection.close()
                logger.info(f"Closed connection to cache node: {node_id}")
            except Exception as e:
                logger.error(f"Error closing connection to {node_id}: {e}")
        
        self.connections.clear()

# Global distributed cache instance
_distributed_cache: Optional[DistributedCacheCluster] = None

def get_distributed_cache() -> Optional[DistributedCacheCluster]:
    """Get global distributed cache instance"""
    return _distributed_cache

def initialize_distributed_cache(nodes: List[CacheNode], 
                                strategy: CacheStrategy = CacheStrategy.CONSISTENT_HASHING) -> DistributedCacheCluster:
    """Initialize global distributed cache"""
    global _distributed_cache
    _distributed_cache = DistributedCacheCluster(nodes, strategy)
    return _distributed_cache