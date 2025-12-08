#!/usr/bin/env node

/**
 * Complete YARNNN Pipeline Examples - P0 → P1 → P2 → P3 → P4
 * 
 * Shows actual data transformations through each stage:
 * P0: Raw dump capture (Sacred Principle #1: Capture is Sacred)
 * P1: Substrate extraction (facts, insights, actions, context)
 * P2: Relationship mapping (causal, temporal, semantic connections)
 * P3: Pattern reflection (insights, gaps, synthesis opportunities)
 * P4: Document composition (deliberate narrative from substrate)
 */

// Real examples showing progression through pipeline stages
const PIPELINE_EXAMPLES = [
  {
    name: "Security Incident Analysis",
    stages: {
      P0_RAW_DUMP: `SECURITY INCIDENT REPORT - SOC-2024-1205
Status: CONTAINED

TIMELINE:
09:15 UTC - Suspicious login detected from IP 185.220.101.42 (Estonia)
09:18 UTC - Failed MFA attempts on admin account 'j.admin@company.com'  
09:23 UTC - Successful credential compromise confirmed via stolen session token
09:27 UTC - Unauthorized database queries detected on customer_data table
09:31 UTC - Data exfiltration attempt blocked by DLP policies
09:45 UTC - Account disabled, session revoked, incident contained

IMPACT ASSESSMENT:
- Affected Systems: Customer database (read access only)
- Data Exposure: 1,247 customer records accessed (names, emails, encrypted)
- Service Disruption: None
- Financial Impact: TBD pending investigation

ROOT CAUSE:
Phishing email containing malicious PDF led to credential harvesting. Admin user clicked link in convincing "IT Security Update" email at 08:45 UTC.

IMMEDIATE ACTIONS:
1. All admin accounts forced password reset + MFA re-enrollment
2. Enhanced monitoring rules deployed
3. Email security filters updated to block similar phishing patterns
4. Customer notification process initiated per breach protocol

LESSONS LEARNED:
- Need mandatory security awareness training refresh
- Consider implementing privileged access management (PAM) solution
- Review admin account provisioning procedures`,

      P1_SUBSTRATE_EXTRACTION: {
        blocks: [
          {
            semantic_type: "summary",
            title: "P1 Data Breach Incident Summary",
            content: "Credential compromise via phishing led to unauthorized database access affecting 1,247 customer records. Incident contained within 30 minutes.",
            confidence_score: 0.94
          },
          {
            semantic_type: "event", 
            title: "Initial Compromise Detection",
            content: "09:15 UTC - Suspicious login detected from IP 185.220.101.42 (Estonia)",
            confidence_score: 0.96
          },
          {
            semantic_type: "event",
            title: "Data Access Breach", 
            content: "09:27 UTC - Unauthorized database queries detected on customer_data table",
            confidence_score: 0.95
          },
          {
            semantic_type: "finding",
            title: "Attack Vector Analysis",
            content: "Phishing email containing malicious PDF led to credential harvesting from admin user",
            confidence_score: 0.92
          },
          {
            semantic_type: "action",
            title: "Mandatory Security Training (High Priority)",
            content: "Implement mandatory security awareness training refresh for all admin users",
            confidence_score: 0.89
          },
          {
            semantic_type: "action", 
            title: "PAM Solution Evaluation (Medium Priority)",
            content: "Consider implementing privileged access management (PAM) solution",
            confidence_score: 0.82
          }
        ],
        context_items: [
          { label: "185.220.101.42", content: "IP Address: Malicious source from Estonia used in attack", kind: "entity" },
          { label: "j.admin@company.com", content: "Account: Compromised administrative account", kind: "entity" },
          { label: "customer_data table", content: "System: Database containing customer PII accessed by attacker", kind: "entity" },
          { label: "Phishing Attack", content: "Attack Vector: Social engineering via convincing IT security email", kind: "classification" },
          { label: "Data Breach", content: "Impact: 1,247 customer records accessed (names, emails, encrypted)", kind: "classification" }
        ]
      },

      P2_RELATIONSHIP_MAPPING: [
        {
          from_type: "block",
          from_id: "event_initial_compromise", 
          to_type: "block",
          to_id: "event_data_access",
          relationship_type: "temporal_sequence",
          strength: 0.95,
          description: "Initial compromise led directly to data access within 12 minutes"
        },
        {
          from_type: "block",
          from_id: "finding_attack_vector",
          to_type: "block", 
          to_id: "event_initial_compromise",
          relationship_type: "causal_relationship",
          strength: 0.93,
          description: "Phishing attack was the root cause that enabled the compromise"
        },
        {
          from_type: "context_item",
          from_id: "phishing_attack",
          to_type: "block",
          to_id: "action_security_training",
          relationship_type: "enablement_chain",
          strength: 0.87,
          description: "Phishing vulnerability directly indicates need for security training"
        },
        {
          from_type: "block",
          from_id: "finding_attack_vector", 
          to_type: "block",
          to_id: "action_pam_solution",
          relationship_type: "impact_relationship",
          strength: 0.84,
          description: "Credential compromise finding suggests need for privileged access controls"
        }
      ],

      P3_PATTERN_REFLECTION: {
        patterns: [
          {
            pattern_type: "temporal",
            description: "Rapid attack progression (30 minutes from initial access to containment)",
            evidence_count: 4,
            confidence: 0.92,
            substrate_references: ["event_initial_compromise", "event_data_access"]
          },
          {
            pattern_type: "structural",
            description: "High connectivity between attack phases and response actions",
            evidence_count: 6,
            confidence: 0.88,
            substrate_references: ["causal_relationship_1", "enablement_chain_1"]
          }
        ],
        insights: [
          {
            insight_type: "synthesis",
            description: "Human vulnerability (phishing) + technical gap (MFA bypass) = rapid compromise",
            supporting_evidence: ["finding_attack_vector", "action_security_training", "action_pam_solution"],
            confidence: 0.86
          },
          {
            insight_type: "opportunity",
            description: "Incident reveals systemic security awareness and access control gaps",
            supporting_evidence: ["action_security_training", "action_pam_solution"],
            confidence: 0.81
          }
        ],
        gaps: [
          {
            gap_type: "missing_context",
            description: "Limited information on why DLP policies were effective but MFA wasn't",
            suggested_actions: ["Analyze DLP policy effectiveness", "Review MFA implementation"],
            priority: "medium"
          }
        ]
      },

      P4_DOCUMENT_COMPOSITION: {
        narrative_structure: {
          introduction: "This security incident analysis reveals a connected chain of human and technical vulnerabilities that led to a contained but significant data breach. The following analysis traces the causal relationships from initial phishing attack through system compromise to organizational response.",
          
          sections: [
            {
              title: "Attack Timeline and Causal Chain",
              content: "The incident began with a sophisticated phishing email at 08:45 UTC that successfully harvested administrative credentials. This led directly to the suspicious login detected at 09:15 UTC from an Estonian IP address. The credential compromise enabled the attacker to bypass initial security controls, leading to failed MFA attempts and ultimately successful session token theft. This progression demonstrates how social engineering attacks can cascade through technical controls when human factors aren't adequately addressed.",
              relationship_focus: "causal_relationship and temporal_sequence connections showing attack progression"
            },
            {
              title: "Impact Assessment and Containment Effectiveness", 
              content: "While the attacker gained access to the customer database, several factors limited the damage. The DLP policies successfully blocked data exfiltration attempts, and the incident was contained within 30 minutes of initial detection. However, 1,247 customer records were accessed during this window. The rapid containment suggests effective monitoring capabilities, but the successful initial compromise indicates gaps in preventive controls.",
              relationship_focus: "impact_relationship connections between attack actions and protective measures"
            },
            {
              title: "Systemic Vulnerabilities and Response Strategy",
              content: "The incident reveals two interconnected vulnerability areas: human factors (susceptibility to phishing) and access control architecture (insufficient MFA protection for high-privilege accounts). The proposed responses - mandatory security training and PAM solution evaluation - directly address these root causes. The training targets the human vulnerability that enabled initial access, while PAM would prevent credential compromise from leading to broad system access.",
              relationship_focus: "enablement_chain relationships between vulnerabilities and proposed solutions"
            }
          ],
          
          summary: "Analysis revealing causal chains between social engineering attack vector and system compromise, with targeted remediation addressing both human and technical factors",
          composition_notes: "Leveraged 4 causal relationships and 2 temporal sequences to show attack progression and response logic",
          synthesis_approach: "Follow causal chains from phishing attack through system access to organizational response"
        },

        substrate_references: [
          { substrate_type: "block", substrate_id: "finding_attack_vector", role: "primary" },
          { substrate_type: "relationship", substrate_id: "causal_phishing_to_compromise", role: "primary" },
          { substrate_type: "block", substrate_id: "action_security_training", role: "supporting" },
          { substrate_type: "context_item", substrate_id: "phishing_attack", role: "supporting" }
        ]
      }
    }
  },

  {
    name: "Product Development Planning",
    stages: {
      P0_RAW_DUMP: `PRODUCT REQUIREMENTS: Mobile Push Notifications v2.0
Product Manager: Lisa Wong
Engineering Lead: David Kim
Target Release: Q1 2025

USER RESEARCH INSIGHTS:
Based on interviews with 89 users and analysis of 12,000 user sessions:
- 73% of users want personalized notification timing
- 68% say current notifications are "too generic"  
- 45% have disabled notifications due to irrelevance
- Top request: "Smart delivery based on my schedule"

CURRENT STATE:
- Notification open rate: 8.2%
- Daily active users: 45,000
- Average sessions per user: 2.1
- User complaints about notifications: 23% of support tickets

SUCCESS METRICS:
- Increase notification open rate to 18%
- Reduce notification-related complaints by 60%
- Maintain or improve DAU retention rate
- Achieve 85% user satisfaction score for notifications

FUNCTIONAL REQUIREMENTS:
FR1: Intelligent timing engine using ML to predict optimal delivery windows
FR2: Content personalization based on user behavior and preferences
FR3: Frequency capping to prevent notification fatigue  
FR4: A/B testing framework for notification copy optimization
FR5: Do-not-disturb integration with device settings

TECHNICAL CONSTRAINTS:
- Must support iOS 14+ and Android 11+
- Backend latency requirement: <200ms for delivery decisions
- Privacy compliance: No PII in recommendation models
- Scalability: Handle 100,000+ users with 5x growth capacity`,

      P1_SUBSTRATE_EXTRACTION: {
        blocks: [
          {
            semantic_type: "summary",
            title: "Mobile Push Notifications v2.0 Requirements",
            content: "Product enhancement to increase notification engagement from 8.2% to 18% through personalization and intelligent timing",
            confidence_score: 0.90
          },
          {
            semantic_type: "metric",
            title: "Current Notification Performance",
            content: "Notification open rate: 8.2%, Daily active users: 45,000, User complaints: 23% of support tickets",
            confidence_score: 0.94
          },
          {
            semantic_type: "finding", 
            title: "User Research Insights",
            content: "73% of users want personalized notification timing, 68% say current notifications are too generic",
            confidence_score: 0.87
          },
          {
            semantic_type: "action",
            title: "Implement ML Timing Engine (High Priority)",
            content: "Build intelligent timing engine using ML to predict optimal delivery windows for each user",
            confidence_score: 0.85
          }
        ],
        context_items: [
          { label: "Lisa Wong", content: "Person: Product Manager leading notifications v2.0 initiative", kind: "entity" },
          { label: "David Kim", content: "Person: Engineering Lead responsible for technical implementation", kind: "entity" },
          { label: "User Personalization", content: "Strategy: ML-driven content and timing personalization approach", kind: "classification" }
        ]
      },

      P2_RELATIONSHIP_MAPPING: [
        {
          from_type: "block",
          from_id: "finding_user_research",
          to_type: "block", 
          to_id: "action_ml_timing",
          relationship_type: "enablement_chain",
          strength: 0.91,
          description: "User research findings directly enable and justify ML timing engine requirement"
        },
        {
          from_type: "block",
          from_id: "metric_current_performance",
          to_type: "block",
          to_id: "summary_enhancement_goals", 
          relationship_type: "causal_relationship",
          strength: 0.88,
          description: "Poor current metrics drive the need for enhancement initiative"
        }
      ],

      P3_PATTERN_REFLECTION: {
        patterns: [
          {
            pattern_type: "thematic", 
            description: "Strong user experience focus with 4 user-centric requirements",
            evidence_count: 4,
            confidence: 0.85
          }
        ],
        insights: [
          {
            insight_type: "synthesis",
            description: "User dissatisfaction (generic notifications) + technical capability (ML) = personalization opportunity",
            supporting_evidence: ["finding_user_research", "action_ml_timing"],
            confidence: 0.83
          }
        ]
      },

      P4_DOCUMENT_COMPOSITION: {
        narrative_structure: {
          sections: [
            {
              title: "User Experience Crisis and Opportunity",
              content: "Current notification performance reveals a significant user experience challenge, with only 8.2% engagement and notifications driving 23% of support complaints. However, user research indicates clear demand for personalization, creating a strategic opportunity to transform notifications from a user pain point into an engagement driver.",
              relationship_focus: "causal_relationship between poor metrics and user dissatisfaction"
            }
          ]
        }
      }
    }
  }
];

