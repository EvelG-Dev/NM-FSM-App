import os
import uuid
from playwright.sync_api import Page, expect

STAGING_URL = os.environ.get("STAGING_URL", "http://localhost:5000").rstrip("/")
STUDENT_NAME = "E2E-" + uuid.uuid4().hex[:8]


def test_homepage_loads(page: Page):
    response = page.goto(STAGING_URL)
    assert response.status == 200
    assert page.title() != ""


def test_add_student_workflow(page: Page):
    page.goto(f"{STAGING_URL}/new")
    for field, value in dict(name=STUDENT_NAME, city="Miami", addr="123 Main St", pin="33101", phone="305-555-9999").items():
        page.fill(f"input[name='{field}']", value)
    page.click("button[type='submit']")
    page.wait_for_url(STAGING_URL + "/")


def test_student_appears_on_list(page: Page):
    page.goto(STAGING_URL)
    expect(page.locator("body")).to_contain_text(STUDENT_NAME)


def test_missing_name_stays_on_form(page: Page):
    page.goto(f"{STAGING_URL}/new")
    page.fill("input[name='city']", "Miami")
    page.fill("input[name='addr']", "1 Main St")
    page.fill("input[name='phone']", "305-555-0000")
    page.click("button[type='submit']")
    assert "/new" in page.url
