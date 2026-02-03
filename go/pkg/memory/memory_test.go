package memory

import (
	"testing"
	"time"
)

func TestEpisodicMemoryBasics(t *testing.T) {
	memory := NewEpisodicMemory(5, 10)

	// Test empty memory
	recent := memory.RetrieveRecent()
	if len(recent) != 0 {
		t.Errorf("Expected empty memory, got %d items", len(recent))
	}

	// Add some memories
	for i := 0; i < 3; i++ {
		item := MemoryItem{
			Role:                "user",
			Content:             map[string]interface{}{"test": i},
			Type:                "stimulus",
			SimulationTimestamp: time.Now(),
		}
		memory.Store(item)
	}

	// Check current episode
	episode := memory.GetCurrentEpisode()
	if len(episode) != 3 {
		t.Errorf("Expected 3 items in current episode, got %d", len(episode))
	}

	// Commit episode
	memory.CommitEpisode()

	// Check that episode was committed
	if len(memory.memories) != 3 {
		t.Errorf("Expected 3 committed memories, got %d", len(memory.memories))
	}

	if len(memory.GetCurrentEpisode()) != 0 {
		t.Errorf("Expected empty current episode after commit")
	}
}

func TestEpisodicMemoryRetrieval(t *testing.T) {
	memory := NewEpisodicMemory(2, 3)

	// Add more memories than the limits
	for i := 0; i < 10; i++ {
		item := MemoryItem{
			Role:                "user",
			Content:             map[string]interface{}{"index": i},
			Type:                "stimulus",
			SimulationTimestamp: time.Now(),
		}
		memory.Store(item)
	}

	recent := memory.RetrieveRecent()

	// Should get prefix (2) + lookback (3) = 5 items maximum
	// But since we have 10 items total, we should get 2 (prefix) + 3 (recent) = 5
	if len(recent) > 5 {
		t.Errorf("Expected at most 5 recent items, got %d", len(recent))
	}

	// Check that we get the first 2 (prefix) and last 3 (lookback)
	if len(recent) > 0 {
		// First item should be index 0
		if content, ok := recent[0].Content["index"].(int); !ok || content != 0 {
			t.Errorf("Expected first item to have index 0")
		}

		// Last item should be index 9
		if content, ok := recent[len(recent)-1].Content["index"].(int); !ok || content != 9 {
			t.Errorf("Expected last item to have index 9")
		}
	}
}

func TestSemanticMemoryBasics(t *testing.T) {
	memory := NewSemanticMemory()

	// Test empty memory
	relevant := memory.RetrieveRelevant("test query", 5)
	if len(relevant) != 0 {
		t.Errorf("Expected empty memory, got %d items", len(relevant))
	}

	// Add some memories
	memories := []string{
		"Alice likes programming",
		"Bob enjoys cooking",
		"Charlie loves reading",
		"Diana practices music",
	}

	memory.StoreAll(memories)

	// Test retrieval (should return most recent)
	relevant = memory.RetrieveRelevant("test query", 2)
	if len(relevant) != 2 {
		t.Errorf("Expected 2 relevant memories, got %d", len(relevant))
	}

	// Should return the last 2 memories
	expected := []string{"Charlie loves reading", "Diana practices music"}
	for i, expected_item := range expected {
		if relevant[i] != expected_item {
			t.Errorf("Expected '%s', got '%s'", expected_item, relevant[i])
		}
	}
}

func TestMemorySerialization(t *testing.T) {
	// Test episodic memory serialization
	episodic := NewEpisodicMemory(2, 3)
	item := MemoryItem{
		Role:                "user",
		Content:             map[string]interface{}{"test": "data"},
		Type:                "stimulus",
		SimulationTimestamp: time.Now(),
	}
	episodic.Store(item)

	data, err := episodic.ToJSON()
	if err != nil {
		t.Fatalf("Failed to serialize episodic memory: %v", err)
	}

	newEpisodic := NewEpisodicMemory(0, 0)
	err = newEpisodic.FromJSON(data)
	if err != nil {
		t.Fatalf("Failed to deserialize episodic memory: %v", err)
	}

	if len(newEpisodic.GetCurrentEpisode()) != 1 {
		t.Errorf("Expected 1 item after deserialization, got %d", len(newEpisodic.GetCurrentEpisode()))
	}

	// Test semantic memory serialization
	semantic := NewSemanticMemory()
	semantic.Store("test memory")

	data, err = semantic.ToJSON()
	if err != nil {
		t.Fatalf("Failed to serialize semantic memory: %v", err)
	}

	newSemantic := NewSemanticMemory()
	err = newSemantic.FromJSON(data)
	if err != nil {
		t.Fatalf("Failed to deserialize semantic memory: %v", err)
	}

	if len(newSemantic.memories) != 1 || newSemantic.memories[0] != "test memory" {
		t.Errorf("Semantic memory not properly deserialized")
	}
}