async function showCompletePipelineExamples() {
  console.log('🔄 COMPLETE YARNNN PIPELINE EXAMPLES');
  console.log('='.repeat(80));
  
  for (const example of PIPELINE_EXAMPLES) {
    console.log(`\n📊 EXAMPLE: ${example.name}`);
    console.log('='.repeat(60));
    
    // P0: Raw Dump Capture
    console.log('\n🎯 P0: RAW DUMP CAPTURE (Sacred Principle #1: Capture is Sacred)');
    console.log('─'.repeat(50));
    console.log('📝 UNSTRUCTURED INPUT:');
    console.log(example.stages.P0_RAW_DUMP.substring(0, 800) + '...');
    console.log(`\n✅ Status: Immutable raw dump created`);
    console.log(`📏 Length: ${example.stages.P0_RAW_DUMP.length} characters`);
    
    // P1: Substrate Extraction  
    console.log('\n🧠 P1: SUBSTRATE EXTRACTION (Agent Intelligence Mandatory)');
    console.log('─'.repeat(50));
    const substrate = example.stages.P1_SUBSTRATE_EXTRACTION;
    
    console.log('📦 BLOCKS EXTRACTED:');
    substrate.blocks.forEach((block, i) => {
      console.log(`   ${i+1}. [${block.semantic_type}] ${block.title}`);
      console.log(`      Content: ${block.content.substring(0, 80)}...`);
      console.log(`      Confidence: ${block.confidence_score}`);
      console.log('');
    });
    
    console.log('🏷️  CONTEXT ITEMS:');
    substrate.context_items.forEach((ctx, i) => {
      console.log(`   ${i+1}. ${ctx.label} (${ctx.kind})`);
      console.log(`      ${ctx.content}`);
      console.log('');
    });
    
    // P2: Relationship Mapping
    console.log('🕸️  P2: RELATIONSHIP MAPPING (Connects substrate without modification)');
    console.log('─'.repeat(50));
    const relationships = example.stages.P2_RELATIONSHIP_MAPPING;
    
    console.log('🔗 RELATIONSHIPS DISCOVERED:');
    relationships.forEach((rel, i) => {
      console.log(`   ${i+1}. ${rel.relationship_type} (strength: ${rel.strength})`);
      console.log(`      ${rel.from_type} → ${rel.to_type}`);
      console.log(`      ${rel.description}`);
      console.log('');
    });
    
    // P3: Pattern Reflection
    console.log('🔍 P3: PATTERN REFLECTION (Read-only computation)');
    console.log('─'.repeat(50));
    const reflection = example.stages.P3_PATTERN_REFLECTION;
    
    console.log('📈 PATTERNS IDENTIFIED:');
    reflection.patterns.forEach((pattern, i) => {
      console.log(`   ${i+1}. [${pattern.pattern_type}] ${pattern.description}`);
      console.log(`      Evidence: ${pattern.evidence_count} items, Confidence: ${pattern.confidence}`);
      console.log('');
    });
    
    console.log('💡 INSIGHTS DERIVED:');
    reflection.insights.forEach((insight, i) => {
      console.log(`   ${i+1}. [${insight.insight_type}] ${insight.description}`);
      console.log(`      Supporting Evidence: ${insight.supporting_evidence.length} items`);
      console.log('');
    });
    
    if (reflection.gaps && reflection.gaps.length > 0) {
      console.log('🔍 GAPS IDENTIFIED:');
      reflection.gaps.forEach((gap, i) => {
        console.log(`   ${i+1}. [${gap.gap_type}] ${gap.description}`);
        console.log(`      Priority: ${gap.priority}`);
        console.log('');
      });
    }
    
    // P4: Document Composition
    console.log('📄 P4: DOCUMENT COMPOSITION (Deliberate narrative from substrate)');
    console.log('─'.repeat(50));
    const composition = example.stages.P4_DOCUMENT_COMPOSITION;
    
    if (composition.narrative_structure.introduction) {
      console.log('📖 INTRODUCTION:');
      console.log(`   ${composition.narrative_structure.introduction}`);
      console.log('');
    }
    
    console.log('📑 NARRATIVE SECTIONS:');
    composition.narrative_structure.sections.forEach((section, i) => {
      console.log(`   ${i+1}. ${section.title}`);
      console.log(`      ${section.content.substring(0, 200)}...`);
      console.log(`      Relationship Focus: ${section.relationship_focus}`);
      console.log('');
    });
    
    console.log('🎯 SYNTHESIS APPROACH:');
    console.log(`   ${composition.narrative_structure.synthesis_approach}`);
    console.log('');
    
    console.log('📚 SUBSTRATE REFERENCES IN DOCUMENT:');
    composition.substrate_references.forEach((ref, i) => {
      console.log(`   ${i+1}. ${ref.substrate_type}:${ref.substrate_id} (${ref.role})`);
    });
    
    console.log('\n' + '='.repeat(80));
  }
  
  // Pipeline Summary
  console.log('\n📊 PIPELINE QUALITY SUMMARY');
  console.log('='.repeat(60));
  console.log('✅ P0: Immutable capture preserves original unstructured data');
  console.log('✅ P1: Domain-aware extraction with confidence scoring');
  console.log('✅ P2: Intelligent relationship discovery (causal, temporal, semantic)');
  console.log('✅ P3: Pattern recognition and insight synthesis');
  console.log('✅ P4: Connected narrative composition using substrate relationships');
  console.log('');
  console.log('🎯 CANON COMPLIANCE:');
  console.log('   - Sacred Principle #1: Capture is Sacred (P0)');
  console.log('   - Sacred Principle #3: Narrative is Deliberate (P4)');
  console.log('   - Sacred Principle #4: Agent Intelligence is Mandatory (P1-P3)');
  console.log('   - No substrate modification across pipeline stages');
  console.log('   - Clear provenance from raw dumps to final documents');
}

// Run the complete pipeline examples
if (require.main === module) {
  showCompletePipelineExamples().catch(console.error);
}

module.exports = { showCompletePipelineExamples };