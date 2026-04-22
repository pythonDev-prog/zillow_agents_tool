# Zillow Agent Scraper 🏠

A professional, multi-threaded Desktop Application built with Python, CustomTkinter, and Playwright for scraping comprehensive real estate agent data from Zillow.

## Features

- **Modern GUI**: Clean, dark-themed dashboard using CustomTkinter.
- **Two-Phase Scraping**:
  1. Gathers basic profiles (names and profile links) by Zip Code.
  2. Deep dives into each profile to extract detailed performance metrics, contact info, and licensing data.
- **CAPTCHA Bypassing**: Integrated with the NopeCHA extension to automate invisible bot challenges.
- **Non-blocking UI**: Uses Python threading to ensure the interface remains responsive during long scraping tasks.
- **Headless Mode Toggle**: Option to view exactly what the browser is doing or hide it in the background.

## Installation

### 1. Requirements

Ensure you have Python 3.10+ installed. Clone this repository and install the dependencies:

```bash
git clone https://github.com/yourusername/zillow_agent_scraper.git
cd zillow_agent_scraper

# Install Python packages
pip install -r requirements.txt

# Install Playwright Chromium browser
playwright install chromium
```

### 2. Setup the NopeCHA Extension

Because Zillow employs robust anti-bot measures, this scraper uses the NopeCHA extension to run seamlessly.

1. Download the latest extension release from here: [NopeCHA Extension Releases](https://github.com/NopeCHALLC/nopecha-extension/releases)
2. Extract the downloaded `.zip` file into a folder on your computer.

### 3. Environment Configuration

For the scraper to find your downloaded extension, you must set an environment variable:

1. Copy the `.env.example` file and rename the copy to `.env`.
2. Open `.env` and update the `EXTENSION_PATH` variable to point identically to the folder where you extracted the NopeCHA extension above.

```env
# Example .env file mapping
EXTENSION_PATH=C:\path\to\your\extracted\nopecha-extension
```

## Usage

Start the application by running the main python script:

```bash
python main.py
```

### Scraping Parameters

- **Target Zip Codes**: Provide a comma-separated list of Zip Codes (e.g., `90210, 33139`).
- **Pages per Zip**: Define how deep in the search results you want to traverse (10, 20, 25, or All).
- **Run in background**: Check this box if you don't want the Chrome browser to be visible.

## Output

The scraper continuously saves its progress and outputs two files (which you can rename in your `.env` file):

**1. `zillow_agents_profiles.csv`**
Basic directory scrape containing:

- Zip Code
- Agent Name
- Profile Link

**2. `zillow_agents_profiles_detailed.csv`**
The final dataset loaded with metrics, ratings, and phone numbers. You will receive exactly the following fields:

- `Zip Code`
- `Agent Name`
- `Sales 12mo` (Number of sales in the last year)
- `Total Sales` (All-time recorded sales)
- `Rating` (Out of 5)
- `Reviews` (Total number of reviews)
- `Years of Experience`
- `Price Range` (e.g., $300k - $900k)
- `Avg Price`
- `License` (License Number & Issuer)
- `Phone`
- `Email`
- `Address`
- `Profile Link`
