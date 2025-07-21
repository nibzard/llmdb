#!/usr/bin/env python3
"""
AI Coding Agent Memory Store Demonstration

This example demonstrates how AI coding agents can use LLMDB as a sophisticated
memory store with bitemporal capabilities. It showcases:

- Code analysis evolution and corrections
- Decision tracking with reasoning
- Conversation context management
- Knowledge learning and updates
- Temporal queries for debugging and rollback
- Agent state reconstruction

The demo simulates an AI agent working on a software project, making decisions,
learning from experience, and correcting its understanding over time.
"""

import os
import tempfile
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from llmdb import KV
from llmdb.temporal_key import Key
from llmdb.kv._codec import JSONValue


def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_timestamp_microseconds(dt: datetime) -> int:
    """Convert datetime to microseconds since epoch"""
    return int(dt.timestamp() * 1_000_000)


class AIAgentMemoryDemo:
    """Demonstrates AI agent memory patterns using LLMDB"""
    
    def __init__(self, db_path: str):
        self.db = KV(db_path)
        self.agent_id = "coding_assistant_v1"
        
    def analyze_code_file(self, file_path: str, analysis_data: dict, timestamp: datetime):
        """Store code analysis results with temporal tracking"""
        file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
        key = Key(
            partition=0,
            user_key=f"agent:analysis:{file_hash}",
            valid_from=get_timestamp_microseconds(timestamp)
        )
        
        analysis_record = {
            "agent_id": self.agent_id,
            "file_path": file_path,
            "timestamp": timestamp.isoformat(),
            "analysis": analysis_data,
            "confidence": analysis_data.get("confidence", 0.5),
            "source": "static_analysis"
        }
        
        self.db.put(key, JSONValue(payload=analysis_record))
        
    def make_decision(self, task_id: str, decision_data: dict, timestamp: datetime):
        """Record agent decision with reasoning"""
        key = Key(
            partition=0,
            user_key=f"agent:decision:{task_id}",
            valid_from=get_timestamp_microseconds(timestamp)
        )
        
        decision_record = {
            "agent_id": self.agent_id,
            "task_id": task_id,
            "timestamp": timestamp.isoformat(),
            "decision": decision_data["decision"],
            "reasoning": decision_data.get("reasoning", []),
            "alternatives": decision_data.get("alternatives", []),
            "confidence": decision_data.get("confidence", 0.5),
            "context": decision_data.get("context", {}),
            "estimated_impact": decision_data.get("impact", "medium")
        }
        
        self.db.put(key, JSONValue(payload=decision_record))
        
    def update_conversation_context(self, session_id: str, context_data: dict, timestamp: datetime):
        """Update conversation context"""
        key = Key(
            partition=0,
            user_key=f"agent:context:{session_id}",
            valid_from=get_timestamp_microseconds(timestamp)
        )
        
        context_record = {
            "agent_id": self.agent_id,
            "session_id": session_id,
            "timestamp": timestamp.isoformat(),
            "context": context_data
        }
        
        self.db.put(key, JSONValue(payload=context_record))
        
    def store_knowledge(self, domain: str, knowledge_data: dict, timestamp: datetime):
        """Store learned knowledge"""
        key = Key(
            partition=0,
            user_key=f"agent:knowledge:{domain}",
            valid_from=get_timestamp_microseconds(timestamp)
        )
        
        knowledge_record = {
            "agent_id": self.agent_id,
            "domain": domain,
            "timestamp": timestamp.isoformat(),
            "knowledge": knowledge_data,
            "confidence": knowledge_data.get("confidence", 0.5),
            "source": knowledge_data.get("source", "learning")
        }
        
        self.db.put(key, JSONValue(payload=knowledge_record))
        
    def get_analysis_history(self, file_path: str) -> List[Dict]:
        """Get evolution of analysis for a file"""
        file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
        versions = []
        prefix = f"agent:analysis:{file_hash}".encode()
        
        for key, value in self.db.items():
            if key.user_key.startswith(prefix):
                valid_time = datetime.fromtimestamp(key.valid_from / 1_000_000)
                versions.append({
                    "valid_time": valid_time,
                    "tx_id": key.tx_id,
                    "data": value.payload
                })
                
        return sorted(versions, key=lambda x: x["valid_time"])
        
    def get_decision_history(self, task_id: str) -> List[Dict]:
        """Get decision evolution for a task"""
        versions = []
        prefix = f"agent:decision:{task_id}".encode()
        
        for key, value in self.db.items():
            if key.user_key.startswith(prefix):
                valid_time = datetime.fromtimestamp(key.valid_from / 1_000_000)
                versions.append({
                    "valid_time": valid_time,
                    "tx_id": key.tx_id,
                    "data": value.payload
                })
                
        return sorted(versions, key=lambda x: x["valid_time"])
        
    def get_knowledge_evolution(self, domain: str) -> List[Dict]:
        """Track knowledge evolution in a domain"""
        versions = []
        prefix = f"agent:knowledge:{domain}".encode()
        
        for key, value in self.db.items():
            if key.user_key.startswith(prefix):
                valid_time = datetime.fromtimestamp(key.valid_from / 1_000_000)
                versions.append({
                    "valid_time": valid_time,
                    "tx_id": key.tx_id,
                    "data": value.payload
                })
                
        return sorted(versions, key=lambda x: x["valid_time"])
        
    def get_agent_state_summary(self) -> Dict:
        """Get summary of current agent state"""
        state = {
            "analyses": 0,
            "decisions": 0, 
            "contexts": 0,
            "knowledge_domains": 0,
            "total_records": 0
        }
        
        for key, value in self.db.items():
            state["total_records"] += 1
            user_key = key.user_key.decode()
            
            if user_key.startswith("agent:analysis:"):
                state["analyses"] += 1
            elif user_key.startswith("agent:decision:"):
                state["decisions"] += 1
            elif user_key.startswith("agent:context:"):
                state["contexts"] += 1
            elif user_key.startswith("agent:knowledge:"):
                state["knowledge_domains"] += 1
                
        return state


