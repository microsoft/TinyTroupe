# TinyTroupe Architecture Changes for Major Expansion

## Overview

This document outlines the architectural changes required to support the major multi-part expansion of TinyTroupe. These changes maintain backward compatibility where possible while enabling significant new capabilities.

---

## Current Architecture (v0.5.x)

### Component Overview
```
TinyTroupe (Current)
├── Agent Layer
│   ├── TinyPerson (core agent)
│   ├── Memory (episodic, semantic)
│   ├── ActionGenerator
│   └── MentalFaculty (base)
├── Environment Layer
│   ├── TinyWorld (base)
│   └── TinySocialNetwork
├── Control Layer
│   ├── Simulation (state mgmt)
│   └── Caching
├── Tools Layer
│   ├── TinyTool (base)
│   ├── TinyWordProcessor
│   └── TinyCalendar
└── Utilities
    ├── LLM interface
    ├── Config management
    └── Validation
```

### Current Strengths
- ✅ Clean separation of concerns
- ✅ Modular component design
- ✅ Extensible base classes
- ✅ Well-defined interfaces

### Current Limitations
- ❌ Sequential execution model
- ❌ Unbounded memory growth
- ❌ Limited tool ecosystem
- ❌ No multi-modal support
- ❌ Basic caching strategy

---

## Target Architecture (v1.0.0)

### Enhanced Component Overview
```
TinyTroupe (Enhanced)
├── Agent Layer (Enhanced)
│   ├── TinyPerson (core)
│   ├── Memory System (Advanced)
│   │   ├── EpisodicMemory (bounded)
│   │   ├── SemanticMemory (indexed)
│   │   ├── MemoryRetrieval (relevance-based)
│   │   ├── Consolidation (automatic)
│   │   └── Forgetting (realistic decay)
│   ├── Perception (Multi-Modal)
│   │   ├── TextPerception
│   │   ├── VisualPerception (new)
│   │   └── AudioPerception (future)
│   ├── Cognition (Enhanced)
│   │   ├── ActionGenerator (parallel)
│   │   ├── EmotionalState (new)
│   │   ├── KnowledgeSynthesis (new)
│   │   └── MentalFaculty (base)
│   └── Loop Detection (advanced)
├── Environment Layer (Expanded)
│   ├── TinyWorld (parallel execution)
│   ├── SpatialWorld (new base)
│   │   ├── TinyRetailStore
│   │   └── Physical layouts
│   ├── Specialized Worlds (new)
│   │   ├── TinyMarketplace
│   │   ├── TinyWorkplace
│   │   ├── TinyClassroom
│   │   └── TinyHospital
│   ├── EventScheduler (new)
│   └── TemporalDynamics (new)
├── Control Layer (Enhanced)
│   ├── Simulation (multi-instance)
│   ├── Caching (LRU + semantic)
│   ├── Parallel Execution Manager (new)
│   └── Resource Monitor (new)
├── Tools Layer (Expanded)
│   ├── TinyTool (standardized)
│   ├── ToolRegistry (new)
│   ├── Core Tools
│   │   ├── TinyWordProcessor
│   │   ├── TinyCalendar
│   │   ├── TinyEmail (new)
│   │   ├── TinyWebSearch (new)
│   │   └── TinyDatabase (new)
│   └── ToolComposition (new)
├── Grounding Layer (New)
│   ├── RAGConnector
│   ├── KnowledgeGraph
│   ├── DocumentProcessor
│   └── FactChecker
├── Analysis Layer (New)
│   ├── InsightGenerator
│   ├── PatternDetection
│   ├── CausalAnalysis
│   └── StatisticalTests
├── Visualization Layer (Enhanced)
│   ├── Dashboard (web-based)
│   ├── NetworkViz
│   ├── TimelineViz
│   ├── SpatialViz
│   └── MemoryViz
└── Developer Tools (New)
    ├── Debugger
    ├── StateInspector
    ├── MockLLM
    └── Profiler
```

---

## Key Architectural Changes

### 1. Memory Architecture Overhaul

#### Current State
```python
class TinyPerson:
    def __init__(self):
        self.episodic_memory = EpisodicMemory()  # Unbounded list
        self.semantic_memory = SemanticMemory()  # Simple index
```

