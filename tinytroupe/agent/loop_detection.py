"""
Enhanced loop detection utilities for TinyPerson agents.
"""
import json
import logging
from typing import List, Dict, Any, Tuple
from collections import deque
import difflib

logger = logging.getLogger("tinytroupe")


class ActionPattern:
    """Represents a pattern of actions for loop detection."""
    
    def __init__(self, actions: List[Dict], pattern_type: str):
        self.actions = actions
        self.pattern_type = pattern_type
        self.count = 1
        
    def matches(self, recent_actions: List[Dict]) -> bool:
        """Check if recent actions match this pattern."""
        if len(recent_actions) < len(self.actions):
            return False
            
        # Compare the last N actions with the pattern
        to_compare = recent_actions[-len(self.actions):]
        return self._actions_similar(to_compare, self.actions)
    
    def _actions_similar(self, actions1: List[Dict], actions2: List[Dict], 
                        threshold: float = 0.9) -> bool:
        """Check if two action sequences are similar."""
        if len(actions1) != len(actions2):
            return False
            
        similarities = []
        for a1, a2 in zip(actions1, actions2):
            # Convert actions to strings for comparison
            str1 = json.dumps(a1, sort_keys=True)
            str2 = json.dumps(a2, sort_keys=True)
            
            # Use difflib to compute similarity
            similarity = difflib.SequenceMatcher(None, str1, str2).ratio()
            similarities.append(similarity)
        
        # Pattern matches if average similarity is above threshold
        avg_similarity = sum(similarities) / len(similarities)
        return avg_similarity >= threshold


