import sys
from gui import ScraperApp

def main():
    try:
        # For PyInstaller compatibility
        from multiprocessing import freeze_support
        freeze_support()
        
        app = ScraperApp()
        app.mainloop()
    except Exception as e:
        print(f"Failed to launch application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
