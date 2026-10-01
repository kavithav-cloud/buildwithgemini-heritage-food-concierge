import asyncio
import os
import glob
import shutil
import subprocess
from playwright.async_api import async_playwright

APP_URL = "https://heritage-food-concierge-ui-243764908694.us-central1.run.app"
OUTPUT_DIR = "/config/Desktop/Session1/heritage-food-concierge/demo_output"

async def record_demo():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    async with async_playwright() as p:
        print("Launching Chromium browser...")
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        print(f"Navigating to {APP_URL}...")
        await page.goto(APP_URL, wait_until="networkidle")
        await asyncio.sleep(3)  # Observe dark mode UI, category chips, greeting

        input_box = page.locator("#input")
        form = page.locator("#form")

        # Step 1: Prompt 1 - Category filter / Food tour search
        print("Executing Prompt 1: Food tour search in Rome...")
        food_chip = page.locator(".chip:has-text('Food Tours')")
        if await food_chip.count() > 0:
            await food_chip.click()
            await asyncio.sleep(1.5)

        await input_box.fill("Show me food tours in Rome with authentic pasta dishes")
        await asyncio.sleep(1)
        await form.evaluate("f => f.dispatchEvent(new Event('submit', {cancelable: true, bubbles: true}))")

        print("Waiting for response and A2UI card rendering...")
        await page.wait_for_selector(".a2card, .msg.agent", timeout=30000)
        await asyncio.sleep(6)  # Pause to showcase rendered cards with images

        # Step 2: Prompt 2 - Richer prompt with generated image / postcard
        print("Executing Prompt 2: Postcard generation tool call...")
        await input_box.fill("generate visual postcard of rome")
        await asyncio.sleep(1)
        await form.evaluate("f => f.dispatchEvent(new Event('submit', {cancelable: true, bubbles: true}))")

        print("Waiting for generated postcard image...")
        await asyncio.sleep(12)  # Wait for postcard generation tool and image rendering

        # Click postcard image to open Lightbox Modal
        postcard_img = page.locator(".a2img").last
        if await postcard_img.count() > 0:
            print("Opening Lightbox Modal...")
            await postcard_img.click()
            await asyncio.sleep(3.5)

            # Close Lightbox Modal
            modal = page.locator("#lightbox-modal")
            if await modal.is_visible():
                await modal.click()
                await asyncio.sleep(2)

        await asyncio.sleep(3)
        await context.close()
        await browser.close()
        print("Browser session closed. Video recording finalized.")

if __name__ == "__main__":
    asyncio.run(record_demo())
