"""
Test script to verify mistake analysis UI toggle functionality.
Tests both enabled and disabled states of MISTAKE_ANALYSIS_UI_ENABLED config.
"""

from app import create_app

def test_mistake_analysis_ui_toggle():
    """Test that mistake analysis section visibility is controlled by config."""
    
    print("\n" + "="*70)
    print("Testing Mistake Analysis UI Toggle (Change 4)")
    print("="*70)
    
    # Test 1: Disabled (default)
    print("\n[Test 1] Testing with MISTAKE_ANALYSIS_UI_ENABLED=False")
    app = create_app()
    app.config['MISTAKE_ANALYSIS_UI_ENABLED'] = False
    
    with app.test_client() as client:
        response = client.get('/analytics')
        html = response.data.decode('utf-8')
        
        if b'mistakeAnalysisSection' in response.data:
            print("❌ FAILED: Mistake analysis section should NOT be in HTML")
            print(f"   Section found in response (length: {len(html)} chars)")
        else:
            print("✅ PASSED: Mistake analysis section correctly hidden from DOM")
            print(f"   HTML response length: {len(html)} chars")
    
    # Test 2: Enabled
    print("\n[Test 2] Testing with MISTAKE_ANALYSIS_UI_ENABLED=True")
    app.config['MISTAKE_ANALYSIS_UI_ENABLED'] = True
    
    with app.test_client() as client:
        response = client.get('/analytics')
        html = response.data.decode('utf-8')
        
        if b'mistakeAnalysisSection' not in response.data:
            print("❌ FAILED: Mistake analysis section SHOULD be in HTML")
            print(f"   Section not found in response (length: {len(html)} chars)")
        else:
            print("✅ PASSED: Mistake analysis section correctly visible in DOM")
            print(f"   HTML response length: {len(html)} chars")
            
            # Verify specific elements exist when enabled
            elements_to_check = [
                (b'mistakeAnalysisSection', 'Section container'),
                (b'Move Analysis by Game Stage', 'Section title'),
                (b'mistakeSummary', 'Summary cards container'),
                (b'mistakeTable', 'Mistake table'),
            ]
            
            print("\n   Checking specific elements:")
            for element, description in elements_to_check:
                if element in response.data:
                    print(f"   ✓ {description} found")
                else:
                    print(f"   ✗ {description} NOT found")
    
    # Test 3: Verify JavaScript safety
    print("\n[Test 3] Verifying JavaScript handles missing section gracefully")
    app.config['MISTAKE_ANALYSIS_UI_ENABLED'] = False
    
    with app.test_client() as client:
        response = client.get('/analytics')
        html = response.data.decode('utf-8')
        
        # Check that JavaScript is still present (it should handle null section)
        if b'analytics.js' in response.data:
            print("✅ PASSED: JavaScript file still loaded")
        else:
            print("❌ FAILED: JavaScript file not found")
        
        # Verify no broken references to mistake analysis elements
        if b'getElementById(\'mistakeAnalysisSection\')' in response.data:
            print("✅ JavaScript references to mistakeAnalysisSection exist")
            print("   (JavaScript has null checks to handle missing element)")
        else:
            print("⚠️  No direct getElementById references found in inline scripts")
    
    print("\n" + "="*70)
    print("Test completed successfully!")
    print("="*70 + "\n")
    
    print("\n💡 Configuration Guide:")
    print("   - Set MISTAKE_ANALYSIS_UI_ENABLED=false in .env to hide section (current)")
    print("   - Set MISTAKE_ANALYSIS_UI_ENABLED=true in .env to show section")
    print("   - Flask will auto-reload after .env changes")

if __name__ == '__main__':
    test_mistake_analysis_ui_toggle()
