import os
import sys
import time
import csv
import requests
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Replace all contoso references with your instance for Vivantio before running.
#
# -----------------------------------------------------------------------------
# 1) Configuration & Automatic Folder Creation
# -----------------------------------------------------------------------------

TARGET_DIR = r"C:\PythonScripts\VivantioScrape"
OUTPUT_DIR = os.path.join(TARGET_DIR, "VivantioKB")
CSV_FILENAME = "Articles.csv"  # e.g. at same location as the script

BASE_URL_TEMPLATE = "https://contoso.vivantio.com/#/Article/Details/{}"
LOGIN_TIMEOUT = 300
IFRAME_TIMEOUT = 30

def ensure_folder_structure():
    """
    Creates C:\PythonScripts\VivantioScrape\ and copies this script there if not already.
    Returns True if everything is OK, or False if user declined the move.
    """
    # 1) Check if we are already in the target directory
    current_script_path = os.path.abspath(sys.argv[0])
    current_script_dir = os.path.dirname(current_script_path)

    if os.path.normpath(current_script_dir) == os.path.normpath(TARGET_DIR):
        # We are already in C:\PythonScripts\VivantioScrape\
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR, exist_ok=True)
        return True
    else:
        # We are NOT in the target folder
        print(f"\nThe script is currently running from:\n{current_script_dir}")
        print(f"We recommend running from:\n{TARGET_DIR}")
        print("We can create the folder if it doesn't exist and copy this script over.\n")
        user_input = input("Continue and copy the script to the target folder? [Y/N] ").strip().lower()
        if user_input == "y":
            # 2) Create folder if needed
            os.makedirs(TARGET_DIR, exist_ok=True)

            # 3) Copy script
            target_script_path = os.path.join(TARGET_DIR, os.path.basename(current_script_path))
            shutil.copy2(current_script_path, target_script_path)
            print(f"Script copied to {target_script_path}")

            # 4) Prompt user to run again from the new location, or auto-run
            print("\nPlease run the script again from that folder, or press Enter to auto-run now.")
            choice = input("[R] to run from new location automatically, [X] to exit: ").strip().lower()
            if choice == "r":
                os.chdir(TARGET_DIR)
                # re-invoke python on the new path
                os.execl(sys.executable, sys.executable, target_script_path)
            else:
                print("Exiting. Please run the script manually from the new location.")
            return False
        else:
            print("Exiting. Please manually move the script if desired.")
            return False

# -----------------------------------------------------------------------------
# 2) Load Article IDs (and Titles) from CSV
# -----------------------------------------------------------------------------
def load_article_data(csv_filename=CSV_FILENAME):
    """
    Reads a CSV with columns 'ID' (and optional 'Title'),
    returns a dict mapping {article_id: article_title}.
    """
    data_map = {}
    csv_path = os.path.join(TARGET_DIR, csv_filename)
    if not os.path.isfile(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return data_map

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "ID" not in row or not row["ID"]:
                continue
            try:
                art_id = int(row["ID"])
            except ValueError:
                continue
            art_title = row.get("Title", f"Untitled {art_id}").strip()
            data_map[art_id] = art_title
    return data_map

# -----------------------------------------------------------------------------
# 3) Main Web Scraping Logic
# -----------------------------------------------------------------------------
def main():
    if not ensure_folder_structure():
        # If user declines or we couldn't auto-copy, exit
        return

    # At this point, we are in C:\PythonScripts\VivantioScrape\ (or user accepted the run)
    # 1) Create/ensure output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2) Load article data from CSV
    article_data_map = load_article_data()
    if not article_data_map:
        print("No valid articles found in CSV, or CSV is missing. Exiting.")
        return

    # 3) Set up Selenium
    driver = webdriver.Chrome()
    driver.get("https://contoso.vivantio.com/")
    print("\nPlease log in manually, including any MFA. Then navigate to the classic UI's Articles page. e.g https://contoso.vivantio.com/Article/Index/ ")

    try:
        WebDriverWait(driver, LOGIN_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "vivMainTabs"))
        )
        print("Login completed successfully. Proceeding to scrape articles...")
    except TimeoutException:
        print("Timeout while waiting for login. Exiting.")
        driver.quit()
        return

    # 4) Create a requests Session and copy Selenium cookies
    s = requests.Session()

    def update_requests_cookies_from_selenium():
        s.cookies.clear()
        selenium_cookies = driver.get_cookies()
        for cookie in selenium_cookies:
            s.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', None))

    # After login
    update_requests_cookies_from_selenium()

    # 5) Scrape each article
    for article_id, article_title in article_data_map.items():
        scrape_article(driver, s, article_id, article_title)

    driver.quit()
    print("\nAll done! Check the VivantioKB folder for results.")

