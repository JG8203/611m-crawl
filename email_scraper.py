
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests

EMAIL_REGEX = re.compile(
    r'(?:mailto:)?[\'"‘“]?\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b[\'"’”]?',
    re.IGNORECASE
)

# Decrypt Cloudflare protected email
def cfDecodeEmail(encodedString):
    try:    
        r = int(encodedString[:2],16)
        email = ''.join([chr(int(encodedString[i:i+2], 16) ^ r) for i in range(2, len(encodedString), 2)])
    except Exception as e:
        print(f"Error decoding Cloudflare email: {e}")
        email = None
    return email

#Find emails
def find_emails(html: str, url: str):
    results = []        #TODO: Handle emails with affiliations and names
    emails = []
    
    # TODO: Handle affiliations and names
    soup = BeautifulSoup(html, "html.parser")
    
    
    #TODO: Remove if not needed anymore
    #Find explicit emails with mailto
    # for a in soup.find_all('a', href=True):
        #DEBUG
        #print(a)
    #     href = a['href'].strip()
    #     if href.startswith('mailto:'):
    #         if href.lower().startswith("mailto:"):
    #             email = href.split(":", 1)[1].split("?")[0].strip()
            
    
    text_content = soup.get_text(separator=" ", strip=True)
    for match in EMAIL_REGEX.findall(text_content):
        emails.append(match)

            
    #Find Cloudflare protected emails
    for span in soup.find_all('span', class_="__cf_email__"):
        
        #DEBUG
        #print(span)
        
        data_cfemail = span.get('data-cfemail')
        if data_cfemail:
            email = cfDecodeEmail(data_cfemail)
            if EMAIL_REGEX.match(email):
                emails.append(email)
                
    return emails   #TODO: Return affiliations and names as well



# --- Sample pages to inspect email extraction ---

# FOR DEBUGGING

# pages = [
#     ("quality@dlsu.edu.ph", "https://www.dlsu.edu.ph/smqa/", "smqa"),
#     ("scholarships@dlsu.edu.ph", "https://www.dlsu.edu.ph/admissions/scholarships/", "admissions"),
#     ("admission.requirements@dlsu.edu.ph", "https://www.dlsu.edu.ph/admissions/undergraduate/", "admissions"),
#     ("graduate.admissions@dlsu.edu.ph", "https://www.dlsu.edu.ph/admissions/graduate/", "admissions"),
#     ("computerstudies@dlsu.edu.ph", "https://www.dlsu.edu.ph/colleges/ccs/", "colleges"),
#     ("graduate.admissions@dlsu.edu.ph", "https://www.dlsu.edu.ph/tdsol/", "tdsol"),
#     ("officeCLA@dlsu.edu.ph", "https://www.dlsu.edu.ph/colleges/cla/", "colleges"),
#     ("chaircomm@dlsu.edu.ph", "https://www.dlsu.edu.ph/colleges/cla/academic-departments/communication/", "colleges"),
#     ("deancos@dlsu.edu.ph", "https://www.dlsu.edu.ph/colleges/cos/", "colleges"),
#     ("chairIE@dlsu.edu.ph", "https://www.dlsu.edu.ph/colleges/gcoe/academic-departments/industrial-engineering/", "colleges"),
#     ("dean.cob@dlsu.edu.ph", "https://www.dlsu.edu.ph/colleges/rvrcob/", "colleges"),
#     ("hub@dlsu.edu.ph", "https://www.dlsu.edu.ph/campuses/manila", "campuses"),
#     ("admission.requirements@dlsu.edu.ph", "https://www.dlsu.edu.ph/admissions/undergraduate/degree-programs/", "admissions"),
#     ("gaodir@dlsu.edu.ph", "https://www.dlsu.edu.ph/admissions/graduate/degree-programs/", "admissions"),
#     ("SoLL@dlsu.edu.ph", "https://www.dlsu.edu.ph/soll/", "soll"),
#     ("registrar@dlsu.edu.ph", "https://www.dlsu.edu.ph/offices/registrar/", "offices"),
# ]


# # --- Run inspection ---
# for expected_email, url, affiliation in pages:
#     print("="*80)
#     print(f"Checking {url}")
    
#     try:
#         resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
#         found = find_emails(resp.text, url)
#         print(found)
#     except Exception as e:
#         print(" ❌ Error:", e)