def run_agent_simulation():
    """Run a comprehensive AI agent memory simulation"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "agent_memory.db")
        agent = AIAgentMemoryDemo(db_path)
        
        print("🤖 AI Coding Agent Memory Store Demonstration")
        print("=" * 60)
        print("\nSimulating an AI agent working on a software project...")
        print("The agent will analyze code, make decisions, learn, and correct itself.\n")
        
        # === Phase 1: Initial Project Analysis ===
        print("📊 Phase 1: Initial Project Analysis")
        print("-" * 40)
        
        base_time = datetime.now() - timedelta(days=7)  # Simulate a week ago
        
        # Analyze authentication module
        print(f"🔍 {format_datetime(base_time)}: Analyzing auth module...")
        agent.analyze_code_file("src/auth/login.py", {
            "lines_of_code": 156,
            "complexity_score": 8.5,
            "dependencies": ["bcrypt", "jwt", "flask"],
            "patterns": ["factory", "decorator"],
            "security_issues": ["hardcoded_secret", "no_rate_limiting"],
            "test_coverage": 0.65,
            "confidence": 0.72,
            "recommendations": [
                "Extract secret to environment variable",
                "Add rate limiting middleware",
                "Improve test coverage"
            ]
        }, base_time)
        
        # Update conversation context
        agent.update_conversation_context("session_001", {
            "current_task": "security_audit",
            "focus_area": "authentication",
            "user_priority": "high",
            "files_reviewed": ["src/auth/login.py"],
            "issues_found": 2
        }, base_time)
        
        # Make decision about security fixes
        print(f"🎯 {format_datetime(base_time + timedelta(minutes=30))}: Making security decision...")
        agent.make_decision("fix_auth_security", {
            "decision": "Implement comprehensive auth security fixes",
            "reasoning": [
                "Found hardcoded secrets which is critical security risk",
                "Missing rate limiting allows brute force attacks",
                "Low test coverage increases risk of regressions"
            ],
            "alternatives": [
                "Quick fix only the hardcoded secret",
                "Postpone fixes until next sprint"
            ],
            "confidence": 0.85,
            "context": {
                "severity": "critical",
                "estimated_hours": 8,
                "dependencies": ["environment_setup", "testing_framework"]
            },
            "impact": "high"
        }, base_time + timedelta(minutes=30))
        
        # === Phase 2: Learning and Knowledge Updates ===
        print("\n🧠 Phase 2: Knowledge Learning and Updates")
        print("-" * 40)
        
        learning_time = base_time + timedelta(days=1)
        print(f"📚 {format_datetime(learning_time)}: Learning about Flask security...")
        
        # Store initial security knowledge
        agent.store_knowledge("flask_security", {
            "best_practices": [
                "Use environment variables for secrets",
                "Implement CSRF protection",
                "Add rate limiting",
                "Use secure session cookies"
            ],
            "common_vulnerabilities": [
                "SQL injection",
                "XSS attacks", 
                "CSRF attacks",
                "Session fixation"
            ],
            "recommended_libraries": [
                "flask-limiter",
                "flask-wtf",
                "flask-talisman"
            ],
            "confidence": 0.78,
            "source": "documentation_study"
        }, learning_time)
        
        # === Phase 3: Deeper Analysis and Corrections ===
        print("\n🔄 Phase 3: Deeper Analysis and Corrections")
        print("-" * 40)
        
        correction_time = base_time + timedelta(days=2)
        print(f"🔍 {format_datetime(correction_time)}: Re-analyzing with deeper inspection...")
        
        # Corrected analysis after more thorough review
        agent.analyze_code_file("src/auth/login.py", {
            "lines_of_code": 156,
            "complexity_score": 7.2,  # Revised down after understanding structure
            "dependencies": ["bcrypt", "jwt", "flask", "redis"],  # Found hidden Redis dependency
            "patterns": ["factory", "decorator", "observer"],  # Found observer pattern for logging
            "security_issues": [
                "hardcoded_secret",
                "no_rate_limiting", 
                "insufficient_password_validation"  # New issue found
            ],
            "test_coverage": 0.65,
            "confidence": 0.88,  # Higher confidence after thorough review
            "recommendations": [
                "Extract secret to environment variable",
                "Add rate limiting middleware",
                "Strengthen password validation rules",
                "Add security event logging"
            ],
            "correction_reason": "Found additional security issue and Redis dependency on deeper inspection"
        }, correction_time)
        
        # Update knowledge with new findings
        print(f"📝 {format_datetime(correction_time + timedelta(minutes=15))}: Updating security knowledge...")
        agent.store_knowledge("flask_security", {
            "best_practices": [
                "Use environment variables for secrets",
                "Implement CSRF protection", 
                "Add rate limiting",
                "Use secure session cookies",
                "Implement strong password policies",  # New learning
                "Add security event logging"  # New learning
            ],
            "common_vulnerabilities": [
                "SQL injection",
                "XSS attacks",
                "CSRF attacks", 
                "Session fixation",
                "Weak password policies",  # New learning
                "Insufficient logging"  # New learning
            ],
            "recommended_libraries": [
                "flask-limiter",
                "flask-wtf",
                "flask-talisman",
                "python-decouple",  # For env management
                "structlog"  # For security logging
            ],
            "confidence": 0.91,  # Increased confidence
            "source": "hands_on_analysis",
            "correction_reason": "Found additional security considerations during code analysis"
        }, correction_time + timedelta(minutes=15))
        
        # === Phase 4: Decision Revision ===
        print("\n⚡ Phase 4: Decision Revision")
        print("-" * 40)
        
        revision_time = base_time + timedelta(days=3)
        print(f"🎯 {format_datetime(revision_time)}: Revising security fix decision...")
        
        # Revise decision based on new knowledge
        agent.make_decision("fix_auth_security", {
            "decision": "Implement comprehensive auth security fixes with phased approach",
            "reasoning": [
                "Found additional security issue requiring password policy update",
                "Need to add security logging for compliance",
                "Phased approach reduces deployment risk",
                "Redis dependency requires coordinated deployment"
            ],
            "alternatives": [
                "Original comprehensive fix all at once",
                "Minimal fixes only for immediate security"
            ],
            "confidence": 0.93,  # Higher confidence with better understanding
            "context": {
                "severity": "critical",
                "estimated_hours": 12,  # Increased estimate
                "dependencies": [
                    "environment_setup", 
                    "testing_framework",
                    "redis_configuration",  # New dependency
                    "logging_infrastructure"  # New dependency
                ],
                "deployment_phases": [
                    "secrets_and_validation",
                    "rate_limiting_and_logging", 
                    "testing_and_monitoring"
                ]
            },
            "impact": "high",
            "revision_reason": "Discovered additional security requirements and deployment dependencies"
        }, revision_time)
        
        # === Phase 5: Memory Analysis and Reporting ===
        print("\n📈 Phase 5: Memory Analysis and Reporting")
        print("-" * 40)
        
        # Show agent state summary
        state = agent.get_agent_state_summary()
        print(f"\n📊 Agent Memory Summary:")
        print(f"   • Total Records: {state['total_records']}")
        print(f"   • Code Analyses: {state['analyses']}")
        print(f"   • Decisions Made: {state['decisions']}")
        print(f"   • Contexts Tracked: {state['contexts']}")
        print(f"   • Knowledge Domains: {state['knowledge_domains']}")
        
        # Show analysis evolution
        print(f"\n🔄 Code Analysis Evolution for 'src/auth/login.py':")
        analysis_history = agent.get_analysis_history("src/auth/login.py")
        for i, version in enumerate(analysis_history):
            data = version["data"]
            analysis = data["analysis"]
            print(f"   Version {i+1} ({format_datetime(version['valid_time'])}):")
            print(f"      Complexity: {analysis['complexity_score']}")
            print(f"      Issues: {len(analysis['security_issues'])}")
            print(f"      Confidence: {analysis['confidence']:.2f}")
            if "correction_reason" in analysis:
                print(f"      Correction: {analysis['correction_reason']}")
        
        # Show decision evolution  
        print(f"\n🎯 Decision Evolution for 'fix_auth_security':")
        decision_history = agent.get_decision_history("fix_auth_security")
        for i, version in enumerate(decision_history):
            data = version["data"]
            print(f"   Version {i+1} ({format_datetime(version['valid_time'])}):")
            print(f"      Decision: {data['decision'][:50]}...")
            print(f"      Confidence: {data['confidence']:.2f}")
            print(f"      Estimated Hours: {data['context'].get('estimated_hours', 'Unknown')}")
            if "revision_reason" in data:
                print(f"      Revision: {data['revision_reason']}")
        
        # Show knowledge evolution
        print(f"\n🧠 Knowledge Evolution for 'flask_security':")
        knowledge_history = agent.get_knowledge_evolution("flask_security")
        for i, version in enumerate(knowledge_history):
            data = version["data"]
            knowledge = data["knowledge"]
            print(f"   Version {i+1} ({format_datetime(version['valid_time'])}):")
            print(f"      Best Practices: {len(knowledge['best_practices'])}")
            print(f"      Vulnerabilities: {len(knowledge['common_vulnerabilities'])}")
            print(f"      Libraries: {len(knowledge['recommended_libraries'])}")
            print(f"      Confidence: {knowledge['confidence']:.2f}")
            if "correction_reason" in knowledge:
                print(f"      Update: {knowledge['correction_reason']}")
        
        # === Phase 6: Temporal Query Demonstrations ===
        print(f"\n⏰ Phase 6: Temporal Query Demonstrations")
        print("-" * 40)
        
        # Demonstrate "what did the agent know when" queries
        query_time = base_time + timedelta(days=1, hours=12)  # Mid-way through learning
        print(f"\n🕐 What did the agent know about Flask security on {format_datetime(query_time)}?")
        
        # Simulate temporal query by finding latest version before query time
        query_timestamp = get_timestamp_microseconds(query_time)
        latest_knowledge = None
        
        for key, value in agent.db.items():
            user_key = key.user_key.decode()
            if user_key == "agent:knowledge:flask_security":
                if key.valid_from <= query_timestamp:
                    if latest_knowledge is None or key.valid_from > latest_knowledge["timestamp"]:
                        latest_knowledge = {
                            "timestamp": key.valid_from,
                            "data": value.payload
                        }
        
        if latest_knowledge:
            knowledge = latest_knowledge["data"]["knowledge"]
            print(f"   At that time, the agent knew about {len(knowledge['best_practices'])} best practices:")
            for practice in knowledge["best_practices"][:3]:
                print(f"      • {practice}")
            print(f"   Agent confidence was: {knowledge['confidence']:.2f}")
        
        # Show what changed after that time
        print(f"\n🔄 What changed in the agent's knowledge after {format_datetime(query_time)}?")
        later_versions = []
        for version in knowledge_history:
            if version["valid_time"] > query_time:
                later_versions.append(version)
        
        for version in later_versions:
            data = version["data"]
            knowledge = data["knowledge"]
            print(f"   Update at {format_datetime(version['valid_time'])}:")
            print(f"      New best practices: {len(knowledge['best_practices']) - len(latest_knowledge['data']['knowledge']['best_practices']) if latest_knowledge else 0}")
            print(f"      Confidence change: +{knowledge['confidence'] - (latest_knowledge['data']['knowledge']['confidence'] if latest_knowledge else 0):.2f}")
            if "correction_reason" in knowledge:
                print(f"      Reason: {knowledge['correction_reason']}")
        
        print(f"\n✨ Key Insights from LLMDB Bitemporal Memory:")
        print("   • Complete audit trail of agent learning and decision-making")
        print("   • Can reconstruct agent state at any point in time")
        print("   • Corrections don't lose original information")
        print("   • Evolution of confidence and understanding is tracked")
        print("   • Enables debugging: 'Why did the agent decide X at time Y?'")
        print("   • Support for rollback and decision replay scenarios")
        
        print(f"\n🎯 This demonstrates LLMDB's power for AI agent memory:")
        print("   Traditional databases would lose the evolution history.")
        print("   LLMDB preserves every step of the agent's learning journey!")


if __name__ == "__main__":
    run_agent_simulation()