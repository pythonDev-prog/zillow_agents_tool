import queue
import threading
import time
import customtkinter as ctk

from config import (
    APP_TITLE, APP_GEOMETRY, APP_MIN_SIZE, GUI_COLORS, STATUS_COLORS,
    PROFILES_CSV, DETAILED_CSV
)
from scraper import ZillowScraper

class ScraperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title(APP_TITLE)
        self.geometry(APP_GEOMETRY)
        self.resizable(True, True)
        self.minsize(*APP_MIN_SIZE)

        # --- Theme ---
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # --- State ---
        self.scraper_thread = None
        self.stop_event = threading.Event()
        self.log_queue = queue.Queue()

        self._build_ui()
        
        # --- Initialization ---
        self.after(100, self._center_window)
        self.after(100, self._process_log_queue)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_header()
        self._build_config_section()
        self._build_control_buttons()
        self._build_status_section()
        self._build_footer()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color=GUI_COLORS['surface'], corner_radius=15)
        header_frame.grid(row=0, column=0, padx=25, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame, text="🏠 Zillow Agent Scraper",
            font=ctk.CTkFont(size=28, weight="bold"), text_color=GUI_COLORS['text_primary']
        )
        title_label.grid(row=0, column=0, padx=30, pady=(20, 5))

        subtitle_label = ctk.CTkLabel(
            header_frame, text="Professional Real Estate Agent Data Collection Tool",
            font=ctk.CTkFont(size=14), text_color=GUI_COLORS['text_secondary']
        )
        subtitle_label.grid(row=1, column=0, padx=30, pady=(0, 20))

    def _build_config_section(self):
        config_frame = ctk.CTkFrame(self, fg_color=GUI_COLORS['surface'], corner_radius=15)
        config_frame.grid(row=1, column=0, padx=25, pady=5, sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)

        zip_label = ctk.CTkLabel(
            config_frame, text="Target Zip Codes:",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=GUI_COLORS['text_primary']
        )
        zip_label.grid(row=1, column=0, padx=(25, 15), pady=8, sticky="w")

        self.zips_entry = ctk.CTkEntry(
            config_frame, placeholder_text="e.g., 90210, 10001, 33139",
            font=ctk.CTkFont(size=13), height=40, corner_radius=8,
            border_width=2, border_color=GUI_COLORS['border']
        )
        self.zips_entry.grid(row=1, column=1, padx=(0, 25), pady=8, sticky="ew")

        pages_label = ctk.CTkLabel(
            config_frame, text="Pages per Zip Code:",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=GUI_COLORS['text_primary']
        )
        pages_label.grid(row=2, column=0, padx=(25, 15), pady=8, sticky="w")

        self.pages_option_menu = ctk.CTkOptionMenu(
            config_frame, values=["10", "20", "25", "All"],
            font=ctk.CTkFont(size=13), height=40, corner_radius=8,
            button_color=GUI_COLORS['primary'], button_hover_color=GUI_COLORS['primary_hover']
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

    def _build_control_buttons(self):
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=25, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.start_button = ctk.CTkButton(
            button_frame, text="🚀 Start Scraping", command=self.start_scraping, height=50,
            font=ctk.CTkFont(size=16, weight="bold"), corner_radius=12,
            fg_color=GUI_COLORS['success'], hover_color=GUI_COLORS['success_hover']
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.stop_button = ctk.CTkButton(
            button_frame, text="⏹️ Stop Scraping", command=self.stop_scraping, height=50,
            font=ctk.CTkFont(size=16, weight="bold"), corner_radius=12, state="disabled",
            fg_color=GUI_COLORS['danger'], hover_color=GUI_COLORS['danger_hover']
        )
        self.stop_button.grid(row=0, column=1, padx=(10, 0), sticky="ew")

    def _build_status_section(self):
        status_frame = ctk.CTkFrame(self, fg_color=GUI_COLORS['surface'], corner_radius=15)
        status_frame.grid(row=3, column=0, padx=25, pady=(5, 0), sticky="nsew")
        status_frame.grid_rowconfigure(2, weight=1)
        status_frame.grid_columnconfigure(0, weight=1)

        monitor_header_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        monitor_header_frame.grid(row=0, column=0, padx=25, pady=(15, 10), sticky="ew")

        status_title = ctk.CTkLabel(
            monitor_header_frame,
            text="📊 Activity Monitor:",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=GUI_COLORS['text_primary']
        )
        status_title.grid(row=0, column=0, sticky="w")

        self.status_label = ctk.CTkLabel(
            monitor_header_frame,
            text="Ready to begin scraping",
            font=ctk.CTkFont(size=14),
            text_color=GUI_COLORS['text_secondary'],
            anchor="w"
        )
        self.status_label.grid(row=0, column=1, padx=(10, 0), sticky="w")

        self.progress_bar = ctk.CTkProgressBar(
            status_frame,
            height=8,
            corner_radius=4,
            progress_color=GUI_COLORS['primary']
        )
        self.progress_bar.grid(row=1, column=0, padx=25, pady=(0, 15), sticky="ew")
        self.progress_bar.set(0)

        log_container = ctk.CTkFrame(status_frame, fg_color=GUI_COLORS['background'], corner_radius=10)
        log_container.grid(row=2, column=0, padx=25, pady=(0, 20), sticky="nsew")
        log_container.grid_rowconfigure(0, weight=1)
        log_container.grid_columnconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(
            log_container,
            state="disabled",
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            corner_radius=8,
            fg_color=GUI_COLORS['background'],
            text_color=GUI_COLORS['text_primary'],
            scrollbar_button_color=GUI_COLORS['surface'],
            scrollbar_button_hover_color=GUI_COLORS['surface_light']
        )
        self.log_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def _build_footer(self):
        footer_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
        footer_frame.grid(row=4, column=0, padx=25, pady=(5, 15), sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=1)

        footer_label = ctk.CTkLabel(
            footer_frame,
            text="© 2025 Zillow Scraper",
            font=ctk.CTkFont(size=11),
            text_color=GUI_COLORS['text_secondary']
        )
        footer_label.grid(row=0, column=0)

    def log(self, message: str):
        self.log_queue.put(message)

    def _process_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get_nowait()
            self.log_textbox.configure(state="normal")
            timestamp = time.strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            self.log_textbox.insert("end", formatted_message + "\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        self.after(100, self._process_log_queue)

    def update_status(self, message: str, status_type: str = "info"):
        color = STATUS_COLORS.get(status_type, GUI_COLORS['text_secondary'])
        self.status_label.configure(text=message, text_color=color)

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

        # Initialize the decoupled scraper
        scraper = ZillowScraper(
            zip_codes=zip_codes,
            num_pages=num_pages,
            is_headless=is_headless,
            logger=self.log,
            stop_event=self.stop_event
        )

        self.scraper_thread = threading.Thread(
            target=scraper.run,
            args=(PROFILES_CSV, DETAILED_CSV, self.on_scraping_complete, self)
        )
        self.scraper_thread.daemon = True
        self.scraper_thread.start()

    def stop_scraping(self):
        self.log("🛑 STOP command issued. Finishing current task and saving progress...")
        self.update_status("Stopping scraper...", "stopping")
        self.stop_button.configure(state="disabled")
        self.stop_event.set()

    def on_scraping_complete(self, final_status: str):
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

    def _center_window(self):
        self.update_idletasks()
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        width, height = self.winfo_width(), self.winfo_height()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
