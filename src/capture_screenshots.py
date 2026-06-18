import os
import sys
import time
from playwright.sync_api import sync_playwright

def main():
    print("==================================================")
    print("      AUTOMATED DASHBOARD SCREENSHOT CAPTURE      ")
    print("==================================================")
    
    screenshots_dir = 'screenshots'
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Start Playwright
    with sync_playwright() as p:
        print("Launching headless Chromium browser...")
        # Launch browser. We fall back to standard systems if chromium is not installed,
        # but usually 'playwright install' can install it if missing.
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as e:
            print(f"Error launching browser: {e}")
            print("Attempting to run 'playwright install'...")
            os.system("playwright install chromium")
            browser = p.chromium.launch(headless=True)
            
        page = browser.new_page()
        # Set viewport to high-res laptop screen
        page.set_viewport_size({"width": 1440, "height": 900})
        
        url = 'http://localhost:5173/'
        print(f"Navigating to dashboard at {url}...")
        try:
            page.goto(url, timeout=30000)
            # Wait for main header to load
            page.wait_for_selector('h1', timeout=15000)
            print("Dashboard loaded successfully.")
        except Exception as e:
            print(f"Error connecting to Vite dev server: {e}")
            print("Please ensure the React Vite dev server is running at http://localhost:5173/")
            browser.close()
            sys.exit(1)
            
        # Define tabs, selectors, and output filenames
        tabs = [
            ("overview", "text=Anomaly Overview", "overview.png"),
            ("anthropology", "text=Cyber Anthropology", "anthropology.png"),
            ("drift", "text=Drift Analytics", "drift_analytics.png"),
            ("similarity", "text=Similarity Matrix", "similarity_heatmap.png"),
            ("research", "text=Research & Sweeps", "research_results.png")
        ]
        
        for name, selector, filename in tabs:
            print(f"Switching to tab: {name}...")
            try:
                page.locator(selector).click()
                time.sleep(1.2) # Let animations and graphs settle
                
                # Take screenshot of the viewport
                out_path = os.path.join(screenshots_dir, filename)
                page.screenshot(path=out_path)
                print(f"  Saved screenshot to {out_path}")
            except Exception as e:
                print(f"  Error capturing {name} tab: {e}")
                
        browser.close()
        print("Screenshot capture completed.")
        print("==================================================")

if __name__ == '__main__':
    main()
