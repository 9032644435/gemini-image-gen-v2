from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://127.0.0.1:8080")

    # Fill out the form
    page.fill("input[name=prompt]", "a test prompt")
    page.select_option("select[name=image_count]", "2")
    page.select_option("select[name=aspect_ratio]", "16:9")

    # Submit the form and wait for the blur effect
    page.click("button[type=submit]")
    expect(page.locator("body")).not_to_have_css("filter", "none")

    # Wait for the loading message to disappear, the blur to be removed, and the results to appear
    page.wait_for_selector("#loading", state="hidden")
    expect(page.locator("body")).to_have_css("filter", "none")
    page.wait_for_selector("#results-container img")

    # Ensure the correct number of images and download buttons are present
    expect(page.locator("#results-container img")).to_have_count(2)
    expect(page.locator("#results-container .download-btn")).to_have_count(2)

    page.screenshot(path="jules-scratch/verification/verification.png")
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