#### Enhanced State
```python
class TinyPerson:
    def __init__(self, memory_config=None):
        # Tiered memory system with automatic management
        self.memory_manager = MemoryManager(config=memory_config)

        # Hot tier: Recent, frequently accessed
        self.episodic_memory = BoundedEpisodicMemory(
            max_size=config.max_episodic_size,
            eviction_policy="relevance"
        )

        # Warm tier: Consolidated knowledge
        self.semantic_memory = SemanticMemory(
            index_type="vector",
            auto_consolidate=True
        )

        # Cold tier: Compressed historical data
        self.archive = MemoryArchive(
            compression="summarization",
            storage="disk"
        )

        # Advanced retrieval
        self.memory_retrieval = MemoryRetrieval(
            strategies=["recency", "relevance", "importance"]
        )
```

**Changes Required**:
- Add `MemoryManager` class for lifecycle management
- Implement `BoundedEpisodicMemory` with configurable limits
- Create `MemoryArchive` for long-term storage
- Develop `MemoryRetrieval` with multiple strategies
- Add automatic consolidation triggers

**Migration Path**:
- Phase 1: Add bounds to existing memory (backward compatible)
- Phase 2: Introduce tiered architecture (opt-in)
- Phase 3: Make tiered default (v1.0.0)

---

### 2. Parallel Execution Framework

#### Current State
```python
class TinyWorld:
    def _step(self):
        # Sequential execution
        for agent in self.agents:
            agent.act()  # Blocking call
```

#### Enhanced State
```python
class TinyWorld:
    def __init__(self, parallel_execution=False, max_workers=None):
        self.parallel_execution = parallel_execution
        self.executor = None
        if parallel_execution:
            self.executor = ThreadPoolExecutor(
                max_workers=max_workers or os.cpu_count()
            )
        self.dependency_graph = DependencyGraph()

    def _step(self):
        if self.parallel_execution:
            return self._parallel_step()
        else:
            return self._sequential_step()

    def _parallel_step(self):
        # Group agents by dependencies
        agent_groups = self.dependency_graph.get_independent_groups(
            self.agents
        )

        # Execute each group in parallel
        for group in agent_groups:
            futures = []
            for agent in group:
                future = self.executor.submit(agent.act)
                futures.append(future)

            # Wait for group completion
            for future in futures:
                future.result()

    def _sequential_step(self):
        # Original sequential logic (backward compatible)
        for agent in self.agents:
            agent.act()
```

**Changes Required**:
- Add `parallel_execution` configuration option
- Implement `DependencyGraph` to detect agent interactions
- Create thread-safe agent action execution
- Add execution result aggregation
- Implement deterministic mode for testing

**Migration Path**:
- Phase 1: Add parallel execution as opt-in feature
- Phase 2: Make parallel default for >5 agents
- Phase 3: Deprecate forced sequential mode

---

### 3. Tool Ecosystem Standardization

#### Current State
```python
class TinyTool:
    def __init__(self, name, owner):
        self.name = name
        self.owner = owner

    def process_action(self, action):
        # Custom implementation per tool
        pass
```

#### Enhanced State
```python
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class ToolParameter(BaseModel):
    """Standardized parameter definition"""
    name: str
    type: str
    required: bool = True
    description: str
    default: Optional[Any] = None

class ToolCapability(BaseModel):
    """Tool capability declaration"""
    name: str
    description: str
    parameters: List[ToolParameter]
    returns: str

class TinyTool(ABC):
    """Enhanced base class with standardized interface"""

    def __init__(self, name: str, owner: 'TinyPerson'):
        self.name = name
        self.owner = owner
        self.capabilities = self._declare_capabilities()
        ToolRegistry.register(self)

    @abstractmethod
    def _declare_capabilities(self) -> List[ToolCapability]:
        """Declare what this tool can do"""
        pass

    @abstractmethod
    def execute(self, capability: str, parameters: Dict[str, Any]) -> Any:
        """Execute a capability with validated parameters"""
        pass

    def validate_parameters(self, capability: str, parameters: Dict) -> bool:
        """Validate parameters against capability definition"""
        cap = self.get_capability(capability)
        # Pydantic validation
        return True

class ToolRegistry:
    """Global tool registry for discovery"""
    _tools: Dict[str, Type[TinyTool]] = {}

    @classmethod
    def register(cls, tool: TinyTool):
        cls._tools[tool.name] = tool

    @classmethod
    def discover(cls, capability: str) -> List[TinyTool]:
        """Find tools with specific capability"""
        return [t for t in cls._tools.values()
                if t.has_capability(capability)]
```