class AdvancedLoopDetector:
    """
    Advanced loop detection system for TinyPerson agents.
    
    Detects various types of loops:
    1. Identical action loops (exact repetition)
    2. Similar action loops (slight variations)
    3. Alternating patterns (A-B-A-B...)
    4. Complex patterns (A-B-C-A-B-C...)
    5. State-based loops (same action in same context)
    """
    
    def __init__(self, max_history: int = 50, similarity_threshold: float = 0.85):
        self.max_history = max_history
        self.similarity_threshold = similarity_threshold
        self.action_history = deque(maxlen=max_history)
        self.detected_patterns = []
        self.state_cache = {}
        
    def add_action(self, action: Dict, context: Dict = None):
        """Add a new action to the history."""
        action_entry = {
            'action': action,
            'context': context or {},
            'timestamp': len(self.action_history)
        }
        self.action_history.append(action_entry)
        
    def detect_loops(self) -> Tuple[bool, str, List[Dict]]:
        """
        Detect if agent is in a loop.
        
        Returns:
            (is_loop, loop_type, problematic_actions)
        """
        if len(self.action_history) < 3:
            return False, "", []
            
        actions = [entry['action'] for entry in self.action_history]
        
        # 1. Check for identical action loops
        loop_detected, loop_type, problematic = self._detect_identical_loops(actions)
        if loop_detected:
            return True, loop_type, problematic
            
        # 2. Check for similar action loops
        loop_detected, loop_type, problematic = self._detect_similar_loops(actions)
        if loop_detected:
            return True, loop_type, problematic
            
        # 3. Check for alternating patterns
        loop_detected, loop_type, problematic = self._detect_alternating_patterns(actions)
        if loop_detected:
            return True, loop_type, problematic
            
        # 4. Check for complex patterns
        loop_detected, loop_type, problematic = self._detect_complex_patterns(actions)
        if loop_detected:
            return True, loop_type, problematic
            
        # 5. Check for state-based loops
        loop_detected, loop_type, problematic = self._detect_state_loops()
        if loop_detected:
            return True, loop_type, problematic
            
        return False, "", []
    
    def _detect_identical_loops(self, actions: List[Dict], min_repetitions: int = 3) -> Tuple[bool, str, List[Dict]]:
        """Detect exact identical action repetitions."""
        if len(actions) < min_repetitions:
            return False, "", []
            
        # Check for consecutive identical actions
        for i in range(len(actions) - min_repetitions + 1):
            action_str = json.dumps(actions[i], sort_keys=True)
            consecutive_count = 1
            
            for j in range(i + 1, len(actions)):
                if json.dumps(actions[j], sort_keys=True) == action_str:
                    consecutive_count += 1
                else:
                    break
                    
            if consecutive_count >= min_repetitions:
                return True, "identical_repetition", actions[i:i+consecutive_count]
                
        return False, "", []
    
    def _detect_similar_loops(self, actions: List[Dict], min_repetitions: int = 3) -> Tuple[bool, str, List[Dict]]:
        """Detect similar (but not identical) action repetitions."""
        if len(actions) < min_repetitions:
            return False, "", []
            
        # Look for patterns of similar actions
        for window_size in range(1, min(6, len(actions) // min_repetitions + 1)):
            for start in range(len(actions) - window_size * min_repetitions + 1):
                pattern = actions[start:start + window_size]
                repetitions = []
                
                current_pos = start
                while current_pos + window_size <= len(actions):
                    candidate = actions[current_pos:current_pos + window_size]
                    if self._patterns_similar(pattern, candidate):
                        repetitions.append(candidate)
                        current_pos += window_size
                    else:
                        break
                        
                if len(repetitions) >= min_repetitions:
                    flat_actions = [action for pattern in repetitions for action in pattern]
                    return True, "similar_repetition", flat_actions
                    
        return False, "", []
    
    def _detect_alternating_patterns(self, actions: List[Dict], min_cycles: int = 3) -> Tuple[bool, str, List[Dict]]:
        """Detect alternating patterns like A-B-A-B-A-B."""
        if len(actions) < min_cycles * 2:
            return False, "", []
            
        # Check for 2-action alternating patterns
        for i in range(len(actions) - min_cycles * 2 + 1):
            action_a = actions[i]
            action_b = actions[i + 1]
            
            # Check if pattern continues
            is_alternating = True
            for j in range(2, min_cycles * 2):
                expected = action_a if j % 2 == 0 else action_b
                actual = actions[i + j]
                
                if not self._actions_similar([actual], [expected]):
                    is_alternating = False
                    break
                    
            if is_alternating:
                return True, "alternating_pattern", actions[i:i + min_cycles * 2]
                
        return False, "", []
    
    def _detect_complex_patterns(self, actions: List[Dict]) -> Tuple[bool, str, List[Dict]]:
        """Detect complex repeating patterns."""
        if len(actions) < 6:
            return False, "", []
            
        # Check for patterns of length 3-8
        for pattern_length in range(3, min(9, len(actions) // 2 + 1)):
            for start in range(len(actions) - pattern_length * 2 + 1):
                pattern = actions[start:start + pattern_length]
                next_pattern = actions[start + pattern_length:start + pattern_length * 2]
                
                if self._patterns_similar(pattern, next_pattern):
                    # Check if pattern repeats once more
                    if start + pattern_length * 3 <= len(actions):
                        third_pattern = actions[start + pattern_length * 2:start + pattern_length * 3]
                        if self._patterns_similar(pattern, third_pattern):
                            return True, "complex_pattern", actions[start:start + pattern_length * 3]
                            
        return False, "", []
    
    def _detect_state_loops(self) -> Tuple[bool, str, List[Dict]]:
        """Detect loops where same actions occur in similar contexts."""
        if len(self.action_history) < 5:
            return False, "", []
            
        # Group actions by type and check for context similarity
        action_groups = {}
        for entry in list(self.action_history)[-10:]:  # Look at last 10 actions
            action_type = entry['action'].get('type', 'unknown')
            if action_type not in action_groups:
                action_groups[action_type] = []
            action_groups[action_type].append(entry)
            
        # Check if any action type has repeated in similar contexts
        for action_type, entries in action_groups.items():
            if len(entries) >= 3:
                # Check context similarity
                contexts = [entry['context'] for entry in entries]
                if self._contexts_similar(contexts):
                    actions = [entry['action'] for entry in entries]
                    return True, "state_loop", actions
                    
        return False, "", []
    
    def _patterns_similar(self, pattern1: List[Dict], pattern2: List[Dict]) -> bool:
        """Check if two patterns are similar."""
        if len(pattern1) != len(pattern2):
            return False
            
        for a1, a2 in zip(pattern1, pattern2):
            if not self._actions_similar([a1], [a2]):
                return False
        return True
    
    def _actions_similar(self, actions1: List[Dict], actions2: List[Dict]) -> bool:
        """Check if actions are similar based on similarity threshold."""
        if len(actions1) != len(actions2):
            return False
            
        for a1, a2 in zip(actions1, actions2):
            str1 = json.dumps(a1, sort_keys=True)
            str2 = json.dumps(a2, sort_keys=True)
            similarity = difflib.SequenceMatcher(None, str1, str2).ratio()
            if similarity < self.similarity_threshold:
                return False
        return True
    
    def _contexts_similar(self, contexts: List[Dict], threshold: float = 0.7) -> bool:
        """Check if contexts are similar."""
        if len(contexts) < 2:
            return False
            
        # Compare each context with the first one
        base_context = json.dumps(contexts[0], sort_keys=True)
        similarities = []
        
        for context in contexts[1:]:
            context_str = json.dumps(context, sort_keys=True)
            similarity = difflib.SequenceMatcher(None, base_context, context_str).ratio()
            similarities.append(similarity)
            
        avg_similarity = sum(similarities) / len(similarities)
        return avg_similarity >= threshold
    
    def get_loop_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected loops."""
        return {
            'total_actions': len(self.action_history),
            'detected_patterns': len(self.detected_patterns),
            'unique_action_types': len(set(entry['action'].get('type', 'unknown') for entry in self.action_history))
        }
    
    def reset(self):
        """Reset the loop detector."""
        self.action_history.clear()
        self.detected_patterns.clear()
        self.state_cache.clear()