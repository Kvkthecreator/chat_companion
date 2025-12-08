#!/usr/bin/env python3
"""
Staging Proof Script for P1 Substrate Agent v2
Creates seeded dumps and processes them with structured ingredient extraction.
"""

import os
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any

# Import the agent and fixtures
import sys
sys.path.append('/Users/macbook/rightnow-agent-app-fullstack/api/src')

from app.agents.pipeline.substrate_agent_v2 import P1SubstrateAgentV2
from tests.fixtures.utf8_multilingual_test_data_fixed import UTF8_TEST_FIXTURES

# Staging test data - 5 different content types
STAGING_TEST_DUMPS = [
    {
        "type": "interview", 
        "content": """Client Interview Notes - Q4 Planning Session
        
Goal: Launch new feature by December 2024 with focus on user retention
Budget constraint: Limited to $75K for development and marketing
Success metrics: 25% increase in DAU, 15% reduction in churn rate
Key stakeholders: Product Manager Sarah Chen, CTO Alex Rodriguez
Technical requirements: Integration with existing API, mobile-first design
User research findings: 80% of users want push notifications, 65% prefer dark mode
Risk factors: Tight timeline, dependency on third-party service
Decision made: Proceed with MVP approach, defer advanced analytics""",
        "dump_id": "staging-interview-001"
    },
    {
        "type": "client_brief",
        "content": """Project Brief: E-commerce Platform Modernization
        
Objective: Migrate legacy PHP system to modern React/Node.js architecture
Constraints: Zero downtime requirement, $200K budget limit, 6-month timeline
Success criteria: 50% faster page load, 99.9% uptime, mobile responsive
Key deliverables: User authentication, product catalog, payment processing
Technical stack: React 18, Node.js 20, PostgreSQL, Redis cache
Performance targets: <2s page load, <100ms API response times
Security requirements: PCI DSS compliance, OAuth2 authentication
Quality metrics: 90% test coverage, accessibility WCAG AA compliance""",
        "dump_id": "staging-brief-002"
    },
    {
        "type": "specification",
        "content": """API Specification: Real-time Notification Service
        
System goal: Deliver push notifications with 99.5% success rate
Infrastructure constraints: AWS only, max 10K concurrent connections
Performance metrics: <50ms latency, 1M+ messages/hour capacity
Entity definitions: User, Device, Notification, Campaign, Analytics
Data flow: Campaign → Targeting → Queue → Delivery → Tracking
Integration points: Mobile SDKs (iOS/Android), Web Push API, Email service
Failure handling: Retry logic with exponential backoff, dead letter queue
Monitoring requirements: Real-time dashboards, alerting on 95th percentile""",
        "dump_id": "staging-spec-003"  
    },
    {
        "type": "chat_log",
        "content": """Team Chat - Sprint Planning Discussion

Sarah: Our main goal this sprint is to improve user onboarding flow
Alex: Constraint - we only have 2 weeks before the demo
Mike: Success metric should be 40% completion rate improvement  
Sarah: Technical entity needed - A/B testing framework
Lisa: Budget constraint - can't exceed $15K for third-party tools
Alex: Performance goal - page load under 1.5 seconds
Mike: User research shows 70% drop-off at step 3
Sarah: Decision - focus on steps 1-3 first, optimize later
Lisa: Quality metric - 95% user satisfaction score target""",
        "dump_id": "staging-chat-004"
    },
    {
        "type": "article",
        "content": """Best Practices: Microservices Monitoring Strategy
        
Strategic objective: Achieve comprehensive observability across distributed systems
Resource constraints: Limited DevOps team (3 people), $50K annual tool budget  
Key performance indicators: MTTR under 15 minutes, 99.95% service availability
Essential components: Metrics collection, log aggregation, distributed tracing
Implementation approach: Start with critical services, expand gradually
Technology stack: Prometheus, Grafana, Jaeger, ELK stack, PagerDuty
Operational metrics: Request throughput, error rates, latency percentiles
Business impact measurement: Revenue loss per minute of downtime
Alerting strategy: Severity-based escalation, context-aware notifications""",
        "dump_id": "staging-article-005"
    }
]

