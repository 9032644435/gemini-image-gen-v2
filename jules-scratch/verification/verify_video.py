from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://127.0.0.1:8080")

    # --- Test Video Generation Form ---

    # Fill out the video form
    page.fill("input[name=video_prompt]", "a test video prompt")
    page.select_option("select[name=video_aspect_ratio]", "9:16")
    page.fill("input[name=video_duration]", "8")

    # Submit the form
    page.click("#generate-video-form button[type=submit]")

    # Wait for the loading message to appear and have the correct text
    page.wait_for_selector("#video-loading", state="visible")
    expect(page.locator("#video-loading")).to_have_text("Operation Started. Video generation is processing asynchronously.")

    # Take a screenshot of the page
    page.screenshot(path="jules-scratch/verification/verification.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
