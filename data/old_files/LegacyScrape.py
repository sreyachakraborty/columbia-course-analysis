'''
Initially, I used selenium to practice scraping professor reviews.
This was because the only tool I knew before was BeautifulSoup, which I tried
but it doesn't allow for dynamically interacting with the JavaScript
since there was a load more button. Initially I found that selenium allows you 
to directly interact with JS components like the load more.
However this was very slow so I switching to interacting with the 
CULPA API requests directly to parse them which is must faster in faster_scrape.py
'''

import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://www.culpa.info/course/7468"

def scrape_culpa():
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(URL)
    time.sleep(2)

    # Keep clicking "Load More"
    while True:
        try:
            load_more = driver.find_element(By.XPATH, "//button[contains(text(),'Load More')]")
            driver.execute_script("arguments[0].click();", load_more)
            time.sleep(1.2)
        except:
            break

    # Get all review cards
    review_cards = driver.find_elements(By.CSS_SELECTOR, ".ui.fluid.card")

    # Skip the first card (professor header)
    review_cards = review_cards[1:]

    data = []
    for card in review_cards:
        try:
            course_tag = card.find_element(By.CSS_SELECTOR, ".header a")
            course = course_tag.text.strip()
        except:
            course = None

        try:
            date_tag = card.find_elements(By.CSS_SELECTOR, ".header")[1]
            date = date_tag.text.strip()
        except:
            date = None

        try:
            text_tag = card.find_element(By.CSS_SELECTOR, ".description")
            text = text_tag.text.strip()
        except:
            text = None

        data.append({
            "course": course,
            "date": date,
            "text": text
        })

    driver.quit()

    # Save JSON locally
    with open("jae_reviews.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"Saved {len(data)} reviews to reviews.json")


if __name__ == "__main__":
    scrape_culpa()