**Changes Required**:
- Add Pydantic models for parameter validation
- Create `ToolCapability` declaration system
- Implement `ToolRegistry` for discovery
- Standardize `execute()` interface
- Add parameter validation framework

**Migration Path**:
- Phase 1: Create new base class (old still works)
- Phase 2: Refactor existing tools to new interface
- Phase 3: Deprecate old interface

---

### 4. Multi-Modal Perception Layer

#### New Architecture
```python
class Perception(ABC):
    """Base class for perception modalities"""

    @abstractmethod
    def perceive(self, stimulus: Any) -> PerceptionResult:
        pass

class VisualPerception(Perception):
    """Vision-based perception using GPT-4 Vision"""

    def __init__(self, agent: 'TinyPerson'):
        self.agent = agent
        self.vision_client = VisionLLMClient()

    def perceive(self, image: Union[str, bytes]) -> PerceptionResult:
        # Generate visual description
        description = self.vision_client.describe_image(
            image,
            context=self.agent.current_context
        )

        # Store in visual memory
        self.agent.memory_manager.store_visual_memory(
            image=image,
            description=description,
            timestamp=time.time()
        )

        return PerceptionResult(
            modality="visual",
            content=description,
            raw_data=image
        )

class TinyPerson:
    def __init__(self):
        # Add perception systems
        self.perception = {
            'text': TextPerception(self),
            'visual': VisualPerception(self),
            # 'audio': AudioPerception(self),  # Future
        }

    def see(self, image: Union[str, bytes]) -> PerceptionResult:
        """Process visual input"""
        return self.perception['visual'].perceive(image)
```

**Changes Required**:
- Create `Perception` base class
- Implement `VisualPerception` with GPT-4V
- Add `MultiModalMemory` storage
- Extend action generator to use visual context
- Update prompts to incorporate visual information

**Migration Path**:
- Phase 1: Add perception layer (opt-in)
- Phase 2: Integrate with memory and actions
- Phase 3: Add to default agent capabilities

---

### 5. Advanced Caching System

#### Current State
```python
class Simulation:
    def _hash_dict(self, d):
        return str(d)  # Simple but problematic

    # File-based caching, no size limits
```

#### Enhanced State
```python
from functools import lru_cache
import pickle
import hashlib

class CacheKey:
    """Deterministic cache key generation"""

    @staticmethod
    def from_object(obj: Any) -> str:
        # Canonical serialization
        serialized = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        return hashlib.sha256(serialized).hexdigest()

class SemanticCache:
    """Embedding-based cache for similar queries"""

    def __init__(self, similarity_threshold=0.95):
        self.cache = {}
        self.embeddings = {}
        self.similarity_threshold = similarity_threshold

    def get(self, key: str, embedding: np.ndarray) -> Optional[Any]:
        # Exact match first
        if key in self.cache:
            return self.cache[key]

        # Semantic similarity search
        for cached_key, cached_embedding in self.embeddings.items():
            similarity = cosine_similarity(embedding, cached_embedding)
            if similarity >= self.similarity_threshold:
                return self.cache[cached_key]

        return None

    def set(self, key: str, value: Any, embedding: np.ndarray):
        self.cache[key] = value
        self.embeddings[key] = embedding

class LRUCache:
    """Size-limited cache with LRU eviction"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            # Move to end (most recent)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: Any):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            self.cache[key] = value
            if len(self.cache) > self.max_size:
                # Remove least recently used
                self.cache.popitem(last=False)

class CacheManager:
    """Unified cache management"""

    def __init__(self, config: CacheConfig):
        self.lru_cache = LRUCache(max_size=config.max_size)
        self.semantic_cache = SemanticCache(
            similarity_threshold=config.semantic_threshold
        )
        self.config = config

    def get(self, key: str, embedding: Optional[np.ndarray] = None):
        # Try LRU first (exact match)
        result = self.lru_cache.get(key)
        if result is not None:
            return result

        # Try semantic cache if embedding provided
        if embedding is not None and self.config.use_semantic:
            result = self.semantic_cache.get(key, embedding)

        return result
```

