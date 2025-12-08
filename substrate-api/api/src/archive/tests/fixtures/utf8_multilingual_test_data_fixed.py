"""
UTF-8 and Multilingual Test Fixtures for P1 Substrate Agent v2
Fixed version with accurate span calculations
"""

def calculate_spans(content: str, target_texts: list) -> list:
    """Calculate accurate spans for target texts in content."""
    spans = []
    for text in target_texts:
        start_idx = content.find(text)
        if start_idx != -1:
            spans.append({
                "start": start_idx,
                "end": start_idx + len(text),
                "text": text
            })
    return spans

# Test fixture 1: Emoji and Unicode
EMOJI_CONTENT = """🚀 Project Goal: Launch MVP by Q2 2024 📅
Key constraint: Budget limited to $50K 💰
Success metric: 1000+ active users 👥
Technical requirement: Support 🌍 multiple languages"""

EMOJI_TARGET_TEXTS = [
    "🚀 Project Goal: Launch MVP by Q2 2024 📅",
    "Key constraint: Budget limited to $50K 💰", 
    "Success metric: 1000+ active users 👥",
    "Technical requirement: Support 🌍 multiple languages"
]

# Test fixture 2: Chinese/Japanese/Korean (CJK) 
CJK_CONTENT = """项目目标：提高用户体验和满意度
制约因素：开发团队只有3人
成功指标：用户满意度达到90%以上
技术实体：机器学习推荐系统"""

CJK_TARGET_TEXTS = [
    "项目目标：提高用户体验和满意度",
    "制约因素：开发团队只有3人", 
    "成功指标：用户满意度达到90%以上",
    "技术实体：机器学习推荐系统"
]

# Test fixture 3: Arabic (RTL)
ARABIC_CONTENT = """الهدف: تحسين تجربة المستخدم في التطبيق
القيد: الميزانية محدودة بـ 10000 دولار
المقياس: زيادة عدد المستخدمين إلى 5000
الكيان التقني: نظام التوصية الذكي"""

ARABIC_TARGET_TEXTS = [
    "الهدف: تحسين تجربة المستخدم في التطبيق",
    "القيد: الميزانية محدودة بـ 10000 دولار",
    "المقياس: زيادة عدد المستخدمين إلى 5000", 
    "الكيان التقني: نظام التوصية الذكي"
]

# Test fixture 4: Mixed scripts
MIXED_CONTENT = """Goal: Développer une app mobile 📱 (French)
制約: リソース不足 💼 (Japanese constraint)
Metric: ≥95% availability ⚡ (Technical KPI)
Entity: AI/ML система 🤖 (Russian/Cyrillic)"""

MIXED_TARGET_TEXTS = [
    "Goal: Développer une app mobile 📱 (French)",
    "制約: リソース不足 💼 (Japanese constraint)",
    "Metric: ≥95% availability ⚡ (Technical KPI)",
    "Entity: AI/ML система 🤖 (Russian/Cyrillic)"
]

# Test fixture 5: Unicode normalization
NORMALIZATION_CONTENT = """Goal: Café normalization test (é vs e + ´)
Constraint: Unicode NFC vs NFD handling
Metric: 100% character accuracy test"""

NORMALIZATION_TARGET_TEXTS = [
    "Goal: Café normalization test (é vs e + ´)",
    "Constraint: Unicode NFC vs NFD handling",
    "Metric: 100% character accuracy test"
]

# Generate all fixtures with calculated spans
UTF8_TEST_FIXTURES = [
    {
        "name": "emoji_unicode",
        "content": EMOJI_CONTENT,
        "expected_spans": calculate_spans(EMOJI_CONTENT, EMOJI_TARGET_TEXTS),
        "description": "Emoji and Unicode symbols test"
    },
    {
        "name": "cjk_characters", 
        "content": CJK_CONTENT,
        "expected_spans": calculate_spans(CJK_CONTENT, CJK_TARGET_TEXTS),
        "description": "Chinese/Japanese/Korean characters test"
    },
    {
        "name": "arabic_rtl",
        "content": ARABIC_CONTENT,
        "expected_spans": calculate_spans(ARABIC_CONTENT, ARABIC_TARGET_TEXTS), 
        "description": "Arabic right-to-left text test"
    },
    {
        "name": "mixed_scripts",
        "content": MIXED_CONTENT,
        "expected_spans": calculate_spans(MIXED_CONTENT, MIXED_TARGET_TEXTS),
        "description": "Mixed script and special character test"
    },
    {
        "name": "normalization",
        "content": NORMALIZATION_CONTENT,
        "expected_spans": calculate_spans(NORMALIZATION_CONTENT, NORMALIZATION_TARGET_TEXTS),
        "description": "Unicode normalization edge case test"
    }
]

def validate_span_integrity(content: str, spans: list) -> bool:
    """Validate that spans correctly map to expected text in content."""
    for span in spans:
        start, end, expected_text = span["start"], span["end"], span["text"]
        
        if start == -1:  # Text not found
            print(f"Text not found in content: '{expected_text}'")
            return False
        
        # Extract actual text from content using span indices
        actual_text = content[start:end]
        
        # Check if extracted text matches expected
        if actual_text != expected_text:
            print(f"Span validation failed:")
            print(f"  Expected: '{expected_text}'")
            print(f"  Actual: '{actual_text}'") 
            print(f"  Span: [{start}:{end}]")
            return False
    
    return True

def test_all_fixtures():
    """Test all UTF-8 fixtures for span integrity."""
    results = []
    
    for fixture in UTF8_TEST_FIXTURES:
        name = fixture["name"]
        content = fixture["content"]
        expected_spans = fixture["expected_spans"]
        
        print(f"\n🧪 Testing {name}:")
        print(f"Content length: {len(content)} chars")
        print(f"Spans: {len(expected_spans)}")
        
        is_valid = validate_span_integrity(content, expected_spans)
        results.append({
            "name": name,
            "valid": is_valid,
            "content_length": len(content),
            "span_count": len(expected_spans)
        })
        
        print(f"Result: {'✅ PASS' if is_valid else '❌ FAIL'}")
    
    return results

def generate_test_cases():
    """Generate test cases for P1 Agent v2 testing."""
    test_cases = []
    
    for fixture in UTF8_TEST_FIXTURES:
        test_case = {
            "dump_id": f"test-{fixture['name']}",
            "content": fixture["content"],
            "expected_provenance_count": len(fixture["expected_spans"]),
            "expected_spans": fixture["expected_spans"],
            "test_type": "utf8_multilingual",
            "description": fixture["description"]
        }
        test_cases.append(test_case)
    
    return test_cases

if __name__ == "__main__":
    print("🧪 Testing UTF-8 and multilingual fixtures (fixed version)...")
    results = test_all_fixtures()
    
    passed = sum(1 for r in results if r["valid"])
    total = len(results)
    
    print(f"\n📊 Final Results: {passed}/{total} fixtures passed")
    
    if passed == total:
        print("✅ All UTF-8 fixtures are valid!")
        
        # Generate test cases for integration testing
        print("\n📋 Generating test cases for P1 Agent v2...")
        test_cases = generate_test_cases()
        print(f"Generated {len(test_cases)} multilingual test cases")
        
        for case in test_cases:
            print(f"  - {case['test_type']}: {case['description']}")
            
    else:
        print("❌ Some fixtures failed - check span calculations")
        exit(1)