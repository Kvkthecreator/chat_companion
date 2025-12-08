"""
UTF-8 and Multilingual Test Fixtures for P1 Substrate Agent v2

Tests span index integrity with emoji, CJK characters, and RTL text.
Critical for validating provenance ranges don't have off-by-one errors.
"""

# Test fixture 1: Emoji and Unicode
EMOJI_CONTENT = """🚀 Project Goal: Launch MVP by Q2 2024 📅
Key constraint: Budget limited to $50K 💰
Success metric: 1000+ active users 👥
Technical requirement: Support 🌍 multiple languages"""

EMOJI_EXPECTED_SPANS = [
    {"start": 0, "end": 39, "text": "🚀 Project Goal: Launch MVP by Q2 2024 📅"},  # Goal span
    {"start": 40, "end": 81, "text": "Key constraint: Budget limited to $50K 💰"},  # Constraint span  
    {"start": 82, "end": 116, "text": "Success metric: 1000+ active users 👥"},  # Metric span
    {"start": 117, "end": 171, "text": "Technical requirement: Support 🌍 multiple languages"}  # Entity span
]

# Test fixture 2: Chinese/Japanese/Korean (CJK)
CJK_CONTENT = """项目目标：提高用户体验和满意度
制约因素：开发团队只有3人
成功指标：用户满意度达到90%以上
技术实体：机器学习推荐系统"""

CJK_EXPECTED_SPANS = [
    {"start": 0, "end": 15, "text": "项目目标：提高用户体验和满意度"},    # Goal
    {"start": 16, "end": 31, "text": "制约因素：开发团队只有3人"},       # Constraint  
    {"start": 32, "end": 51, "text": "成功指标：用户满意度达到90%以上"},  # Metric
    {"start": 52, "end": 67, "text": "技术实体：机器学习推荐系统"}       # Entity
]

# Test fixture 3: Arabic (RTL)
ARABIC_CONTENT = """الهدف: تحسين تجربة المستخدم في التطبيق
القيد: الميزانية محدودة بـ 10000 دولار  
المقياس: زيادة عدد المستخدمين إلى 5000
الكيان التقني: نظام التوصية الذكي"""

ARABIC_EXPECTED_SPANS = [
    {"start": 0, "end": 37, "text": "الهدف: تحسين تجربة المستخدم في التطبيق"},     # Goal
    {"start": 38, "end": 75, "text": "القيد: الميزانية محدودة بـ 10000 دولار"},    # Constraint
    {"start": 78, "end": 116, "text": "المقياس: زيادة عدد المستخدمين إلى 5000"},   # Metric  
    {"start": 117, "end": 150, "text": "الكيان التقني: نظام التوصية الذكي"}        # Entity
]

# Test fixture 4: Mixed scripts with special characters
MIXED_CONTENT = """Goal: Développer une app mobile 📱 (French)
制約: リソース不足 💼 (Japanese constraint)  
Metric: ≥95% availability ⚡ (Technical KPI)
Entity: AI/ML система 🤖 (Russian/Cyrillic)"""

MIXED_EXPECTED_SPANS = [
    {"start": 0, "end": 44, "text": "Goal: Développer une app mobile 📱 (French)"},
    {"start": 45, "end": 79, "text": "制約: リソース不足 💼 (Japanese constraint)"},
    {"start": 82, "end": 118, "text": "Metric: ≥95% availability ⚡ (Technical KPI)"},
    {"start": 119, "end": 156, "text": "Entity: AI/ML система 🤖 (Russian/Cyrillic)"}
]

# Test fixture 5: Edge case - Zero-width characters and normalization
NORMALIZATION_CONTENT = """Goal: Café normalization test (é vs e + ´)
Constraint: Unicode NFC vs NFD handling  
Metric: 100% character accuracy test"""

NORMALIZATION_EXPECTED_SPANS = [
    {"start": 0, "end": 42, "text": "Goal: Café normalization test (é vs e + ´)"},
    {"start": 43, "end": 79, "text": "Constraint: Unicode NFC vs NFD handling"},
    {"start": 82, "end": 116, "text": "Metric: 100% character accuracy test"}
]

# All test fixtures for comprehensive validation
UTF8_TEST_FIXTURES = [
    {
        "name": "emoji_unicode",
        "content": EMOJI_CONTENT,
        "expected_spans": EMOJI_EXPECTED_SPANS,
        "description": "Emoji and Unicode symbols test"
    },
    {
        "name": "cjk_characters", 
        "content": CJK_CONTENT,
        "expected_spans": CJK_EXPECTED_SPANS,
        "description": "Chinese/Japanese/Korean characters test"
    },
    {
        "name": "arabic_rtl",
        "content": ARABIC_CONTENT, 
        "expected_spans": ARABIC_EXPECTED_SPANS,
        "description": "Arabic right-to-left text test"
    },
    {
        "name": "mixed_scripts",
        "content": MIXED_CONTENT,
        "expected_spans": MIXED_EXPECTED_SPANS, 
        "description": "Mixed script and special character test"
    },
    {
        "name": "normalization",
        "content": NORMALIZATION_CONTENT,
        "expected_spans": NORMALIZATION_EXPECTED_SPANS,
        "description": "Unicode normalization edge case test"
    }
]

def validate_span_integrity(content: str, spans: list) -> bool:
    """
    Validate that spans correctly map to expected text in content.
    Returns True if all spans are valid, False otherwise.
    """
    for span in spans:
        start, end, expected_text = span["start"], span["end"], span["text"]
        
        # Extract actual text from content using span indices
        actual_text = content[start:end]
        
        # Check if extracted text matches expected
        if actual_text != expected_text:
            print(f"Span validation failed:")
            print(f"  Expected: '{expected_text}'")
            print(f"  Actual: '{actual_text}'")
            print(f"  Span: [{start}:{end}]")
            print(f"  Content length: {len(content)}")
            return False
    
    return True

def test_all_fixtures():
    """Test all UTF-8 fixtures for span integrity."""
    results = []
    
    for fixture in UTF8_TEST_FIXTURES:
        name = fixture["name"]
        content = fixture["content"]
        expected_spans = fixture["expected_spans"]
        
        is_valid = validate_span_integrity(content, expected_spans)
        results.append({
            "name": name,
            "valid": is_valid,
            "content_length": len(content),
            "span_count": len(expected_spans)
        })
        
        print(f"✅ {name}: {'PASS' if is_valid else 'FAIL'}")
    
    return results

if __name__ == "__main__":
    print("🧪 Testing UTF-8 and multilingual fixtures...")
    results = test_all_fixtures()
    
    passed = sum(1 for r in results if r["valid"])
    total = len(results)
    
    print(f"\n📊 Results: {passed}/{total} fixtures passed")
    
    if passed == total:
        print("✅ All UTF-8 fixtures are valid!")
    else:
        print("❌ Some fixtures failed - check span calculations")
        exit(1)