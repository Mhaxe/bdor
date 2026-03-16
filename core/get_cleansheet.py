import asyncio
from playwright.async_api import async_playwright

async def download_csv():
    url = [
        #"https://www.accaplanner.com/league/france-ligue-1/clean-sheets/",
        "https://www.accaplanner.com/league/english-premier-league/clean-sheets/",
        "https://www.accaplanner.com/league/germany-bundesliga/clean-sheets/",
        "https://www.accaplanner.com/league/italy-serie-a/clean-sheets/",
        "https://www.accaplanner.com/league/spain-la-liga/clean-sheets/"
           ]
    i = 1
    for url in url:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()

            # Go to the page
            await page.goto(url)

            # Start waiting for the download event
            async with page.expect_download() as download_info:
                # Click the CSV button
                await page.click(".buttons-csv")   # the class you showed
            download = await download_info.value

            # Save the CSV file locally
            save_path = f"{i}.csv"
            await download.save_as(save_path)

            print(f"CSV saved as: {save_path}")

            i = i + 1

            await browser.close()

asyncio.run(download_csv())
