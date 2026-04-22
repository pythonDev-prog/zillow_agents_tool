import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# --- File Paths and Chrome Extension ---
# Default to the known path if the environment variable isn't set
_env_extension_path = os.getenv("EXTENSION_PATH")
EXTENSION_PATH = Path(_env_extension_path) if _env_extension_path else None

PROFILES_CSV = os.getenv("PROFILES_OUTPUT_CSV") or "zillow_agents_profiles.csv"
DETAILED_CSV = os.getenv("DETAILED_OUTPUT_CSV") or "zillow_agents_profiles_detailed.csv"

# --- UI Configuration ---
APP_TITLE = "Zillow Agent Scraper"
APP_GEOMETRY = "530x700"
APP_MIN_SIZE = (500, 700)

GUI_COLORS = {
    'primary': '#1f538d',
    'primary_hover': '#2563eb',
    'secondary': '#64748b',
    'success': '#10b981',
    'success_hover': '#059669',
    'danger': '#ef4444',
    'danger_hover': '#dc2626',
    'warning': '#f59e0b',
    'background': '#0f172a',
    'surface': '#1e293b',
    'surface_light': '#334155',
    'text_primary': '#f8fafc',
    'text_secondary': '#cbd5e1',
    'border': '#475569'
}

STATUS_COLORS = {
    "ready": GUI_COLORS['text_secondary'],
    "running": GUI_COLORS['primary'],
    "stopping": GUI_COLORS['warning'],
    "finished": GUI_COLORS['success'],
    "error": GUI_COLORS['danger']
}

# --- Scraping Configuration ---
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
PLAYWRIGHT_TIMEOUT_SHORT = 6000000
PLAYWRIGHT_TIMEOUT_LONG = 600000000
PLAYWRIGHT_TIMEOUT_EXTRA_LONG = 600000000  # Used when waiting for possible CAPTCHA logic

# CSV Output Ordering
COLUMN_ORDER = [
    'Zip Code', 'Agent Name', 'Sales 12mo', 'Total Sales', 
    'Rating', 'Reviews', 'Years of Experience', 'Price Range', 
    'Avg Price', 'License', 'Phone', 'Email', 'Address', 'Profile Link'
]