async def create_staging_proof():
    """Create staging proof with real P1 agent extraction."""
    print("🚀 Starting Staging Proof for P1 Substrate Agent v2")
    print("=" * 60)
    
    # Initialize agent
    try:
        agent = P1SubstrateAgentV2()
        print(f"✅ Agent initialized: {agent.agent_name}")
    except RuntimeError as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("💡 Make sure OPENAI_API_KEY is set in environment")
        return
    
    # Process each test dump
    results = []
    
    for dump in STAGING_TEST_DUMPS:
        print(f"\n📄 Processing {dump['type']} content...")
        print(f"Content length: {len(dump['content'])} characters")
        
        try:
            # Extract with LLM  
            extraction_result = await agent._extract_with_llm(
                dump['content'], 
                dump['dump_id']
            )
            
            # Analyze results
            blocks = extraction_result.get('blocks', [])
            metadata = extraction_result.get('extraction_metadata', {})
            
            # Calculate statistics
            total_entities = sum(len(block.get('entities', [])) for block in blocks)
            total_goals = sum(len(block.get('goals', [])) for block in blocks) 
            total_constraints = sum(len(block.get('constraints', [])) for block in blocks)
            total_metrics = sum(len(block.get('metrics', [])) for block in blocks)
            
            # Validate provenance coverage
            provenance_coverage = 0
            total_items = total_entities + total_goals + total_constraints + total_metrics
            validated_items = 0
            
            for block in blocks:
                if block.get('provenance', {}).get('ranges'):
                    validated_items += 1
                    
                for entity in block.get('entities', []):
                    if entity.get('provenance', {}).get('ranges'):
                        validated_items += 1
                        
                for goal in block.get('goals', []):
                    if goal.get('provenance', {}).get('ranges'):
                        validated_items += 1
                        
                for constraint in block.get('constraints', []):
                    if constraint.get('provenance', {}).get('ranges'):
                        validated_items += 1
                        
                for metric in block.get('metrics', []):
                    if metric.get('provenance', {}).get('ranges'):
                        validated_items += 1
            
            if total_items > 0:
                provenance_coverage = (validated_items / total_items) * 100
            
            result = {
                "dump_type": dump['type'],
                "dump_id": dump['dump_id'],
                "content_length": len(dump['content']),
                "blocks_extracted": len(blocks),
                "semantic_types": list(set(block.get('semantic_type', 'unknown') for block in blocks)),
                "total_entities": total_entities,
                "total_goals": total_goals,
                "total_constraints": total_constraints, 
                "total_metrics": total_metrics,
                "average_confidence": sum(block.get('confidence', 0) for block in blocks) / len(blocks) if blocks else 0,
                "provenance_coverage_percent": round(provenance_coverage, 1),
                "extraction_successful": True,
                "sample_extractions": blocks[:2] if blocks else []  # First 2 blocks as examples
            }
            
            results.append(result)
            
            print(f"  ✅ Extracted {len(blocks)} blocks")
            print(f"  📊 Confidence: {result['average_confidence']:.2f}")
            print(f"  🔍 Provenance: {result['provenance_coverage_percent']}%")
            print(f"  🏷️ Types: {', '.join(result['semantic_types'])}")
            
        except Exception as e:
            print(f"  ❌ Extraction failed: {e}")
            results.append({
                "dump_type": dump['type'],
                "dump_id": dump['dump_id'], 
                "extraction_successful": False,
                "error": str(e)
            })
    
    # Test UTF-8 multilingual fixtures
    print(f"\n🌍 Testing UTF-8 multilingual fixtures...")
    
    for fixture in UTF8_TEST_FIXTURES:
        print(f"  Testing {fixture['name']}...")
        
        try:
            extraction_result = await agent._extract_with_llm(
                fixture['content'],
                f"utf8-{fixture['name']}"
            )
            
            blocks = extraction_result.get('blocks', [])
            print(f"    ✅ {len(blocks)} blocks extracted from {fixture['description']}")
            
        except Exception as e:
            print(f"    ❌ UTF-8 extraction failed: {e}")
    
    # Generate staging report
    print(f"\n📋 Generating Staging Report...")
    report = generate_staging_report(results)
    
    # Save report
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_file = f"/Users/macbook/rightnow-agent-app-fullstack/staging_proof_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Report saved to: {report_file}")
    print("\n" + "=" * 60)
    print("🎯 Staging Proof Summary:")
    print(f"   Successful extractions: {report['summary']['successful_extractions']}/{report['summary']['total_dumps']}")
    print(f"   Average confidence: {report['summary']['average_confidence']:.2f}")  
    print(f"   Average provenance coverage: {report['summary']['average_provenance_coverage']:.1f}%")
    print(f"   Semantic types found: {', '.join(report['summary']['all_semantic_types'])}")
    
    return report

