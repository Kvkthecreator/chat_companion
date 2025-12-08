#!/usr/bin/env node

/**
 * Show Actual Raw Dump → Substrate Examples
 * 
 * Creates real dumps and shows what substrate proposals would be generated
 */

// Real test content examples
const ACTUAL_TEST_DUMPS = [
  {
    name: "Financial Earnings Call",
    raw_content: `Q3 2024 Earnings Call Transcript - TechCorp Inc.

CEO Sarah Martinez: "We delivered strong results this quarter with revenue of $127 million, representing 18% year-over-year growth. Our SaaS recurring revenue now represents 85% of total revenue, up from 78% last quarter."

CFO Mike Chen: "Gross margins improved to 71%, driven by operational efficiency gains and improved pricing on enterprise contracts. Operating expenses were $89 million, slightly above guidance due to increased R&D investment."

Analyst Question: "Can you comment on customer acquisition trends?"

CEO: "We added 847 new enterprise customers this quarter. Customer acquisition cost decreased 12% while average contract value increased 23%. Our net retention rate remains above 110%."

Key Metrics Summary:
- Revenue: $127M (+18% YoY)
- Gross Margin: 71% (vs 68% Q2)
- New Enterprise Customers: 847
- CAC: Down 12%
- ACV: Up 23%
- Net Retention: 110%+

Forward Guidance: Q4 revenue expected between $135-140M.`
  },
  
  {
    name: "Security Incident Report", 
    raw_content: `INCIDENT REPORT: SOC-2024-1205
Classification: P1 - Data Breach
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
- Review admin account provisioning procedures`
  },

  {
    name: "Product Requirements Doc",
    raw_content: `PRODUCT REQUIREMENTS: Mobile Push Notifications v2.0
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
- Scalability: Handle 100,000+ users with 5x growth capacity

ACCEPTANCE CRITERIA:
✓ User can set notification preferences (timing, frequency, categories)
✓ System learns from user interaction patterns over 30-day period
✓ Notifications respect device do-not-disturb settings
✓ A/B tests can be configured without code deployment
✓ Analytics dashboard shows engagement metrics in real-time`
  }
];

async function showActualSubstrateExamples() {
  console.log('📋 ACTUAL RAW DUMP → SUBSTRATE EXAMPLES');
  console.log('='.repeat(70));
  
  for (const dump of ACTUAL_TEST_DUMPS) {
    console.log(`\n📄 RAW DUMP: ${dump.name}`);
    console.log('─'.repeat(50));
    console.log('📝 UNSTRUCTURED CONTENT:');
    console.log(dump.raw_content);
    console.log('');
    
    // Simulate substrate proposal based on improved P1 agent logic
    const substrate = analyzeAndPropose(dump.raw_content, dump.name);
    
    console.log('🎯 PROPOSED SUBSTRATE:');
    console.log('─'.repeat(30));
    
    console.log('📊 BLOCKS:');
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
    
    console.log('📈 EXTRACTION SUMMARY:');
    console.log(`   Content Type: ${substrate.content_type}`);
    console.log(`   Facts: ${substrate.summary.facts_count}`);
    console.log(`   Insights: ${substrate.summary.insights_count}`);
    console.log(`   Actions: ${substrate.summary.actions_count}`);
    console.log(`   Overall Confidence: ${substrate.extraction_confidence}`);
    
    console.log('\n' + '='.repeat(70));
  }
}

