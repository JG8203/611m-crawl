
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
