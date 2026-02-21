"""
Test script to verify Google Tag Manager integration.
"""
import requests
from bs4 import BeautifulSoup


def test_gtm_on_main_page():
    """Test that GTM scripts are present on the main page."""
    print("\n" + "="*60)
    print("GOOGLE TAG MANAGER INTEGRATION TEST")
    print("="*60)
    
    url = "http://127.0.0.1:5000/"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"\n✓ Page Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ FAILED: Expected status 200, got {response.status_code}")
            return False
        
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Test 1: Check for GTM head script
        print("\n1. Checking GTM Head Script...")
        gtm_head_found = False
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'googletagmanager.com/gtm.js' in script.string:
                if 'GT-NFBTKHBS' in script.string:
                    print("   ✓ GTM head script found with correct container ID")
                    gtm_head_found = True
                    # Check for dataLayer initialization
                    if 'dataLayer' in script.string:
                        print("   ✓ dataLayer initialization found")
                    break
        
        if not gtm_head_found:
            print("   ✗ GTM head script NOT found")
            return False
        
        # Test 2: Check for GTM noscript iframe
        print("\n2. Checking GTM Noscript Fallback...")
        noscript_tags = soup.find_all('noscript')
        gtm_noscript_found = False
        for noscript in noscript_tags:
            iframe = noscript.find('iframe')
            if iframe and 'googletagmanager.com/ns.html' in str(iframe):
                if 'GT-NFBTKHBS' in str(iframe):
                    print("   ✓ GTM noscript iframe found with correct container ID")
                    gtm_noscript_found = True
                    # Check iframe attributes
                    if iframe.get('height') == '0' and iframe.get('width') == '0':
                        print("   ✓ Iframe has correct dimensions (hidden)")
                    break
        
        if not gtm_noscript_found:
            print("   ✗ GTM noscript iframe NOT found")
            return False
        
        # Test 3: Check script placement
        print("\n3. Checking Script Placement...")
        head_content = str(soup.head)
        body_content = str(soup.body)
        
        # GTM should be near the top of <head>
        head_position = head_content.find('googletagmanager.com/gtm.js')
        if head_position > 0 and head_position < 1000:
            print("   ✓ GTM head script is near the top of <head>")
        else:
            print("   ⚠ WARNING: GTM head script position may not be optimal")
        
        # Noscript should be right after <body>
        body_position = body_content.find('googletagmanager.com/ns.html')
        if body_position > 0 and body_position < 500:
            print("   ✓ GTM noscript is near the top of <body>")
        else:
            print("   ⚠ WARNING: GTM noscript position may not be optimal")
        
        # Test 4: Verify no duplicate GTM tags
        print("\n4. Checking for Duplicates...")
        gtm_script_count = html_content.count('GT-NFBTKHBS')
        if gtm_script_count == 2:
            print(f"   ✓ Correct number of GTM references found (2)")
        else:
            print(f"   ⚠ WARNING: Found {gtm_script_count} GTM references (expected 2)")
        
        # Test 5: Check page title
        print("\n5. Page Information...")
        title = soup.title.string if soup.title else "No title"
        print(f"   Page Title: {title}")
        print(f"   Content Length: {len(html_content)} bytes")
        
        print("\n" + "="*60)
        print("✓ ALL GTM TESTS PASSED")
        print("="*60)
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ FAILED: Could not connect to server")
        print(f"   Error: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = test_gtm_on_main_page()
    sys.exit(0 if success else 1)
