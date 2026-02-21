"""
Playwright test to verify GTM loads without JavaScript errors.
"""
from playwright.sync_api import sync_playwright
import sys


def test_gtm_no_console_errors():
    """Test that GTM doesn't introduce JavaScript errors."""
    print("\n" + "="*60)
    print("GTM BROWSER TEST - Console Error Check")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Collect console messages
        console_messages = []
        errors = []
        
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            if msg.type == 'error':
                errors.append(msg.text)
        
        page.on('console', handle_console)
        
        # Navigate to the page
        print("\nNavigating to http://localhost:5000...")
        try:
            response = page.goto('http://localhost:5000', wait_until='networkidle', timeout=10000)
            print(f"✓ Page loaded with status: {response.status}")
        except Exception as e:
            print(f"✗ Failed to load page: {e}")
            browser.close()
            return False
        
        # Wait for GTM to load
        print("\nWaiting for GTM to initialize...")
        try:
            # Check if dataLayer exists
            datalayer_exists = page.evaluate("() => typeof window.dataLayer !== 'undefined'")
            if datalayer_exists:
                print("✓ window.dataLayer is defined")
                
                # Get dataLayer contents
                datalayer_length = page.evaluate("() => window.dataLayer ? window.dataLayer.length : 0")
                print(f"✓ dataLayer has {datalayer_length} entries")
            else:
                print("⚠ window.dataLayer is not defined")
        except Exception as e:
            print(f"⚠ Could not check dataLayer: {e}")
        
        # Check for GTM script in the page
        print("\nVerifying GTM scripts in DOM...")
        gtm_scripts = page.evaluate("""() => {
            const scripts = Array.from(document.querySelectorAll('script'));
            return scripts.filter(s => s.src && s.src.includes('googletagmanager.com')).length;
        }""")
        print(f"✓ Found {gtm_scripts} GTM script tag(s) in DOM")
        
        # Check for noscript iframe
        gtm_noscript = page.evaluate("""() => {
            const noscripts = Array.from(document.querySelectorAll('noscript'));
            return noscripts.some(n => n.innerHTML.includes('googletagmanager.com/ns.html'));
        }""")
        if gtm_noscript:
            print("✓ GTM noscript iframe present")
        else:
            print("⚠ GTM noscript iframe not found")
        
        # Check for console errors
        print("\nConsole Error Check...")
        if errors:
            print(f"✗ Found {len(errors)} console error(s):")
            for error in errors[:5]:  # Show first 5 errors
                print(f"   - {error}")
        else:
            print("✓ No console errors detected")
        
        # Show sample of console messages
        if console_messages:
            print(f"\nTotal console messages: {len(console_messages)}")
            print("Sample messages:")
            for msg in console_messages[:3]:
                print(f"   {msg}")
        
        browser.close()
        
        print("\n" + "="*60)
        if not errors:
            print("✓ GTM BROWSER TEST PASSED - No console errors")
        else:
            print("⚠ GTM loaded but with console errors")
        print("="*60)
        
        return len(errors) == 0


if __name__ == "__main__":
    success = test_gtm_no_console_errors()
    sys.exit(0 if success else 1)
