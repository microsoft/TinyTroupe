package memory

import (
	"encoding/json"
	"time"
)

// MemoryItem represents a single memory item
type MemoryItem struct {
	Role                string                 `json:"role"`
	Content             map[string]interface{} `json:"content"`
	Type                string                 `json:"type"`
	SimulationTimestamp time.Time              `json:"simulation_timestamp"`
}

// EpisodicMemory manages episodic memories for agents
type EpisodicMemory struct {
	memories       []MemoryItem
	currentEpisode []MemoryItem
	fixedPrefixLen int
	lookbackLen    int
}

// NewEpisodicMemory creates a new episodic memory instance
func NewEpisodicMemory(fixedPrefixLen, lookbackLen int) *EpisodicMemory {
	return &EpisodicMemory{
		memories:       make([]MemoryItem, 0),
		currentEpisode: make([]MemoryItem, 0),
		fixedPrefixLen: fixedPrefixLen,
		lookbackLen:    lookbackLen,
	}
}

// Store adds a memory item to the current episode
func (em *EpisodicMemory) Store(item MemoryItem) {
	em.currentEpisode = append(em.currentEpisode, item)
}

// CommitEpisode commits the current episode to long-term memory
func (em *EpisodicMemory) CommitEpisode() {
	if len(em.currentEpisode) > 0 {
		em.memories = append(em.memories, em.currentEpisode...)
		em.currentEpisode = make([]MemoryItem, 0)
	}
}

// RetrieveRecent gets recent memories for prompting
func (em *EpisodicMemory) RetrieveRecent() []MemoryItem {
	allMemories := append(em.memories, em.currentEpisode...)

	if len(allMemories) == 0 {
		return []MemoryItem{}
	}

	// Return fixed prefix + recent lookback
	var result []MemoryItem

	// Add fixed prefix
	prefixEnd := em.fixedPrefixLen
	if prefixEnd > len(allMemories) {
		prefixEnd = len(allMemories)
	}
	result = append(result, allMemories[:prefixEnd]...)

	// Add recent lookback (avoiding overlap)
	if len(allMemories) > em.fixedPrefixLen {
		lookbackStart := len(allMemories) - em.lookbackLen
		if lookbackStart < em.fixedPrefixLen {
			lookbackStart = em.fixedPrefixLen
		}
		result = append(result, allMemories[lookbackStart:]...)
	}

	return result
}

// Clear removes memories (for testing or amnesia)
func (em *EpisodicMemory) Clear() {
	em.memories = make([]MemoryItem, 0)
	em.currentEpisode = make([]MemoryItem, 0)
}

// GetCurrentEpisode returns the current episode
func (em *EpisodicMemory) GetCurrentEpisode() []MemoryItem {
	return em.currentEpisode
}

// ToJSON serializes the memory to JSON
func (em *EpisodicMemory) ToJSON() ([]byte, error) {
	data := struct {
		Memories       []MemoryItem `json:"memories"`
		CurrentEpisode []MemoryItem `json:"current_episode"`
		FixedPrefixLen int          `json:"fixed_prefix_len"`
		LookbackLen    int          `json:"lookback_len"`
	}{
		Memories:       em.memories,
		CurrentEpisode: em.currentEpisode,
		FixedPrefixLen: em.fixedPrefixLen,
		LookbackLen:    em.lookbackLen,
	}
	return json.Marshal(data)
}

// FromJSON deserializes memory from JSON
func (em *EpisodicMemory) FromJSON(data []byte) error {
	var temp struct {
		Memories       []MemoryItem `json:"memories"`
		CurrentEpisode []MemoryItem `json:"current_episode"`
		FixedPrefixLen int          `json:"fixed_prefix_len"`
		LookbackLen    int          `json:"lookback_len"`
	}

	if err := json.Unmarshal(data, &temp); err != nil {
		return err
	}

	em.memories = temp.Memories
	em.currentEpisode = temp.CurrentEpisode
	em.fixedPrefixLen = temp.FixedPrefixLen
	em.lookbackLen = temp.LookbackLen

	return nil
}

// SemanticMemory manages semantic/long-term memories
type SemanticMemory struct {
	memories []string
}

// NewSemanticMemory creates a new semantic memory instance
func NewSemanticMemory() *SemanticMemory {
	return &SemanticMemory{
		memories: make([]string, 0),
	}
}

// Store adds a semantic memory
func (sm *SemanticMemory) Store(memory string) {
	sm.memories = append(sm.memories, memory)
}

// StoreAll adds multiple semantic memories
func (sm *SemanticMemory) StoreAll(memories []string) {
	sm.memories = append(sm.memories, memories...)
}

// RetrieveRelevant finds relevant memories (simplified version)
func (sm *SemanticMemory) RetrieveRelevant(query string, topK int) []string {
	// TODO: Implement proper semantic search with embeddings
	// For now, return most recent memories
	start := len(sm.memories) - topK
	if start < 0 {
		start = 0
	}
	return sm.memories[start:]
}

// ToJSON serializes semantic memory to JSON
func (sm *SemanticMemory) ToJSON() ([]byte, error) {
	return json.Marshal(sm.memories)
}

// FromJSON deserializes semantic memory from JSON
func (sm *SemanticMemory) FromJSON(data []byte) error {
	return json.Unmarshal(data, &sm.memories)
}