**Changes Required**:
- Implement deterministic serialization
- Create LRU cache with size limits
- Add semantic similarity caching
- Build unified cache manager
- Add cache analytics and monitoring

**Migration Path**:
- Phase 1: Add deterministic keys (backward compatible)
- Phase 2: Introduce LRU caching
- Phase 3: Add semantic caching (opt-in)

---

### 6. Grounding and RAG Integration

#### New Architecture
```python
class GroundingConnector(ABC):
    """Base class for knowledge grounding"""

    @abstractmethod
    def query(self, query: str, context: Dict) -> GroundingResult:
        pass

class RAGConnector(GroundingConnector):
    """Retrieval-Augmented Generation connector"""

    def __init__(self, index_path: str, llm_client: LLMClient):
        from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader

        # Load documents
        documents = SimpleDirectoryReader(index_path).load_data()

        # Create index
        self.index = GPTVectorStoreIndex.from_documents(documents)
        self.query_engine = self.index.as_query_engine()

    def query(self, query: str, context: Dict) -> GroundingResult:
        # Retrieve relevant documents
        response = self.query_engine.query(query)

        return GroundingResult(
            answer=response.response,
            sources=response.source_nodes,
            confidence=response.metadata.get('confidence', 0.0)
        )

class KnowledgeGraphConnector(GroundingConnector):
    """Knowledge graph-based grounding"""

    def __init__(self, graph_uri: str):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(graph_uri)

    def query(self, query: str, context: Dict) -> GroundingResult:
        # Extract entities from query
        entities = self.extract_entities(query)

        # Query knowledge graph
        with self.driver.session() as session:
            result = session.run(
                "MATCH (e:Entity)-[r]->(t:Entity) "
                "WHERE e.name IN $entities "
                "RETURN e, r, t",
                entities=entities
            )

        return GroundingResult(
            answer=self.synthesize_answer(result),
            sources=result,
            confidence=0.8
        )

class TinyPerson:
    def __init__(self, grounding: Optional[GroundingConnector] = None):
        self.grounding = grounding or RAGConnector(
            index_path="./knowledge_base"
        )

    def _enrich_context_with_knowledge(self, query: str) -> str:
        if self.grounding:
            grounding_result = self.grounding.query(
                query,
                context=self.get_current_context()
            )
            return grounding_result.answer
        return ""
```

**Changes Required**:
- Create `GroundingConnector` base class
- Implement `RAGConnector` with LlamaIndex
- Build `KnowledgeGraphConnector`
- Integrate grounding into action generation
- Add confidence scoring

**Migration Path**:
- Phase 1: Add grounding as optional feature
- Phase 2: Integrate into prompts and actions
- Phase 3: Make RAG default for knowledge-intensive scenarios

---

## Configuration Changes

### Enhanced Config Structure

```ini
[OpenAI]
# Existing settings...

[Memory]
# New section for memory management
max_episodic_memory_size = 1000
auto_consolidate = true
consolidation_threshold = 500
consolidation_strategy = relevance
enable_forgetting = true
forgetting_curve = ebbinghaus
memory_retrieval_strategy = hybrid

[Parallel]
# New section for parallel execution
enable_parallel_execution = false
max_workers = 8
dependency_detection = automatic
deterministic_mode = false

[Cache]
# Enhanced caching settings
max_cache_size = 10000
cache_eviction_policy = lru
enable_semantic_caching = false
semantic_similarity_threshold = 0.95
cache_compression = true

[Tools]
# New section for tools
auto_discover = true
tool_timeout = 30
enable_composition = true

[Grounding]
# New section for knowledge grounding
enable_rag = false
rag_index_path = ./knowledge_base
rag_similarity_top_k = 5
enable_knowledge_graph = false
kg_uri = bolt://localhost:7687

[Visualization]
# New section for visualization
enable_dashboard = false
dashboard_port = 8501
realtime_updates = true

[Development]
# New section for development tools
enable_debugger = false
enable_profiler = false
use_mock_llm = false
log_level = INFO
```

---

## Database Schema Changes

### New Tables/Collections

