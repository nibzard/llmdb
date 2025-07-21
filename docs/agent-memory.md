# AI Agent Memory Guide

This guide demonstrates how to use LLMDB as a sophisticated memory store for AI coding agents, leveraging bitemporal capabilities for decision tracking, knowledge evolution, and context management.

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Agent Memory Patterns](#agent-memory-patterns) 
3. [Temporal Queries for Agents](#temporal-queries-for-agents)
4. [Implementation Examples](#implementation-examples)
5. [Best Practices](#best-practices)
6. [Advanced Patterns](#advanced-patterns)

## Core Concepts

LLMDB's bitemporal model provides two critical time dimensions for AI agents:

- **Valid Time**: When information was true in the real world
- **Transaction Time**: When the agent recorded the information

This enables agents to:
- Track the evolution of their understanding
- Handle corrections without losing history
- Query "what did I know when" for debugging
- Maintain complete audit trails of decisions

### Key Benefits for AI Agents

1. **Decision Auditability**: Complete history of agent reasoning and choices
2. **Knowledge Evolution**: Track how understanding improves over time
3. **Context Preservation**: Maintain conversation state across sessions
4. **Error Recovery**: Rollback to previous good states
5. **Learning from History**: Analyze past decisions to improve future ones

## Agent Memory Patterns

### 1. Code Analysis Storage

Store evolving understanding of codebases with correction trails:

```python
from llmdb import KV
from llmdb.temporal_key import Key
from llmdb.kv._codec import JSONValue
from datetime import datetime
import hashlib

class CodeAnalysisMemory:
    def __init__(self, db_path: str):
        self.db = KV(db_path)
    
    def store_analysis(self, file_path: str, analysis: dict, timestamp: datetime = None):
        """Store code analysis with temporal tracking"""
        if timestamp is None:
            timestamp = datetime.now()
            
        file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
        key = Key(
            partition=0,
            user_key=f"agent:analysis:{file_hash}",
            valid_from=int(timestamp.timestamp() * 1_000_000)
        )
        
        analysis_data = {
            "file_path": file_path,
            "timestamp": timestamp.isoformat(),
            "confidence": analysis.get("confidence", 0.5),
            **analysis
        }
        
        self.db.put(key, JSONValue(payload=analysis_data))
        
    def get_current_analysis(self, file_path: str):
        """Get latest analysis for a file"""
        file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
        key = Key(partition=0, user_key=f"agent:analysis:{file_hash}")
        result = self.db.get(key)
        return result.payload if result else None
        
    def get_analysis_evolution(self, file_path: str):
        """Track how understanding of a file evolved"""
        file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
        versions = []
        prefix = f"agent:analysis:{file_hash}".encode()
        
        for key, value in self.db.items():
            if key.user_key.startswith(prefix):
                valid_time = datetime.fromtimestamp(key.valid_from / 1_000_000)
                versions.append({
                    "valid_time": valid_time,
                    "tx_id": key.tx_id,
                    "analysis": value.payload
                })
        
        return sorted(versions, key=lambda x: x["valid_time"])

# Usage Example
analysis_mem = CodeAnalysisMemory("./agent_memory.db")

# Initial analysis
analysis_mem.store_analysis("src/auth/login.py", {
    "complexity_score": 8.5,
    "dependencies": ["bcrypt", "jwt"],
    "patterns": ["factory", "decorator"],
    "issues": ["missing_error_handling", "hardcoded_timeout"],
    "confidence": 0.75
})

# Corrected analysis after deeper inspection
analysis_mem.store_analysis("src/auth/login.py", {
    "complexity_score": 7.2,  # Revised down
    "dependencies": ["bcrypt", "jwt", "redis"],  # Found hidden dependency
    "patterns": ["factory", "decorator", "singleton"],
    "issues": ["missing_error_handling"],  # Timeout was configurable
    "confidence": 0.90,
    "correction_reason": "Found configuration-driven timeout, hidden Redis dependency"
})
```

### 2. Decision History with Reasoning

Track agent decisions with complete context and reasoning:

```python
class DecisionMemory:
    def __init__(self, db_path: str):
        self.db = KV(db_path)
    
    def record_decision(self, task_id: str, decision: dict, timestamp: datetime = None):
        """Record a decision with full context"""
        if timestamp is None:
            timestamp = datetime.now()
            
        key = Key(
            partition=0,
            user_key=f"agent:decision:{task_id}",
            valid_from=int(timestamp.timestamp() * 1_000_000)
        )
        
        decision_record = {
            "timestamp": timestamp.isoformat(),
            "task_id": task_id,
            "decision": decision["decision"],
            "reasoning": decision.get("reasoning", []),
            "alternatives_considered": decision.get("alternatives", []),
            "confidence": decision.get("confidence", 0.5),
            "context": decision.get("context", {}),
            "dependencies": decision.get("dependencies", [])
        }
        
        self.db.put(key, JSONValue(payload=decision_record))
        
    def get_decision_history(self, task_id: str):
        """Get complete history of decisions for a task"""
        versions = []
        prefix = f"agent:decision:{task_id}".encode()
        
        for key, value in self.db.items():
            if key.user_key.startswith(prefix):
                versions.append({
                    "valid_time": datetime.fromtimestamp(key.valid_from / 1_000_000),
                    "tx_id": key.tx_id,
                    "decision": value.payload
                })
                
        return sorted(versions, key=lambda x: x["valid_time"])
    
    def rollback_decision(self, task_id: str, rollback_to_tx: int):
        """Mark a decision as rolled back"""
        rollback_key = Key(
            partition=0,
            user_key=f"agent:decision:{task_id}:rollback",
            valid_from=int(datetime.now().timestamp() * 1_000_000)
        )
        
        rollback_record = {
            "status": "rolled_back",
            "rollback_to_transaction": rollback_to_tx,
            "rollback_timestamp": datetime.now().isoformat(),
            "reason": "decision_revision_requested"
        }
        
        self.db.put(rollback_key, JSONValue(payload=rollback_record))

# Usage Example
decision_mem = DecisionMemory("./agent_memory.db")

# Record initial decision
decision_mem.record_decision("refactor_auth", {
    "decision": "Extract authentication logic to separate service",
    "reasoning": [
        "Reduces coupling between auth and business logic",
        "Enables easier testing with mock auth",
        "Follows microservices pattern"
    ],
    "alternatives": [
        "Keep auth inline with better abstractions",
        "Use dependency injection without extraction"
    ],
    "confidence": 0.75,
    "context": {
        "files_analyzed": 23,
        "current_test_coverage": 0.68,
        "estimated_effort_hours": 16,
        "team_size": 3
    },
    "dependencies": ["database_refactor", "api_versioning"]
})

# Later, revise the decision
decision_mem.record_decision("refactor_auth", {
    "decision": "Improve current auth with dependency injection",
    "reasoning": [
        "Lower risk than full service extraction",
        "Achieves testability goals with less work",
        "Team lacks microservices experience"
    ],
    "confidence": 0.85,
    "context": {
        "risk_assessment": "high",
        "timeline_pressure": True,
        "team_feedback": "concerned_about_complexity"
    }
})
```

### 3. Conversation Context Management

Maintain persistent context across agent sessions:

```python
class ConversationMemory:
    def __init__(self, db_path: str):
        self.db = KV(db_path)
    
    def update_context(self, session_id: str, context_update: dict, timestamp: datetime = None):
        """Update conversation context"""
        if timestamp is None:
            timestamp = datetime.now()
            
        key = Key(
            partition=0,
            user_key=f"agent:context:{session_id}",
            valid_from=int(timestamp.timestamp() * 1_000_000)
        )
        
        # Get current context and merge with update
        current = self.get_current_context(session_id)
        if current:
            merged_context = {**current, **context_update}
        else:
            merged_context = context_update
            
        merged_context["last_updated"] = timestamp.isoformat()
        self.db.put(key, JSONValue(payload=merged_context))
        
    def get_current_context(self, session_id: str):
        """Get current conversation context"""
        key = Key(partition=0, user_key=f"agent:context:{session_id}")
        result = self.db.get(key)
        return result.payload if result else None
        
    def get_context_evolution(self, session_id: str):
        """Track how conversation context evolved"""
        versions = []
        prefix = f"agent:context:{session_id}".encode()
        
        for key, value in self.db.items():
            if key.user_key.startswith(prefix):
                versions.append({
                    "timestamp": datetime.fromtimestamp(key.valid_from / 1_000_000),
                    "context": value.payload
                })
                
        return sorted(versions, key=lambda x: x["timestamp"])

# Usage Example  
conv_mem = ConversationMemory("./agent_memory.db")

# Initial context
conv_mem.update_context("session_123", {
    "current_task": "implementing_user_auth",
    "project_root": "/project/myapp",
    "relevant_files": ["src/auth/", "tests/auth/"],
    "user_preferences": {
        "coding_style": "functional_first", 
        "test_framework": "pytest",
        "documentation_level": "detailed"
    },
    "conversation_summary": "Starting authentication implementation"
})

# Update as conversation progresses
conv_mem.update_context("session_123", {
    "current_task": "implementing_jwt_validation",
    "relevant_files": ["src/auth/", "tests/auth/", "config/jwt.py"],
    "conversation_summary": "Decided on JWT approach, discussing validation",
    "pending_questions": [
        "Should we use RS256 or HS256?",
        "Token expiration policy?"
    ]
})
```

## Temporal Queries for Agents

### Knowledge Evolution Tracking

```python
def analyze_knowledge_evolution(db: KV, topic: str):
    """Analyze how agent knowledge evolved over time"""
    
    evolution_data = []
    prefix = f"agent:knowledge:{topic}".encode()
    
    for key, value in db.items():
        if key.user_key.startswith(prefix):
            valid_time = datetime.fromtimestamp(key.valid_from / 1_000_000)
            knowledge = value.payload
            
            evolution_data.append({
                "timestamp": valid_time,
                "tx_id": key.tx_id,
                "confidence": knowledge.get("confidence", 0.5),
                "knowledge": knowledge
            })
    
    # Sort by time and calculate confidence changes
    evolution_data.sort(key=lambda x: x["timestamp"])
    
    for i in range(1, len(evolution_data)):
        prev_conf = evolution_data[i-1]["confidence"]
        curr_conf = evolution_data[i]["confidence"]
        evolution_data[i]["confidence_delta"] = curr_conf - prev_conf
        
    return evolution_data

def get_agent_state_at_time(db: KV, timestamp: datetime, agent_id: str = None):
    """Get complete agent state as of a specific time"""
    
    target_timestamp = int(timestamp.timestamp() * 1_000_000)
    agent_state = {}
    
    # Find all agent data valid at the target time
    for key, value in db.items():
        user_key = key.user_key.decode()
        if user_key.startswith("agent:"):
            if key.valid_from <= target_timestamp:
                # This is the version valid at target time
                category = user_key.split(":")[1]  # context, analysis, decision, etc.
                
                if category not in agent_state:
                    agent_state[category] = {}
                    
                agent_state[category][user_key] = {
                    "data": value.payload,
                    "valid_from": datetime.fromtimestamp(key.valid_from / 1_000_000),
                    "tx_id": key.tx_id
                }
    
    return agent_state
```

### Decision Analysis and Patterns

```python
def analyze_decision_patterns(db: KV):
    """Analyze agent decision patterns and success rates"""
    
    decisions = []
    outcomes = []
    
    # Collect all decisions
    for key, value in db.items():
        user_key = key.user_key.decode()
        if user_key.startswith("agent:decision:") and not user_key.endswith(":rollback"):
            decisions.append({
                "task_id": user_key.split(":")[-1],
                "timestamp": datetime.fromtimestamp(key.valid_from / 1_000_000),
                "decision": value.payload
            })
        elif user_key.endswith(":rollback"):
            outcomes.append({
                "task_id": user_key.split(":")[-2], 
                "outcome": "rolled_back",
                "rollback_data": value.payload
            })
    
    # Analyze patterns
    patterns = {
        "total_decisions": len(decisions),
        "rollback_rate": len(outcomes) / len(decisions) if decisions else 0,
        "confidence_distribution": {},
        "reasoning_patterns": {},
        "success_indicators": {}
    }
    
    # Confidence analysis
    confidences = [d["decision"].get("confidence", 0.5) for d in decisions]
    patterns["confidence_distribution"] = {
        "mean": sum(confidences) / len(confidences) if confidences else 0,
        "min": min(confidences) if confidences else 0,
        "max": max(confidences) if confidences else 0
    }
    
    # Common reasoning patterns
    reasoning_keywords = {}
    for decision in decisions:
        reasoning = decision["decision"].get("reasoning", [])
        for reason in reasoning:
            words = reason.lower().split()
            for word in words:
                if len(word) > 4:  # Skip short words
                    reasoning_keywords[word] = reasoning_keywords.get(word, 0) + 1
    
    patterns["reasoning_patterns"] = dict(sorted(
        reasoning_keywords.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:10])  # Top 10 reasoning keywords
    
    return patterns
```

## Implementation Examples

### Complete AI Agent Memory System

```python
class AIAgentMemory:
    """Complete memory system for AI coding agents"""
    
    def __init__(self, db_path: str, agent_id: str):
        self.db = KV(db_path)
        self.agent_id = agent_id
        
        # Initialize subsystems
        self.code_analysis = CodeAnalysisMemory(db_path)
        self.decisions = DecisionMemory(db_path) 
        self.conversations = ConversationMemory(db_path)
    
    def store_learning(self, domain: str, knowledge: dict, confidence: float = 0.5):
        """Store new learning with confidence tracking"""
        timestamp = datetime.now()
        key = Key(
            partition=0,
            user_key=f"agent:knowledge:{domain}",
            valid_from=int(timestamp.timestamp() * 1_000_000)
        )
        
        learning_record = {
            "agent_id": self.agent_id,
            "domain": domain,
            "knowledge": knowledge,
            "confidence": confidence,
            "learned_at": timestamp.isoformat(),
            "source": "experience"
        }
        
        self.db.put(key, JSONValue(payload=learning_record))
    
    def correct_knowledge(self, domain: str, correction: dict, reason: str):
        """Correct previous knowledge with explanation"""
        # Get current knowledge
        current = self.get_knowledge(domain)
        if not current:
            raise ValueError(f"No knowledge found for domain: {domain}")
        
        # Create corrected version
        corrected_knowledge = {**current["knowledge"], **correction}
        
        timestamp = datetime.now()
        key = Key(
            partition=0,
            user_key=f"agent:knowledge:{domain}",
            valid_from=int(timestamp.timestamp() * 1_000_000)
        )
        
        correction_record = {
            "agent_id": self.agent_id,
            "domain": domain,
            "knowledge": corrected_knowledge,
            "confidence": correction.get("confidence", current["confidence"]),
            "learned_at": timestamp.isoformat(),
            "source": "correction",
            "correction_reason": reason,
            "corrected_from_tx": current["tx_id"] if "tx_id" in current else None
        }
        
        self.db.put(key, JSONValue(payload=correction_record))
    
    def get_knowledge(self, domain: str):
        """Get current knowledge for a domain"""
        key = Key(partition=0, user_key=f"agent:knowledge:{domain}")
        result = self.db.get(key)
        return result.payload if result else None
    
    def debug_agent_state(self, timestamp: datetime = None):
        """Get complete agent state for debugging"""
        if timestamp is None:
            timestamp = datetime.now()
            
        state = get_agent_state_at_time(self.db, timestamp, self.agent_id)
        
        return {
            "agent_id": self.agent_id,
            "state_at": timestamp.isoformat(),
            "knowledge_domains": len(state.get("knowledge", {})),
            "active_conversations": len(state.get("context", {})),
            "decisions_made": len(state.get("decision", {})),
            "files_analyzed": len(state.get("analysis", {})),
            "full_state": state
        }

# Usage Example
agent = AIAgentMemory("./agent_memory.db", "coding_assistant_v1")

# Store initial learning
agent.store_learning("python_testing", {
    "best_practices": ["use_pytest", "mock_external_deps", "test_edge_cases"],
    "common_patterns": ["arrange_act_assert", "given_when_then"],
    "tools": ["pytest", "mock", "coverage"]
}, confidence=0.8)

# Later, correct the knowledge
agent.correct_knowledge("python_testing", {
    "tools": ["pytest", "mock", "coverage", "hypothesis"],  # Add hypothesis
    "best_practices": [
        "use_pytest", 
        "mock_external_deps", 
        "test_edge_cases",
        "property_based_testing"  # Add new practice
    ]
}, reason="Learned about property-based testing with Hypothesis")

# Debug current state
debug_info = agent.debug_agent_state()
print(f"Agent has knowledge in {debug_info['knowledge_domains']} domains")
```

## Best Practices

### 1. Confidence Tracking
Always include confidence scores with agent data:

```python
{
    "data": {...},
    "confidence": 0.85,  # 0.0 to 1.0
    "confidence_reason": "based_on_multiple_sources",
    "confidence_factors": {
        "source_reliability": 0.9,
        "data_completeness": 0.8,
        "cross_validation": 0.85
    }
}
```

### 2. Source Attribution
Track how the agent obtained information:

```python
{
    "data": {...},
    "source": "static_analysis",  # static_analysis, user_input, external_api, etc.
    "source_details": {
        "tool": "ast_parser",
        "version": "1.2.3",
        "timestamp": "2024-07-21T10:30:00Z"
    },
    "reliability": 0.9
}
```

### 3. Dependency Tracking
Record what data depends on other data:

```python
{
    "data": {...},
    "dependencies": [
        "agent:analysis:file1.py",
        "agent:knowledge:python_patterns"
    ],
    "affects": [
        "agent:decision:refactor_auth",
        "agent:progress:project_alpha"
    ]
}
```

### 4. Expiration and Validation
Some agent data may become stale:

```python
{
    "data": {...},
    "expires_at": "2024-08-21T10:30:00Z",  # When this data becomes stale
    "validation_frequency": "daily",        # How often to revalidate
    "last_validated": "2024-07-21T10:30:00Z"
}
```

### 5. Memory Cleanup
Implement strategies for managing memory size:

```python
def cleanup_old_data(db: KV, retention_days: int = 30):
    """Remove old, low-confidence data to manage memory size"""
    
    cutoff_timestamp = int(
        (datetime.now() - timedelta(days=retention_days)).timestamp() * 1_000_000
    )
    
    to_delete = []
    for key, value in db.items():
        user_key = key.user_key.decode()
        if user_key.startswith("agent:"):
            data = value.payload
            
            # Keep high-confidence data longer
            if data.get("confidence", 0.5) < 0.6 and key.valid_from < cutoff_timestamp:
                to_delete.append(key)
    
    # Note: LMDB doesn't support deletion in current implementation
    # This would be implemented when delete operations are added
    return len(to_delete)  # Return count that would be deleted
```

## Advanced Patterns

### Agent Memory Synchronization

For multi-agent systems, synchronize memory across agents:

```python
def sync_agent_memories(source_db: KV, target_db: KV, sync_patterns: list):
    """Synchronize memory between agents"""
    
    for pattern in sync_patterns:
        prefix = pattern.encode()
        
        for key, value in source_db.items():
            if key.user_key.startswith(prefix):
                # Copy knowledge with attribution
                sync_data = value.payload.copy()
                sync_data["synced_from"] = "agent_primary"
                sync_data["sync_timestamp"] = datetime.now().isoformat()
                
                target_db.put(key, JSONValue(payload=sync_data))
```

### Memory-Driven Decision Making

Use historical memory to improve decision quality:

```python
def make_informed_decision(agent: AIAgentMemory, task_id: str, options: list):
    """Make decisions based on historical memory"""
    
    # Analyze past similar decisions
    past_decisions = []
    for key, value in agent.db.items():
        user_key = key.user_key.decode()
        if user_key.startswith("agent:decision:"):
            decision_data = value.payload
            if any(keyword in decision_data.get("decision", "") 
                  for keyword in task_id.split("_")):
                past_decisions.append(decision_data)
    
    # Calculate success rate for similar decisions
    success_indicators = {}
    for decision in past_decisions:
        decision_type = decision.get("decision", "").split()[0].lower()
        confidence = decision.get("confidence", 0.5)
        
        if decision_type not in success_indicators:
            success_indicators[decision_type] = []
        success_indicators[decision_type].append(confidence)
    
    # Use historical data to inform new decision
    best_option = None
    best_score = 0
    
    for option in options:
        option_type = option["type"]
        base_score = option.get("base_confidence", 0.5)
        
        # Adjust based on historical success
        if option_type in success_indicators:
            historical_success = sum(success_indicators[option_type]) / len(success_indicators[option_type])
            adjusted_score = (base_score + historical_success) / 2
        else:
            adjusted_score = base_score * 0.8  # Penalize unknown patterns
        
        if adjusted_score > best_score:
            best_score = adjusted_score
            best_option = option
    
    # Record the decision
    agent.decisions.record_decision(task_id, {
        "decision": best_option["description"],
        "confidence": best_score,
        "reasoning": [
            f"Based on analysis of {len(past_decisions)} similar past decisions",
            f"Historical success rate for this pattern: {success_indicators.get(best_option['type'], 'unknown')}",
            option.get("reasoning", "No specific reasoning provided")
        ],
        "alternatives": [opt["description"] for opt in options if opt != best_option],
        "decision_method": "memory_informed"
    })
    
    return best_option

# Usage
options = [
    {
        "type": "extract",
        "description": "Extract logic to separate module",
        "base_confidence": 0.7,
        "reasoning": "Improves modularity"
    },
    {
        "type": "refactor", 
        "description": "Refactor existing code in place",
        "base_confidence": 0.6,
        "reasoning": "Lower risk approach"
    }
]

chosen_option = make_informed_decision(agent, "improve_auth_system", options)
```

This comprehensive guide demonstrates how LLMDB's bitemporal capabilities can create sophisticated memory systems for AI coding agents, enabling them to learn, correct mistakes, and make better decisions based on historical experience.