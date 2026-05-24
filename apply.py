"""
apply.py — Fill job application forms automatically.

Usage:
    python apply.py --url <greenhouse-job-url> --profile profile.yaml [--submit]

Supports: Greenhouse ATS
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import yaml
from playwright.async_api import async_playwright, Page


# ── Greenhouse form filler ─────────────────────────────────────────────────────

async def fill_greenhouse(page: Page, profile: dict, resume_path: str | None, cover_letter_path: str | None) -> None:
    await page.wait_for_selector("#application_form", timeout=15_000)

    fields = {
        'input[name="job_application[first_name]"]': profile.get("first_name", ""),
        'input[name="job_application[last_name]"]': profile.get("last_name", ""),
        'input[name="job_application[email]"]': profile.get("email", ""),
        'input[name="job_application[phone]"]': profile.get("phone", ""),
    }
    for selector, value in fields.items():
        el = page.locator(selector).first
        if await el.count() > 0 and value:
            await el.fill(value)

    # Location
    loc_selector = 'input[name="job_application[location]"]'
    loc_el = page.locator(loc_selector).first
    if await loc_el.count() > 0 and profile.get("location"):
        await loc_el.fill(profile["location"])
        await page.wait_for_timeout(600)
        dropdown = page.locator(".pac-item, [role='option']").first
        if await dropdown.count() > 0:
            await dropdown.click()

    # LinkedIn / website
    for field_name, key in [("linkedin_url", "linkedin"), ("website", "website")]:
        sel = f'input[name="job_application[{field_name}]"]'
        el = page.locator(sel).first
        if await el.count() > 0 and profile.get(key):
            await el.fill(profile[key])

    # Resume upload
    if resume_path and Path(resume_path).exists():
        resume_input = page.locator('input[type="file"]').first
        if await resume_input.count() > 0:
            await resume_input.set_input_files(resume_path)
            await page.wait_for_timeout(1000)

    # Cover letter (textarea, JS-injected for hidden fields)
    if cover_letter_path and Path(cover_letter_path).exists():
        cl_text = Path(cover_letter_path).read_text()
        # Try paste toggle first
        paste_btn = page.locator("text=Paste").first
        if await paste_btn.count() > 0:
            await paste_btn.click()
            await page.wait_for_timeout(300)
        ta = page.locator('textarea[name="cover_letter_text"]').first
        if await ta.count() > 0:
            await page.evaluate(
                """(text) => {
                    const el = document.querySelector('textarea[name="cover_letter_text"]');
                    if (el) {
                        el.removeAttribute('hidden');
                        el.style.display = 'block';
                        el.value = text;
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                    }
                }""",
                cl_text,
            )

    # Custom questions — work authorization dropdowns
    for q_text, answer in profile.get("custom_answers", {}).items():
        label = page.locator(f"label:has-text('{q_text}')").first
        if await label.count() > 0:
            for_id = await label.get_attribute("for")
            if for_id:
                el = page.locator(f"#{for_id}").first
                tag = await el.evaluate("el => el.tagName.toLowerCase()")
                if tag == "select":
                    await el.select_option(label=answer)
                elif tag == "input":
                    await el.fill(answer)


async def run(url: str, profile: dict, submit: bool, screenshot_path: str) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        print(f"Navigating to {url}")
        await page.goto(url, wait_until="networkidle", timeout=30_000)

        resume_path = profile.get("resume_pdf")
        cover_letter_path = profile.get("cover_letter_txt")

        if "greenhouse.io" in url:
            await fill_greenhouse(page, profile, resume_path, cover_letter_path)
        else:
            print("WARNING: Unsupported ATS. Only Greenhouse is currently supported.")

        print(f"Saving screenshot to {screenshot_path}")
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved: {screenshot_path}")

        if submit:
            submit_btn = page.locator("#submit_app, button[type='submit']:not([hidden])").last
            if await submit_btn.count() > 0:
                print("Submitting application...")
                await submit_btn.click()
                await page.wait_for_timeout(3000)
                await page.screenshot(path=screenshot_path.replace(".png", "_after_submit.png"))
                print("Submitted.")
            else:
                print("Submit button not found — check screenshot and submit manually.")
        else:
            print("--submit not passed. Review the screenshot, then re-run with --submit.")

        await browser.close()


def load_profile(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Fill job application forms automatically.")
    parser.add_argument("--url", required=True, help="Job application URL")
    parser.add_argument("--profile", required=True, help="Path to profile YAML file")
    parser.add_argument("--submit", action="store_true", help="Actually submit the form (default: fill only)")
    parser.add_argument("--screenshot", default="form_filled.png", help="Screenshot output path")
    args = parser.parse_args()

    profile = load_profile(args.profile)
    asyncio.run(run(args.url, profile, args.submit, args.screenshot))


if __name__ == "__main__":
    main()