```sql
-- Memory Archive (if using SQL backend)
CREATE TABLE memory_archive (
    id UUID PRIMARY KEY,
    agent_id VARCHAR(255),
    memory_type VARCHAR(50),
    content TEXT,
    embedding VECTOR(1536),
    importance FLOAT,
    timestamp TIMESTAMP,
    access_count INT,
    last_accessed TIMESTAMP,
    compressed BOOLEAN,
    INDEX idx_agent_time (agent_id, timestamp),
    INDEX idx_embedding (embedding) -- Vector index
);

-- Visual Memories (if using SQL backend)
CREATE TABLE visual_memories (
    id UUID PRIMARY KEY,
    agent_id VARCHAR(255),
    image_path VARCHAR(500),
    description TEXT,
    embedding VECTOR(1536),
    timestamp TIMESTAMP,
    associated_episodic_memory UUID,
    FOREIGN KEY (associated_episodic_memory) REFERENCES episodic_memories(id)
);

-- Tool Usage Log
CREATE TABLE tool_usage (
    id UUID PRIMARY KEY,
    agent_id VARCHAR(255),
    tool_name VARCHAR(100),
    capability VARCHAR(100),
    parameters JSONB,
    result JSONB,
    success BOOLEAN,
    execution_time_ms INT,
    timestamp TIMESTAMP
);
```

---

## API Changes

### Breaking Changes (v1.0.0)

1. **Memory API**
   ```python
   # Old
   agent.store_in_memory("Some content")

   # New
   agent.memory_manager.store(
       content="Some content",
       memory_type="episodic",
       importance=0.8
   )
   ```

2. **Tool API**
   ```python
   # Old
   tool.process_action(action)

   # New
   tool.execute(
       capability="write_document",
       parameters={"title": "Doc", "content": "Text"}
   )
   ```

3. **World Execution**
   ```python
   # Old
   world.run(steps=10)

   # New (backward compatible with warning)
   world.run(
       steps=10,
       parallel=True,  # New parameter
       max_workers=4   # New parameter
   )
   ```

### New APIs

1. **Perception API**
   ```python
   agent.see(image_path="product.jpg")
   agent.hear(audio_path="review.mp3")  # Future
   ```

2. **Grounding API**
   ```python
   agent.ground_to_knowledge(
       source="documents/",
       type="rag"
   )
   ```

3. **Emotional API**
   ```python
   agent.emotional_state.get_current()
   agent.emotional_state.update(event="positive_feedback")
   ```

---

## Deployment Architecture Changes

### Current Deployment
```
User Code → TinyTroupe Library → LLM API
```

### Enhanced Deployment
```
User Code
    ↓
TinyTroupe Core
    ├→ LLM API (text)
    ├→ Vision API (images)
    ├→ Vector DB (RAG)
    ├→ Graph DB (knowledge)
    ├→ Cache Layer
    │   ├→ In-Memory (LRU)
    │   ├→ Disk (Archive)
    │   └→ Redis (Distributed) [Optional]
    └→ Web Dashboard [Optional]
```

---

## Migration Strategy

### Phase 1: Backward Compatible Additions
- Add new features as opt-in
- Maintain existing APIs
- Deprecation warnings for future changes

### Phase 2: Parallel Support
- Both old and new APIs work
- Migration guides published
- Automated migration tools

### Phase 3: Breaking Changes (v1.0.0)
- Remove deprecated APIs
- Full transition to new architecture
- Legacy mode available for 6 months

---

## Risk Mitigation

### Technical Risks

1. **Performance Regression**
   - Mitigation: Continuous benchmarking
   - Fallback: Sequential mode always available

2. **Memory Leaks**
   - Mitigation: Extensive testing, profiling
   - Monitoring: Built-in memory tracking

3. **API Complexity**
   - Mitigation: Maintain simple defaults
   - Documentation: Comprehensive examples

### Operational Risks

1. **Increased Dependencies**
   - Mitigation: Optional dependencies
   - Fallbacks: Core functionality works without extras

2. **Configuration Complexity**
   - Mitigation: Sensible defaults
   - Validation: Pydantic-based config validation

---

## Success Criteria

### Performance Metrics
- 50%+ reduction in simulation time (parallel mode)
- 70%+ reduction in memory usage (with bounds)
- 30%+ improvement in cache hit rate

### Quality Metrics
- 95%+ test coverage
- Zero critical security vulnerabilities
- <5% regression in existing functionality

### Adoption Metrics
- 80%+ of users successfully migrate
- <10% increase in support questions
- Positive community feedback

---

*Document Version: 1.0*
*Last Updated: 2025-11-16*
*Status: Ready for Review and Implementation*
