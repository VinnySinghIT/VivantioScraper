# Vivantio Knowledge Base Scraper

Vivantio, an ITSM platform makes it difficult to export your knowledgebase articles, especially with inline pictures. This python script aims to solve that problem.

**VivantioScrape** is a Python script that logs in to your **classic Vivantio** instance (non-Flex UI) via Chrome/Selenium, navigates to each article, and saves:
- **HTML** of the article (including images),  
- **Screenshots** of each article,  
- **Folder structure** neatly organized by article ID.

## 1. Requirements

Windows only but script could be modified for other operating systems.

1. **Python 3.x**  
   - [Download](https://www.python.org/downloads/) and install (check “Add Python to PATH” on Windows).

2. **Google Chrome** and **ChromeDriver**  
   - [ChromeDriver](https://chromedriver.chromium.org/downloads) must match your Chrome version.  
   - Ensure `chromedriver.exe` is on your system PATH or in the same directory as the script.

3. **Python Libraries**  
   ```bash
   pip install selenium requests beautifulsoup4
   ```

## 2. Setup

1. **Clone or download** this repository.  
2. **Edit** `scrape_vivantio.py`:
   - Replace all instances of `contoso.vivantio.com` with **your** Vivantio subdomain (e.g., `mycompany.vivantio.com`).
   - (Optional) Adjust timeouts or folder paths if needed.
3. **Disable Flex (New UI)** in Vivantio:
   - Go to **Settings → Preferences** → **Default to FLEX** = **Off**  
   - The script only works with the classic UI.

4. **Export Articles** from Vivantio:
   - In the classic Articles list, use **Export Results**.  
   - Rename the downloaded file to `Articles.csv` (place it in the same folder as `scrape_vivantio.py`).

## 3. Running the Script

1. **Open a terminal** (Command Prompt or PowerShell on Windows).  
2. **Navigate** to the script’s directory:
   ```bash
   cd path\to\VivantioScrape
   ```
3. **Run**:
   ```bash
   python scrape_vivantio.py
   ```
4. **Manual Login & Articles Page**  
   - A Chrome window will appear.  
   - Log in to Vivantio (with MFA as needed).  
   - Make sure you’re in the classic UI (no `flex` in the URL).  
   - Once the script detects you’re logged in, and gone to https://contoso.vivantio.com/Article/Index/, it will begin scraping each article listed in `Articles.csv`.

## 4. Output

By default, the script creates a folder structure like:

```
VivantioKB/
  ├─ article_397/
  │    ├─ article_397.html
  │    ├─ article_397.png
  │    └─ img/
  │         └─ img_1.png
  ├─ article_398/
  └─ ...
```

- **`article_###.html`**: The full article, with `<img>` paths rewritten to local `img/` subfolder.  
- **`article_###.png`**: A screenshot of that article’s iframe.  
- **`img/`** subfolder: Contains all downloaded images for that article.

## 5. Notes & Performance

Script & CSV: C:\PythonScripts\VivantioScrape\scrape_vivantio.py and Articles.csv

Output Root: C:\PythonScripts\VivantioScrape\VivantioKB

HTML & Screenshots: VivantioKB\article_{ID}\article_{ID}.html (and article_{ID}.png)

Images: VivantioKB\article_{ID}\img\img_X.png

Once the script finishes, you’ll find one folder per article with the HTML, a screenshot, and an img\ subfolder for any inline images.

- **Time**: Scraping ~500 articles can take about 1 hour, depending on your connection speed and Vivantio’s page load times.  
- **Stability**: If Flex is not fully disabled or if your session expires mid-run, you may see timeouts. Just re-run the script and ensure you’re in the classic UI.  
- **Cookies & Authentication**: The script uses Selenium cookies to download images with `requests`. If any images are still HTML after download, verify your subdomain and login session.  

---

That’s it!  
- **Any issues?** Check your Python, ChromeDriver versions, and that Flex is disabled.  
- **Need custom changes?** Adjust the script’s timeouts or folder paths as needed.  