# -----------------------------------------------------------------------------
# 4) The `scrape_article` function (similar to your existing logic)
# -----------------------------------------------------------------------------
def scrape_article(driver, requests_session, article_id, article_title):
    article_url = BASE_URL_TEMPLATE.format(article_id)
    print(f"\nNavigating to article {article_id}: {article_url}")
    driver.get(article_url)

    # Create dedicated folder for this article
    article_folder = os.path.join(OUTPUT_DIR, f"article_{article_id}")
    os.makedirs(article_folder, exist_ok=True)
    img_folder = os.path.join(article_folder, "img")
    os.makedirs(img_folder, exist_ok=True)

    html_path = os.path.join(article_folder, f"article_{article_id}.html")
    screenshot_path = os.path.join(article_folder, f"article_{article_id}.png")

    try:
        # Switch into main iframe
        WebDriverWait(driver, IFRAME_TIMEOUT).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "#mainFrame"))
        )
        print("Switched into mainFrame iframe.")

        # Switch into nested previewFrame
        preview_frame_selector = f"iframe[src*='/Article/PreviewFrame/{article_id}']"
        WebDriverWait(driver, IFRAME_TIMEOUT).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, preview_frame_selector))
        )
        print("Switched into nested article iframe.")
        time.sleep(5)  # small delay for dynamic content

        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        # Insert the article_title at the top
        body_tag = soup.find("body")
        if body_tag:
            title_tag = soup.new_tag("h1")
            title_tag.string = article_title
            body_tag.insert(0, title_tag)

        # Re-check cookies & download images
        update_requests_cookies_from_selenium = (
            lambda: requests_session.cookies.update({
                c['name']: c['value'] for c in driver.get_cookies()
            })
        )
        update_requests_cookies_from_selenium()

        img_tags = soup.find_all("img")
        for i, img_tag in enumerate(img_tags, start=1):
            src = img_tag.get("src")
            if not src:
                continue
            absolute_url = urljoin(driver.current_url, src)

            try:
                r = requests_session.get(absolute_url, timeout=15)
                r.raise_for_status()
                content_type = r.headers.get("Content-Type", "").lower()
                if "text/html" in content_type:
                    print(f"WARNING: The URL {absolute_url} returned HTML, not an image. Skipping.")
                    continue

                local_img_name = f"img_{i}.png"
                local_img_path = os.path.join(img_folder, local_img_name)
                with open(local_img_path, "wb") as f:
                    f.write(r.content)

                # Rewrite <img> src
                img_tag["src"] = f"img/{local_img_name}"

            except Exception as exc:
                print(f"Failed to download image from {absolute_url}: {exc}")

        # Write modified HTML
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

        # Screenshot
        driver.save_screenshot(screenshot_path)
        print(f"Saved HTML, images, and screenshot for article {article_id} in {article_folder}")

    except TimeoutException as e:
        print(f"Timed out while handling iframes/loading for article {article_id}. Error: {e}")
    except Exception as e:
        print(f"Error scraping article {article_id}: {e}")
    finally:
        # Switch back for next article
        driver.switch_to.default_content()

# -----------------------------------------------------------------------------
# 5) Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
