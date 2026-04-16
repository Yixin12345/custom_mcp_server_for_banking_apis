"""Playwright script to log into the XYZ Bank demo and deposit $200."""

from __future__ import annotations

import os
from dataclasses import dataclass

from playwright.sync_api import Page, expect, sync_playwright

BASE_URL = "https://www.globalsqa.com/angularJs-protractor/BankingProject/"
PERSON_NAME = "Hermoine Granger"
DEPOSIT_AMOUNT = 200


@dataclass(slots=True)
class DepositResult:
    # person_name: str
    # account_number: str
    starting_balance: int
    ending_balance: int
    deposited_amount: int


def parse_balance(page: Page) -> int:
    balance_text = page.locator("div.center strong").nth(1).inner_text().strip()
    return int(balance_text)


def choose_person(page: Page, person_name: str = "Hermoine Granger") -> None:
    person_dropdown = page.locator("#userSelect")
    person_dropdown.wait_for(state="visible")

    options = [
        option.strip()
        for option in person_dropdown.locator("option").all_inner_texts()
        if option.strip() and not option.strip().startswith("---")
    ]
    if not options:
        raise RuntimeError("No person options were available in the login dropdown.")

    # if person_name not in options:
    #     raise RuntimeError(f"Person '{person_name}' was not available in the login dropdown.")

    person_dropdown.select_option(label=person_name)


def deposit_money(page: Page, amount: int) -> DepositResult:
    print("Step: opening XYZ Bank page", flush=True)
    page.goto(BASE_URL, wait_until="domcontentloaded")

    print("Step: logging in as customer", flush=True)
    page.get_by_role("button", name="Customer Login").click()
    choose_person(page, PERSON_NAME)
    page.get_by_role("button", name="Login").click()

    expect(page.get_by_role("button", name="Deposit")).to_be_visible()

    # account_number = page.locator("div.center strong").first.inner_text().strip()
    starting_balance = parse_balance(page)

    print("Step: submitting deposit", flush=True)
    page.get_by_role("button", name="Deposit").click()
    amount_input = page.locator("input[ng-model='amount']")
    expect(amount_input).to_be_visible()
    amount_input.fill(str(amount))
    page.get_by_role("form").get_by_role("button", name="Deposit").click()

    success_message = page.locator("span.error")
    expect(success_message).to_have_text("Deposit Successful")
    expect(page.locator("div.center strong").nth(1)).to_have_text(str(starting_balance + amount))

    ending_balance = parse_balance(page)
    return DepositResult(
        # person_name=person_name,
        # account_number=account_number,
        starting_balance=starting_balance,
        ending_balance=ending_balance,
        deposited_amount=amount,
    )


def main() -> None:
    headless = os.getenv("HEADLESS", "true").lower() == "true"
    print(f"Mode: {'headless' if headless else 'headed'}", flush=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=headless,
            slow_mo=250 if not headless else 0,
        )
        page = browser.new_page()
        try:
            result = deposit_money(page, DEPOSIT_AMOUNT)
            # print(f"Person: {result.person_name}")
            # print(f"Account number: {result.account_number}")
            print(f"Starting balance: {result.starting_balance}", flush=True)
            print(f"Deposited: {result.deposited_amount}", flush=True)
            print(f"Ending balance: {result.ending_balance}", flush=True)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
