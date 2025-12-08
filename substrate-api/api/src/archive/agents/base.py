"""
DEPRECATED: Base agent classes for legacy agents.

All new agents should use the canonical pipeline agents in agents/pipeline/.
This file is kept for backward compatibility only.

Canonical Pipeline Agents (agents/pipeline/) - Canon v3.1:
- P0CaptureAgent: Only writes raw_dumps, never interprets
- P1SubstrateAgent: Creates blocks with semantic duplicate detection
- P3ReflectionAgent: Pattern analysis and insight generation
- P4PresentationAgent: Document composition from substrate + insights

Note: P2 (Graph/Relationships) removed in v3.1 - replaced by Neural Map
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

logger = logging.getLogger("uvicorn.error")


class BaseInfraAgent(ABC):
    """Base class for infrastructure agents providing common functionality."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logger
        
    @abstractmethod
    async def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        """Perform analysis specific to this agent."""
        pass
        
    async def log_analysis(self, analysis_result: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Log analysis results for audit trail."""
        try:
            log_data = {
                "agent": self.agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                "result": analysis_result,
                "metadata": metadata or {}
            }
            self.logger.info(f"Agent analysis completed: {self.agent_name}", extra=log_data)
        except Exception as e:
            self.logger.warning(f"Failed to log analysis for {self.agent_name}: {e}")
            
    def get_agent_info(self) -> Dict[str, str]:
        """Get basic agent information."""
        return {
            "name": self.agent_name,
            "type": "infrastructure",
            "status": "active"
        }


class BaseNarrativeAgent(ABC):
    """Base class for narrative agents providing user-facing functionality."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logger
        
    @abstractmethod
    async def generate_narrative(self, *args, **kwargs) -> Dict[str, Any]:
        """Generate narrative content specific to this agent."""
        pass
        
    async def log_narrative_generation(self, narrative_result: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Log narrative generation for audit trail."""
        try:
            log_data = {
                "agent": self.agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                "result": narrative_result,
                "metadata": metadata or {}
            }
            self.logger.info(f"Narrative generation completed: {self.agent_name}", extra=log_data)
        except Exception as e:
            self.logger.warning(f"Failed to log narrative generation for {self.agent_name}: {e}")
            
    def get_agent_info(self) -> Dict[str, str]:
        """Get basic agent information."""
        return {
            "name": self.agent_name,
            "type": "narrative",
            "status": "active"
        }