import random
import time
import os
import threading
import pandas as pd
from typing import List, Callable
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from config import (
    EXTENSION_PATH, USER_AGENT, 
    PLAYWRIGHT_TIMEOUT_SHORT, PLAYWRIGHT_TIMEOUT_LONG, PLAYWRIGHT_TIMEOUT_EXTRA_LONG,
    COLUMN_ORDER
)
from parsers import extract_agent_details

class ZillowScraper:
    """Core logic for scraping Zillow agents."""

    def __init__(self, zip_codes: List[str], num_pages: int, is_headless: bool, 
                 logger: Callable[[str], None], stop_event: threading.Event):
        self.zip_codes = zip_codes
        self.num_pages = num_pages
        self.is_headless = is_headless
        self.logger = logger
        self.stop_event = stop_event

    def run(self, profiles_csv: str, detailed_csv: str, on_complete_callback: Callable[[str], None], app_instance) -> None:
        """Main execution flow for scraping."""
        final_status = "Stopped"
        try:
            success = self._scrape_profiles(profiles_csv)
            
            if self.stop_event.is_set():
                app_instance.after(0, on_complete_callback, "Stopped")
                return

            if success and os.path.exists(profiles_csv):
                self._scrape_details(profiles_csv, detailed_csv)
            elif not success:
                self.logger("Profile scraping failed. Aborting detailed scraping.")
            else:
                self.logger(f"Could not find '{profiles_csv}' after scraping. Aborting detailed scraping.")

            final_status = "Finished" if not self.stop_event.is_set() else "Stopped"

        except Exception as e:
            self.logger(f"CRITICAL ERROR in scraper runner: {e}")
            final_status = "Error"
        finally:
            app_instance.after(0, on_complete_callback, final_status)

    def _scrape_profiles(self, output_path: str) -> bool:
        all_data = []
        self.logger("--- STEP 1: Starting Agent Profile Scraping ---")
        
        try:
            with sync_playwright() as p:
                args = [
                    '--disable-blink-features=AutomationControlled', 
                    '--disable-dev-shm-usage',
                ]
                
                # Only load the extension if the path exists
                if EXTENSION_PATH is not None and EXTENSION_PATH.exists() and EXTENSION_PATH.is_dir():
                    args.append(f"--disable-extensions-except={EXTENSION_PATH.resolve()}")
                    args.append(f"--load-extension={EXTENSION_PATH.resolve()}")
                else:
                    self.logger("⚠️ WARNING: NopeCHA extension path is invalid or missing.")

                browser = p.chromium.launch_persistent_context(
                    user_data_dir='new_profile', 
                    headless=self.is_headless,
                    args=args,
                    user_agent=USER_AGENT,
                    ignore_https_errors=True
                )
                
                for zip_code in self.zip_codes:
                    if self.stop_event.is_set():
                        self.logger("Stop signal received. Halting profile scraping.")
                        break
                        
                    self.logger(f"\n▶ Processing zip code: {zip_code}")
                    page = browser.new_page()
                    
                    try:
                        page.set_extra_http_headers({'Accept-Language': 'en-US,en;q=0.9', 'Referer': 'https://www.google.com/'})
                        url = f'https://www.zillow.com/professionals/real-estate-agent-reviews/{zip_code}/'
                        page.goto(url, timeout=PLAYWRIGHT_TIMEOUT_EXTRA_LONG, wait_until='domcontentloaded')
                        page.wait_for_selector('div.MediaObject__Body-sc-12gs3hz-2', timeout=PLAYWRIGHT_TIMEOUT_SHORT)
                        
                        base_url = page.url.split('?')[0]
                        
                        for current_page_num in range(1, self.num_pages + 1):
                            if self.stop_event.is_set(): 
                                break
                            
                            if current_page_num > 1:
                                page.goto(f"{base_url}?page={current_page_num}", timeout=PLAYWRIGHT_TIMEOUT_LONG, wait_until='domcontentloaded')
                                
                            time.sleep(random.uniform(1.5, 3))
                            
                            try:
                                page.wait_for_selector('div.MediaObject__Body-sc-12gs3hz-2', timeout=15000)
                            except Exception:
                                self.logger(f"ⓘ No more agents found on page {current_page_num} for {zip_code}. Moving to next zip.")
                                break
                                
                            soup = BeautifulSoup(page.content(), 'html.parser')
                            agent_cards = soup.select('.eZTHwg')
                            
                            for card in agent_cards:
                                # Updated selector based on user preference
                                name_element = card.select_one('.hbZTEb')
                                name = name_element.get_text(strip=True) if name_element else 'N/A'
                                link = card.get('href', '') if card.name == 'a' else card.find('a', href=True).get('href', '')
                                all_data.append({'Zip Code': zip_code, 'Agent Name': name, 'Profile Link': link})
                                
                            self.logger(f"  Scraped {len(agent_cards)} agents from page {current_page_num} of {zip_code}")
                            
                    except Exception as e:
                        self.logger(f"❌ ERROR processing {zip_code}: {e}")
                    finally:
                        page.close()
                        
                browser.close()
                
            if all_data:
                df = pd.DataFrame(all_data)
                df.to_csv(output_path, index=False)
                self.logger(f"\n✔ Profile scraping complete. Data saved to {output_path}")
                return True
                
            self.logger("\nⓘ No agents found. No profile data saved.")
            return False
            
        except Exception as e:
            self.logger(f"❌ A critical error occurred during profile scraping: {e}")
            return False

    def _scrape_details(self, csv_path: str, output_path: str) -> None:
        self.logger("\n--- STEP 2: Starting Detailed Agent Scraping ---")
        df_input = pd.read_csv(csv_path)
        scraped_data_list = []
        
        try:
            with sync_playwright() as p:
                args = ['--disable-blink-features=AutomationControlled']
                if EXTENSION_PATH is not None and EXTENSION_PATH.exists() and EXTENSION_PATH.is_dir():
                    args.append(f"--disable-extensions-except={EXTENSION_PATH.resolve()}")
                    args.append(f"--load-extension={EXTENSION_PATH.resolve()}")

                browser = p.chromium.launch_persistent_context(
                    user_data_dir='new_profile', 
                    headless=self.is_headless,
                    args=args
                )
                page = browser.new_page()
                
                for index, row in df_input.iterrows():
                    if self.stop_event.is_set(): 
                        self.logger("Stop signal received. Halting detailed scraping.")
                        break
                        
                    profile_url = row.get('Profile Link')
                    agent_name = row.get('Agent Name', 'N/A')
                    zip_code = row.get('Zip Code', '')
                    
                    if not profile_url or pd.isna(profile_url) or not str(profile_url).startswith('http'):
                        self.logger(f"Skipping row {index+2}: Invalid URL -> {profile_url}")
                        continue
                        
                    self.logger(f"\n▶ Processing agent {index+1}/{len(df_input)}: {agent_name}")
                    try:
                        page.goto(profile_url, timeout=PLAYWRIGHT_TIMEOUT_LONG, wait_until='domcontentloaded')
                        details = extract_agent_details(page, self.logger)
                        time.sleep(2)

                        result_row = {'Zip Code': zip_code, 'Agent Name': agent_name, 'Profile Link': profile_url, **details}
                        scraped_data_list.append(result_row)
                        
                        # Save progress every 10 agents
                        if (index + 1) % 10 == 0 and scraped_data_list:
                            temp_df = pd.DataFrame(scraped_data_list).reindex(columns=COLUMN_ORDER)
                            temp_df.to_csv(output_path, index=False)
                            self.logger(f"  💾 Saved progress for {len(scraped_data_list)} agents to {output_path}")
                            
                        time.sleep(random.uniform(2.0, 4.0))
                    except Exception as e:
                        self.logger(f"  ❌ Error processing agent {agent_name}: {e}")
                        
                browser.close()
                
            if scraped_data_list:
                final_df = pd.DataFrame(scraped_data_list).reindex(columns=COLUMN_ORDER)
                final_df.to_csv(output_path, index=False)
                self.logger(f"\n✔ Detailed scraping complete! Final results saved to {output_path}")
                
        except Exception as e:
            self.logger(f"❌ A critical error occurred during detailed scraping: {e}")
