from analyzer import VOCAnalyzer

# Initialize analyzer (will print warning about missing key, which is fine for this test)
analyzer = VOCAnalyzer()

# Manually trigger log creation to verify the format
print("Testing log creation...")
analyzer._log_trace(
    category="Test_Category",
    input_data="[Review 1] This is a test input.",
    prompt_text="You are a VOC analyst... (Prompt content here)",
    response_text="### N [Test_Category] Result\n- Issue: Test successful"
)
