import customtkinter as ctk
import threading
import pandas as pd
from playwright.sync_api import sync_playwright
import time
import random
import re
from bs4 import BeautifulSoup
import os
import queue
from pathlib import Path

EXTENSION_PATH = Path(r"E:\zillow_agents_tool\nopecha-extensionC")
# --- PROFESSIONAL GUI APPLICATION ---

class ScraperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("Zillow Agent Scraper")
        # MODIFIED: Further reduced initial height for a more compact view
        self.geometry("530x700")
        self.resizable(True, True)
        # MODIFIED: Reduced the minimum height
        self.minsize(500, 700)

        # --- Professional Theme ---
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- Custom Colors (Unchanged) ---
        self.colors = {
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

        # --- Threading Control ---
        self.scraper_thread = None
        self.stop_event = threading.Event()

        # --- GUI Data Queue ---
        self.log_queue = queue.Queue()

        # --- Build the UI ---
        self.create_widgets()

        # --- Center window after creation ---
        self.after(100, self.center_window)
        self.after(100, self.process_log_queue)

    def create_widgets(self):
        # Configure main grid - Row 3 (Activity Monitor) will expand vertically
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # --- Header Section ---
        header_frame = ctk.CTkFrame(self, fg_color=self.colors['surface'], corner_radius=15)
        header_frame.grid(row=0, column=0, padx=25, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame, text="🏠 Zillow Agent Scraper",
            font=ctk.CTkFont(size=28, weight="bold"), text_color=self.colors['text_primary']
        )
        title_label.grid(row=0, column=0, padx=30, pady=(20, 5))

        subtitle_label = ctk.CTkLabel(
            header_frame, text="Professional Real Estate Agent Data Collection Tool",
            font=ctk.CTkFont(size=14), text_color=self.colors['text_secondary']
        )
        subtitle_label.grid(row=1, column=0, padx=30, pady=(0, 20))

        # --- Configuration Section ---
        config_frame = ctk.CTkFrame(self, fg_color=self.colors['surface'], corner_radius=15)
        config_frame.grid(row=1, column=0, padx=25, pady=5, sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)

        # config_title = ctk.CTkLabel(
        #     config_frame, text="⚙️ Configuration",
        #     font=ctk.CTkFont(size=18, weight="bold"), text_color=self.colors['text_primary']
        # )
        # config_title.grid(row=0, column=0, columnspan=2, padx=25, pady=(15, 10), sticky="w")

        zip_label = ctk.CTkLabel(
            config_frame, text="Target Zip Codes:",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_primary']
        )
        zip_label.grid(row=1, column=0, padx=(25, 15), pady=8, sticky="w")

        self.zips_entry = ctk.CTkEntry(
            config_frame, placeholder_text="e.g., 90210, 10001, 33139",
            font=ctk.CTkFont(size=13), height=40, corner_radius=8,
            border_width=2, border_color=self.colors['border']
        )
        self.zips_entry.grid(row=1, column=1, padx=(0, 25), pady=8, sticky="ew")

        pages_label = ctk.CTkLabel(
            config_frame, text="Pages per Zip Code:",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_primary']
        )
        pages_label.grid(row=2, column=0, padx=(25, 15), pady=8, sticky="w")

        self.pages_option_menu = ctk.CTkOptionMenu(
            config_frame, values=["10", "20", "25", "All"],
            font=ctk.CTkFont(size=13), height=40, corner_radius=8,
            button_color=self.colors['primary'], button_hover_color=self.colors['primary_hover']
        )
        self.pages_option_menu.grid(row=2, column=1, padx=(0, 25), pady=8, sticky="w")
        self.pages_option_menu.set("10")

        self.headless_var = ctk.StringVar(value="off")
        self.headless_checkbox = ctk.CTkCheckBox(
            config_frame, text="Run browser in background (headless mode)",
            variable=self.headless_var, onvalue="on", offvalue="off", font=ctk.CTkFont(size=13),
            checkbox_width=20, checkbox_height=20, corner_radius=4, border_width=2
        )
        self.headless_checkbox.grid(row=3, column=0, columnspan=2, padx=25, pady=(8, 15), sticky="w")

        # --- Control Buttons Section ---
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=25, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.start_button = ctk.CTkButton(
            button_frame, text="🚀 Start Scraping", command=self.start_scraping, height=50,
            font=ctk.CTkFont(size=16, weight="bold"), corner_radius=12,
            fg_color=self.colors['success'], hover_color=self.colors['success_hover']
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.stop_button = ctk.CTkButton(
            button_frame, text="⏹️ Stop Scraping", command=self.stop_scraping, height=50,
            font=ctk.CTkFont(size=16, weight="bold"), corner_radius=12, state="disabled",
            fg_color=self.colors['danger'], hover_color=self.colors['danger_hover']
        )
        self.stop_button.grid(row=0, column=1, padx=(10, 0), sticky="ew")

        # --- Status and Progress Section ---
        status_frame = ctk.CTkFrame(self, fg_color=self.colors['surface'], corner_radius=15)
        status_frame.grid(row=3, column=0, padx=25, pady=(5, 0), sticky="nsew")
        # MODIFIED: Change expanding row to 2 (log container)
        status_frame.grid_rowconfigure(2, weight=1)
        status_frame.grid_columnconfigure(0, weight=1)

        # MODIFIED: Create a new frame for the monitor header line
        monitor_header_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        monitor_header_frame.grid(row=0, column=0, padx=25, pady=(15, 10), sticky="ew")

        # MODIFIED: Place title inside the new frame
        status_title = ctk.CTkLabel(
            monitor_header_frame,
            text="📊 Activity Monitor:",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors['text_primary']
        )
        status_title.grid(row=0, column=0, sticky="w")

        # MODIFIED: Place status label inside the new frame, next to the title
        self.status_label = ctk.CTkLabel(
            monitor_header_frame,
            text="Ready to begin scraping",
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_secondary'],
            anchor="w"
        )
        self.status_label.grid(row=0, column=1, padx=(10, 0), sticky="w")

        # MODIFIED: Move progress bar to row 1
        self.progress_bar = ctk.CTkProgressBar(
            status_frame,
            height=8,
            corner_radius=4,
            progress_color=self.colors['primary']
        )
        self.progress_bar.grid(row=1, column=0, padx=25, pady=(0, 15), sticky="ew")
        self.progress_bar.set(0)

        # MODIFIED: Move log container to row 2
        log_container = ctk.CTkFrame(status_frame, fg_color=self.colors['background'], corner_radius=10)
        log_container.grid(row=2, column=0, padx=25, pady=(0, 20), sticky="nsew")
        log_container.grid_rowconfigure(0, weight=1)
        log_container.grid_columnconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(
            log_container,
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            corner_radius=8,
            fg_color=self.colors['background'],
            text_color=self.colors['text_primary'],
            scrollbar_button_color=self.colors['surface'],
            scrollbar_button_hover_color=self.colors['surface_light']
        )
        self.log_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # --- Footer ---
        footer_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
        footer_frame.grid(row=4, column=0, padx=25, pady=(5, 15), sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=1)

        footer_label = ctk.CTkLabel(
            footer_frame,
            text="© 2025 Zillow Scraper",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['text_secondary']
        )
        footer_label.grid(row=0, column=0)

    def log(self, message):
        self.log_queue.put(message)

    def process_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get_nowait()
            self.log_textbox.configure(state="normal")
            timestamp = time.strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            self.log_textbox.insert("end", formatted_message + "\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        self.after(100, self.process_log_queue)

    def start_scraping(self):
        zips_str = self.zips_entry.get().strip()
        if not zips_str or "e.g." in zips_str:
            self.log("❌ ERROR: Please enter valid zip codes.")
            self.update_status("Error: Invalid zip codes", "error")
            return

        self.stop_event.clear()
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.update_status("Initializing scraper...", "running")
        self.progress_bar.start()

        pages_selection = self.pages_option_menu.get()
        num_pages = 9999 if pages_selection == "All" else int(pages_selection)
        zip_codes = [z.strip() for z in zips_str.split(',') if z.strip()]
        is_headless = self.headless_var.get() == "on"

        self.log("🚀 Starting scraping session")
        self.log(f"📍 Target zip codes: {', '.join(zip_codes)}")
        self.log(f"📄 Pages per zip: {pages_selection}")
        self.log(f"🔇 Headless mode: {'Enabled' if is_headless else 'Disabled'}")
        self.log("─" * 50)

        self.scraper_thread = threading.Thread(
            target=run_full_scraper,
            # MODIFIED: Pass the app instance 'self' for a more robust callback
            args=(zip_codes, num_pages, is_headless, self.log, self.stop_event, self.on_scraping_complete, self)
        )
        self.scraper_thread.daemon = True
        self.scraper_thread.start()

    def stop_scraping(self):
        self.log("🛑 STOP command issued. Finishing current task and saving progress...")
        self.update_status("Stopping scraper...", "stopping")
        self.stop_button.configure(state="disabled")
        self.stop_event.set()

    def update_status(self, message, status_type="info"):
        """Update status with color coding"""
        colors = {
            "ready": self.colors['text_secondary'],
            "running": self.colors['primary'],
            "stopping": self.colors['warning'],
            "finished": self.colors['success'],
            "error": self.colors['danger']
        }
        
        color = colors.get(status_type, self.colors['text_secondary'])
        # MODIFIED: Removed the "Status: " prefix from the text
        self.status_label.configure(text=message, text_color=color)

    def on_scraping_complete(self, final_status):
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.progress_bar.stop()
        
        if final_status == "Finished":
            self.progress_bar.set(1)
            self.update_status("Scraping completed successfully", "finished")
            self.log("✅ All tasks completed successfully!")
        elif final_status == "Stopped":
            self.progress_bar.set(0)
            self.update_status("Scraping stopped by user", "stopping")
            self.log("⏹️ Scraping stopped by user request")
        else:
            self.progress_bar.set(0)
            self.update_status("Scraping failed with errors", "error")
            self.log("❌ Scraping encountered errors")
        
        self.log("─" * 50)
        self.log(f">>> Session {final_status.lower()}. <<<")

    def center_window(self):
        self.update_idletasks()
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        width, height = self.winfo_width(), self.winfo_height()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

# --- SCRAPER BACKEND (Logic preserved, callback mechanism improved) ---

# MODIFIED: Added 'app_instance' parameter for robust callbacks
def run_full_scraper(zip_codes, num_pages, is_headless, logger, stop_event, on_complete_callback, app_instance):
    final_status = "Stopped"
    try:
        profiles_csv = 'zillow_agents_profilestest.csv'
        detailed_csv = 'zillow_agents_profiles_detailed.csv'
        
        success = scrape_agents_task(zip_codes, num_pages, is_headless, profiles_csv, logger, stop_event)
        
        if stop_event.is_set():
            # MODIFIED: Use app_instance for thread-safe UI updates
            app_instance.after(0, on_complete_callback, "Stopped")
            return

        if success and os.path.exists(profiles_csv):
            scrape_agent_details_task(profiles_csv, detailed_csv, is_headless, logger, stop_event)
        elif not success:
            logger("Profile scraping failed. Aborting detailed scraping.")
        else:
            logger(f"Could not find '{profiles_csv}' after scraping. Aborting detailed scraping.")

        final_status = "Finished" if not stop_event.is_set() else "Stopped"

    except Exception as e:
        logger(f"CRITICAL ERROR in scraper runner: {e}")
        final_status = "Error"
    finally:
        # MODIFIED: Use app_instance for thread-safe UI updates
        app_instance.after(0, on_complete_callback, final_status)

# --- (The rest of the backend code is unchanged as it contains the core logic) ---
def scrape_agents_task(zip_codes, num_pages, is_headless, output_path, logger, stop_event):
    all_data = []
    logger("--- STEP 1: Starting Agent Profile Scraping ---")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir='new_profile', headless=is_headless,
                args=[
                    '--disable-blink-features=AutomationControlled', 
                    '--disable-dev-shm-usage',
                    f"--disable-extensions-except={EXTENSION_PATH.resolve()}",
                    f"--load-extension={EXTENSION_PATH.resolve()}",

                ],
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                ignore_https_errors=True
            )
            for zip_code in zip_codes:
                if stop_event.is_set():
                    logger("Stop signal received. Halting profile scraping."); break
                logger(f"\n▶ Processing zip code: {zip_code}")
                page = browser.new_page()
                try:
                    page.set_extra_http_headers({'Accept-Language': 'en-US,en;q=0.9', 'Referer': 'https://www.google.com/'})
                    page.goto(f'https://www.zillow.com/professionals/real-estate-agent-reviews/{zip_code}/', timeout=600000000, wait_until='domcontentloaded')
                    # page.goto(f'https://www.zillow.com/professionals/real-estate-agent-reviews/34756/', timeout=600000000, wait_until='domcontentloaded')
                    page.wait_for_selector('div.MediaObject__Body-sc-12gs3hz-2', timeout=200000000)
                    base_url = page.url.split('?')[0]
                    for current_page_num in range(1, num_pages + 1):
                        if stop_event.is_set(): break
                        if current_page_num > 1:
                            page.goto(f"{base_url}?page={current_page_num}", timeout=60000, wait_until='domcontentloaded')
                        time.sleep(random.uniform(1.5, 3))
                        try:
                            page.wait_for_selector('div.MediaObject__Body-sc-12gs3hz-2', timeout=15000)
                        except Exception:
                            logger(f"ⓘ No more agents found on page {current_page_num} for {zip_code}. Moving to next zip."); break
                        soup = BeautifulSoup(page.content(), 'html.parser')
                        agent_cards = soup.select('.eZTHwg')
                        for card in agent_cards:
                            name_element = card.select_one('.hbZTEb')
                            name = name_element.get_text(strip=True) if name_element else 'N/A'
                            link = card.get('href', '') if card.name == 'a' else card.find('a', href=True).get('href', '')
                            all_data.append({'Zip Code': zip_code, 'Agent Name': name, 'Profile Link': link})
                        logger(f"  Scraped {len(agent_cards)} agents from page {current_page_num} of {zip_code}")
                except Exception as e:
                    logger(f"❌ ERROR processing {zip_code}: {e}")
                finally:
                    page.close()
            browser.close()
        if all_data:
            df = pd.DataFrame(all_data); df.to_csv(output_path, index=False)
            logger(f"\n✔ Profile scraping complete. Data saved to {output_path}")
            return True
        logger("\nⓘ No agents found. No profile data saved.")
        return False
    except Exception as e:
        logger(f"❌ A critical error occurred during profile scraping: {e}")
        return False

def scrape_agent_details_task(csv_path, output_path, is_headless, logger, stop_event):
    def extract_license_info(page, logger):
        try:
            license_button = page.locator(".cJVBTO button").first
            if not license_button.is_visible(): return ""
            license_button.click()
            dialog_body_selector = "div.DialogBody-c11n-8-107-0__sc-1l4a94i-0"
            page.wait_for_selector(dialog_body_selector, timeout=5000)
            license_cards = page.query_selector_all(f"{dialog_body_selector} .StyledCard-c11n-8-107-0__sc-1w6p0lv-0")
            all_licenses = []
            for card in license_cards:
                texts = [span.get_text(strip=True) for span in BeautifulSoup(card.inner_html(), 'html.parser').select('.Grid-c11n-8-107-0__sc-18zzowe-0 span')]
                license_num, issuer = "", ""
                try: license_num = texts[texts.index('License #:') + 1]
                except (ValueError, IndexError): pass
                try: issuer = texts[texts.index('Issued by:') + 1]
                except (ValueError, IndexError): pass
                if license_num: all_licenses.append(f"{license_num} ({issuer})")
            close_button = page.query_selector('section[role="dialog"] button:has-text("Close")')
            if close_button: close_button.click(); page.wait_for_selector('section[role="dialog"]', state='hidden', timeout=3000)
            return "; ".join(all_licenses) if all_licenses else ""
        except Exception as e:
            logger(f"    ⓘ License extraction notice: {e}"); return ""
    def extract_contact_info(page):
        contact_info = {'Phone': '', 'Email': '', 'Address': ''}
        try:
            phone_links = page.query_selector_all('a[href^="tel:"]')
            contact_info['Phone'] = "; ".join([link.text_content().strip() for link in phone_links])
            email_link = page.query_selector('a[href^="mailto:"]')
            if email_link: contact_info['Email'] = email_link.text_content().strip()
            address_link = page.query_selector('div.Flex-c11n-8-107-0__sc-n94bjd-0.dHtwdj a[href*="maps"]')
            if address_link: contact_info['Address'] = address_link.text_content().replace('\n', ', ').strip()
        except Exception: pass
        return contact_info
    def extract_agent_details(page, logger):
        details = {'Sales 12mo': '', 'Total Sales': '', 'Rating': '', 'Reviews': '', 'Years of Experience': '', 'Price Range': '', 'Avg Price': '', 'License': '', 'Phone': '', 'Email': '', 'Address': ''}
        try:
            page.wait_for_selector('div.Flex-c11n-8-107-0__sc-n94bjd-0.eHkBjA', timeout=60000)
            for stat in page.query_selector_all('div.Flex-c11n-8-107-0__sc-n94bjd-0.bXVNIZ'):
                label = stat.query_selector('span.Text-c11n-8-107-0__sc-aiai24-0.gOSOFV')
                value = stat.query_selector('span.Text-c11n-8-107-0__sc-aiai24-0.kUNVWz')
                if label and value:
                    label_text, value_text = label.text_content().strip().lower(), value.text_content().strip()
                    if 'last 12 months' in label_text: details['Sales 12mo'] = value_text
                    elif 'total sales' in label_text or 'all-time' in label_text: details['Total Sales'] = value_text
                    elif 'years of experience' in label_text: details['Years of Experience'] = value_text
                    elif 'price range' in label_text: details['Price Range'] = value_text
                    elif 'average price' in label_text: details['Avg Price'] = value_text

            rating_el = page.query_selector('span.StyledNumberRating-c11n-8-107-0__sc-ilk12m-0')
            if rating_el:
                match = re.search(r'\d+\.?\d*', rating_el.text_content().strip())
                if match: details['Rating'] = match.group()
            reviews_element = page.query_selector('a:has-text("reviews")')
            if reviews_element:
                match = re.search(r'\d+', reviews_element.text_content().strip())
                details['Reviews'] = match.group() if match else '0'


            details['License'] = extract_license_info(page, logger)
            details.update(extract_contact_info(page))
        except Exception as e:
            logger(f"    ❌ Detail extraction error: {e}")
        return details
    logger("\n--- STEP 2: Starting Detailed Agent Scraping ---")
    df_input = pd.read_csv(csv_path)
    scraped_data_list = []
    column_order = ['Zip Code', 'Agent Name', 'Sales 12mo', 'Total Sales', 'Rating', 'Reviews', 'Years of Experience', 'Price Range', 'Avg Price', 'License', 'Phone', 'Email', 'Address', 'Profile Link']
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir='new_profile', headless=is_headless,
                args=['--disable-blink-features=AutomationControlled',
                    f"--disable-extensions-except={EXTENSION_PATH.resolve()}",
                    f"--load-extension={EXTENSION_PATH.resolve()}",
]
            )
            page = browser.new_page()
            # page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())
            for index, row in df_input.iterrows():
                if stop_event.is_set(): logger("Stop signal received. Halting detailed scraping."); break
                profile_url, agent_name, zip_code = row.get('Profile Link'), row.get('Agent Name', 'N/A'), row.get('Zip Code', '')
                if not profile_url or pd.isna(profile_url) or not str(profile_url).startswith('http'):
                    logger(f"Skipping row {index+2}: Invalid URL -> {profile_url}"); continue
                logger(f"\n▶ Processing agent {index+1}/{len(df_input)}: {agent_name}")
                try:
                    page.goto(profile_url, timeout=60000, wait_until='domcontentloaded')
                    details = extract_agent_details(page, logger)
                    time.sleep(2)

                    result_row = {'Zip Code': zip_code, 'Agent Name': agent_name, 'Profile Link': profile_url, **details}
                    scraped_data_list.append(result_row)
                    if (index + 1) % 10 == 0 and scraped_data_list:
                        temp_df = pd.DataFrame(scraped_data_list).reindex(columns=column_order)
                        temp_df.to_csv(output_path, index=False)
                        logger(f"  💾 Saved progress for {len(scraped_data_list)} agents to {output_path}")
                    time.sleep(random.uniform(2.0, 4.0))
                except Exception as e:
                    logger(f"  ❌ Error processing agent {agent_name}: {e}")
            browser.close()
        if scraped_data_list:
            final_df = pd.DataFrame(scraped_data_list).reindex(columns=column_order)
            final_df.to_csv(output_path, index=False)
            logger(f"\n✔ Detailed scraping complete! Final results saved to {output_path}")
    except Exception as e:
        logger(f"❌ A critical error occurred during detailed scraping: {e}")


# --- MAIN EXECUTION ---
if __name__ == '__main__':
    try:
        # For PyInstaller compatibility
        from multiprocessing import freeze_support
        freeze_support()
        
        app = ScraperApp()
        app.mainloop()
    except Exception as e:
        print(f"Failed to launch application: {e}")