def generate_staging_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate comprehensive staging report."""
    successful_results = [r for r in results if r.get('extraction_successful', False)]
    
    # Calculate summary statistics
    total_blocks = sum(r.get('blocks_extracted', 0) for r in successful_results)
    total_entities = sum(r.get('total_entities', 0) for r in successful_results)
    total_goals = sum(r.get('total_goals', 0) for r in successful_results)
    total_constraints = sum(r.get('total_constraints', 0) for r in successful_results)
    total_metrics = sum(r.get('total_metrics', 0) for r in successful_results)
    
    avg_confidence = sum(r.get('average_confidence', 0) for r in successful_results) / len(successful_results) if successful_results else 0
    avg_provenance = sum(r.get('provenance_coverage_percent', 0) for r in successful_results) / len(successful_results) if successful_results else 0
    
    all_semantic_types = set()
    for r in successful_results:
        all_semantic_types.update(r.get('semantic_types', []))
    
    # Create redacted examples (first 3 successful extractions)
    redacted_examples = []
    for result in successful_results[:3]:
        if result.get('sample_extractions'):
            example = {
                "dump_type": result['dump_type'],
                "semantic_type": result['sample_extractions'][0].get('semantic_type', 'unknown'),
                "title": result['sample_extractions'][0].get('title', 'Untitled'),
                "confidence": result['sample_extractions'][0].get('confidence', 0),
                "entity_count": len(result['sample_extractions'][0].get('entities', [])),
                "goal_count": len(result['sample_extractions'][0].get('goals', [])),
                "provenance_ranges": len(result['sample_extractions'][0].get('provenance', {}).get('ranges', []))
            }
            redacted_examples.append(example)
    
    report = {
        "report_type": "P1_Substrate_Agent_v2_Staging_Proof",
        "generated_at": datetime.utcnow().isoformat(),
        "agent_version": "2.0_concrete_llm",
        "summary": {
            "total_dumps": len(results),
            "successful_extractions": len(successful_results),
            "total_blocks_extracted": total_blocks,
            "total_entities": total_entities,
            "total_goals": total_goals,
            "total_constraints": total_constraints,  
            "total_metrics": total_metrics,
            "average_confidence": round(avg_confidence, 3),
            "average_provenance_coverage": round(avg_provenance, 1),
            "all_semantic_types": list(all_semantic_types)
        },
        "counts_by_semantic_type": {},  # Would calculate from semantic_types
        "redacted_examples": redacted_examples,
        "detailed_results": results,
        "validation_status": {
            "provenance_coverage_100_percent": all(
                r.get('provenance_coverage_percent', 0) == 100.0 
                for r in successful_results
            ),
            "confidence_above_threshold": all(
                r.get('average_confidence', 0) >= 0.7
                for r in successful_results  
            ),
            "no_extraction_failures": len(successful_results) == len(results)
        }
    }
    
    return report

if __name__ == "__main__":
    # Set up environment
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set. Please set it in your environment.")
        print("💡 export OPENAI_API_KEY='your-key-here'")
        exit(1)
    
    # Run staging proof
    asyncio.run(create_staging_proof())