function analyzeAndPropose(content, name) {
  // Simulate the improved P1 substrate agent analysis
  const contentType = detectContentType(content);
  
  let blocks = [];
  let context_items = [];
  
  if (contentType === 'financial') {
    // Financial content analysis
    blocks = [
      {
        semantic_type: "summary",
        title: "Q3 2024 Financial Performance Summary", 
        content: "TechCorp delivered strong Q3 results with $127M revenue (+18% YoY), 71% gross margins, and 847 new enterprise customers.",
        confidence_score: 0.92
      },
      {
        semantic_type: "metric",
        title: "Revenue Growth Metric",
        content: "Q3 2024 revenue of $127 million represents 18% year-over-year growth",
        confidence_score: 0.95
      },
      {
        semantic_type: "metric", 
        title: "SaaS Revenue Mix",
        content: "SaaS recurring revenue now represents 85% of total revenue, up from 78% last quarter",
        confidence_score: 0.93
      },
      {
        semantic_type: "quote",
        title: "CEO Statement on Customer Acquisition",
        content: "We added 847 new enterprise customers this quarter. Customer acquisition cost decreased 12% while average contract value increased 23%",
        confidence_score: 0.88
      },
      {
        semantic_type: "finding",
        title: "Operational Efficiency Gains",
        content: "Gross margins improved to 71%, driven by operational efficiency gains and improved pricing on enterprise contracts",
        confidence_score: 0.85
      }
    ];
    
    context_items = [
      { label: "TechCorp Inc", content: "Company: Public technology company reporting Q3 earnings", kind: "entity" },
      { label: "Sarah Martinez", content: "Person: Chief Executive Officer providing earnings commentary", kind: "entity" },
      { label: "Mike Chen", content: "Person: Chief Financial Officer discussing financial metrics", kind: "entity" },
      { label: "SaaS Business Model", content: "Strategy: 85% recurring revenue indicates strong subscription model", kind: "classification" },
      { label: "Enterprise Focus", content: "Market: 847 new enterprise customers with improved pricing power", kind: "classification" }
    ];
    
  } else if (contentType === 'security') {
    // Security incident analysis
    blocks = [
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
    ];
    
    context_items = [
      { label: "185.220.101.42", content: "IP Address: Malicious source from Estonia used in attack", kind: "entity" },
      { label: "j.admin@company.com", content: "Account: Compromised administrative account", kind: "entity" },
      { label: "customer_data table", content: "System: Database containing customer PII accessed by attacker", kind: "entity" },
      { label: "Phishing Attack", content: "Attack Vector: Social engineering via convincing IT security email", kind: "classification" },
      { label: "Data Breach", content: "Impact: 1,247 customer records accessed (names, emails, encrypted)", kind: "classification" }
    ];
    
  } else if (contentType === 'product') {
    // Product requirements analysis
    blocks = [
      {
        semantic_type: "summary",
        title: "Mobile Push Notifications v2.0 Requirements",
        content: "Product enhancement to increase notification engagement from 8.2% to 18% through personalization and intelligent timing.",
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
      },
      {
        semantic_type: "action",
        title: "A/B Testing Framework (Medium Priority)",
        content: "Develop A/B testing framework for notification copy optimization without code deployment",
        confidence_score: 0.83
      }
    ];
    
    context_items = [
      { label: "Lisa Wong", content: "Person: Product Manager leading notifications v2.0 initiative", kind: "entity" },
      { label: "David Kim", content: "Person: Engineering Lead responsible for technical implementation", kind: "entity" },
      { label: "iOS 14+ and Android 11+", content: "Technology: Minimum platform requirements for feature support", kind: "entity" },
      { label: "User Personalization", content: "Strategy: ML-driven content and timing personalization approach", kind: "classification" },
      { label: "Notification Fatigue", content: "Problem: 45% of users disabled notifications due to irrelevance", kind: "classification" }
    ];
  }
  
  return {
    content_type: contentType,
    blocks,
    context_items,
    extraction_confidence: 0.89,
    summary: {
      facts_count: blocks.filter(b => ['metric', 'event', 'finding'].includes(b.semantic_type)).length,
      insights_count: blocks.filter(b => b.semantic_type === 'insight').length, 
      actions_count: blocks.filter(b => b.semantic_type === 'action').length,
      primary_theme: name.split(' ')[0].toLowerCase()
    }
  };
}

function detectContentType(content) {
  const lower = content.toLowerCase();
  
  const financial = ['revenue', 'margin', 'quarter', 'earnings', 'ceo', 'cfo'].some(k => lower.includes(k));
  const security = ['incident', 'breach', 'attack', 'malicious', 'credential'].some(k => lower.includes(k));
  const product = ['requirements', 'users', 'features', 'metrics', 'product'].some(k => lower.includes(k));
  
  if (financial) return 'financial';
  if (security) return 'security'; 
  if (product) return 'product';
  return 'general';
}

// Run the examples
if (require.main === module) {
  showActualSubstrateExamples().catch(console.error);
}

module.exports = { showActualSubstrateExamples };