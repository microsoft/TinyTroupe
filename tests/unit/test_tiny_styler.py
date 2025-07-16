import pytest
import textwrap

import logging
logger = logging.getLogger("tinytroupe")

import sys
# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

from testing_utils import *

from tinytroupe.enrichment.tiny_styler import TinyStyler

def test_apply_style():
    """Test the basic functionality of apply_style using the actual LLM."""
    content_to_style = textwrap.dedent("""
    The results of our quarterly financial analysis show a 15% increase in revenue 
    and a 5% decrease in operating costs. Customer acquisition costs have decreased
    by 10% while retention rates have improved from 65% to 78%. Our new product line
    has contributed to 25% of this quarter's growth.
    """).strip()

    style = "casual"
    
    # Call the method with the actual LLM
    styler = TinyStyler()
    result = styler.apply_style(
        content=content_to_style,
        style=style,
        content_type="report", 
        verbose=True
    )
    
    # lowercase the content to make assertions case-insensitive
    result = result.lower() if result else None
    # Log the result for manual inspection
    logger.debug(f"Styled content: {result}")

    # Assert result
    assert result is not None, "The result should not be None"
    # Check that key information is preserved in the styled content
    assert ("15" in result) or ("fifteen" in result), "The styled content should preserve the 15% revenue increase information"
    assert ("5" in result) or ("five" in result), "The styled content should preserve the 5% decrease in operating costs information"
    assert ("78" in result) or ("seventy-eight" in result), "The styled content should preserve the 78% retention rate information"
    
    # Semantic verification: ensure the styled content maintains financial/business meaning
    assert proposition_holds(result + " - The content discusses financial performance, revenue, costs, or business metrics")
    
    # Semantic verification: ensure the styled content is actually in casual style
    assert proposition_holds(result + " - The writing style is casual, informal, or conversational rather than formal or technical")
    
    # Check that the style has been applied (this is more subjective)
    # For casual style, we might expect certain casual markers
    casual_indicators = ["!", "we", "our", "pretty", "nice", "great", "awesome", "cool", "hey", "check", "looking"]
    has_casual_tone = any(indicator in result.lower() for indicator in casual_indicators)
    assert has_casual_tone, "The result should have a casual tone"
    
    logger.debug(f"Styling result: {result}")

def test_apply_style_with_different_styles():
    """Test applying different styles to the same content."""
    content_to_style = "We need to improve our customer retention strategies to boost quarterly performance."
    
    # Test with three different styles
    styles = ["technical", "professional", "enthusiastic"]
    results = {}
    
    styler = TinyStyler()
    for style in styles:
        results[style] = styler.apply_style(
            content=content_to_style,
            style=style
        )
        # Basic validation
        assert results[style] is not None, f"The {style} styled result should not be None"
        assert "customer retention" in results[style], f"The {style} styled content should preserve the key information"
        
        # Semantic verification: ensure each style is appropriately applied
        if style == "technical":
            assert proposition_holds(results[style] + " - The writing style is technical, detailed, or uses professional/technical language")
        elif style == "professional":
            assert proposition_holds(results[style] + " - The writing style is professional, formal, or business-like")
        elif style == "enthusiastic":
            assert proposition_holds(results[style] + " - The writing style is enthusiastic, energetic, or shows excitement")
    
    # Verify that different styles produce different results
    assert results["technical"] != results["professional"] != results["enthusiastic"], "Different styles should produce different results"
    
    # Log results for manual inspection
    for style, result in results.items():
        logger.debug(f"{style} styling result: {result}")

def test_context_cache_usage():
    """Test that context cache is properly used when enabled."""
    # Create styler with context caching enabled
    styler = TinyStyler(use_past_results_in_context=True)
    
    # First styling
    first_content = "The team completed the project ahead of schedule."
    first_style = "formal"
    first_result = styler.apply_style(content=first_content, style=first_style)
    
    # Second styling - should have context from first
    second_content = "We saved 15% on the project budget."
    second_style = "casual"
    second_result = styler.apply_style(content=second_content, style=second_style)
    
    # Verify context cache has been populated
    assert len(styler.context_cache) == 2, "Context cache should contain 2 entries"
    assert styler.context_cache[0]["original"] == first_content
    assert styler.context_cache[0]["style"] == first_style
    assert styler.context_cache[0]["styled"] == first_result
    
    # Third styling with explicit context
    third_content = "Customer satisfaction increased by 20%."
    external_context = [{"original": "Original text", "style": "poetic", "styled": "Poetic version"}]
    third_result = styler.apply_style(
        content=third_content, 
        style="technical",
        context_cache=external_context
    )
    
    # Verify context_cache parameter was respected (it should override the instance's context_cache)
    assert len(styler.context_cache) == 3, "Context cache should now contain 3 entries"

def test_temperature_parameter():
    """Test that temperature parameter affects output variability."""
    content_to_style = "The product launch is scheduled for next month."
    style = "creative"
    
    # Generate outputs with different temperatures
    styler = TinyStyler()
    results_low_temp = [
        styler.apply_style(content=content_to_style, style=style, temperature=0.1)
        for _ in range(2)
    ]
    
    results_high_temp = [
        styler.apply_style(content=content_to_style, style=style, temperature=1.0)
        for _ in range(2)
    ]
    
    # With very low temperature, results should be more similar to each other
    # With high temperature, results should be more varied
    # This is a probabilistic test, so it might not always pass
    
    # Log results for manual inspection
    logger.debug(f"Low temperature results: {results_low_temp}")
    logger.debug(f"High temperature results: {results_high_temp}")
    
    # If we want more deterministic testing, we could check that all results preserve key information
    for result in results_low_temp + results_high_temp:
        assert "product launch" in result.lower(), "All styled content should preserve key information"
        assert "next month" in result.lower(), "All styled content should preserve time information"

if __name__ == '__main__':
    pytest.main()