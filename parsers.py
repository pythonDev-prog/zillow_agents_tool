import re
from typing import Dict, Any
from bs4 import BeautifulSoup
from playwright.sync_api import Page

def extract_license_info(page: Page, logger: callable) -> str:
    """Extracts license information from the modal dialog."""
    try:
        license_button = page.locator(".cJVBTO button").first
        if not license_button.is_visible():
            return ""

        license_button.click()
        dialog_body_selector = "div.DialogBody-c11n-8-107-0__sc-1l4a94i-0"
        page.wait_for_selector(dialog_body_selector, timeout=5000)

        license_cards = page.query_selector_all(f"{dialog_body_selector} .StyledCard-c11n-8-107-0__sc-1w6p0lv-0")
        all_licenses = []

        for card in license_cards:
            soup = BeautifulSoup(card.inner_html(), 'html.parser')
            texts = [span.get_text(strip=True) for span in soup.select('.Grid-c11n-8-107-0__sc-18zzowe-0 span')]
            
            license_num, issuer = "", ""
            try:
                license_num = texts[texts.index('License #:') + 1]
            except (ValueError, IndexError):
                pass
            
            try:
                issuer = texts[texts.index('Issued by:') + 1]
            except (ValueError, IndexError):
                pass
                
            if license_num:
                all_licenses.append(f"{license_num} ({issuer})")

        close_button = page.query_selector('section[role="dialog"] button:has-text("Close")')
        if close_button:
            close_button.click()
            page.wait_for_selector('section[role="dialog"]', state='hidden', timeout=3000)
            
        return "; ".join(all_licenses) if all_licenses else ""
        
    except Exception as e:
        logger(f"    ⓘ License extraction notice: {e}")
        return ""

def extract_contact_info(page: Page) -> Dict[str, str]:
    """Extracts phone, email, and address contact information."""
    contact_info = {'Phone': '', 'Email': '', 'Address': ''}
    try:
        phone_links = page.query_selector_all('a[href^="tel:"]')
        contact_info['Phone'] = "; ".join([link.text_content().strip() for link in phone_links])
        
        email_link = page.query_selector('a[href^="mailto:"]')
        if email_link:
            contact_info['Email'] = email_link.text_content().strip()
            
        address_link = page.query_selector('div.Flex-c11n-8-107-0__sc-n94bjd-0.dHtwdj a[href*="maps"]')
        if address_link:
            contact_info['Address'] = address_link.text_content().replace('\n', ', ').strip()
    except Exception:
        pass
    
    return contact_info

def extract_agent_details(page: Page, logger: callable) -> Dict[str, Any]:
    """Extracts all agent details including stats, rating, reviews, and contact info."""
    details = {
        'Sales 12mo': '', 'Total Sales': '', 'Rating': '', 'Reviews': '', 
        'Years of Experience': '', 'Price Range': '', 'Avg Price': '', 
        'License': '', 'Phone': '', 'Email': '', 'Address': ''
    }
    
    try:
        page.wait_for_selector('div.Flex-c11n-8-107-0__sc-n94bjd-0.eHkBjA', timeout=60000)
        
        # Extract stats grid
        for stat in page.query_selector_all('div.Flex-c11n-8-107-0__sc-n94bjd-0.bXVNIZ'):
            label = stat.query_selector('span.Text-c11n-8-107-0__sc-aiai24-0.gOSOFV')
            value = stat.query_selector('span.Text-c11n-8-107-0__sc-aiai24-0.kUNVWz')
            
            if label and value:
                label_text = label.text_content().strip().lower()
                value_text = value.text_content().strip()
                
                if 'last 12 months' in label_text:
                    details['Sales 12mo'] = value_text
                elif 'total sales' in label_text or 'all-time' in label_text:
                    details['Total Sales'] = value_text
                elif 'years of experience' in label_text:
                    details['Years of Experience'] = value_text
                elif 'price range' in label_text:
                    details['Price Range'] = value_text
                elif 'average price' in label_text:
                    details['Avg Price'] = value_text

        # Extract Rating
        rating_el = page.query_selector('span.StyledNumberRating-c11n-8-107-0__sc-ilk12m-0')
        if rating_el:
            match = re.search(r'\d+\.?\d*', rating_el.text_content().strip())
            if match:
                details['Rating'] = match.group()
                
        # Extract Reviews
        reviews_element = page.query_selector('a:has-text("reviews")')
        if reviews_element:
            match = re.search(r'\d+', reviews_element.text_content().strip())
            details['Reviews'] = match.group() if match else '0'

        # Extract License and Contact info
        details['License'] = extract_license_info(page, logger)
        details.update(extract_contact_info(page))
        
    except Exception as e:
        logger(f"    ❌ Detail extraction error: {e}")
        
    return details
