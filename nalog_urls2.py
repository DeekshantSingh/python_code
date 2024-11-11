import requests
from parsel import Selector
from ugTranslate import translate_text
import pandas as pd
import re
from datetime import datetime

# Define cookies and headers
cookies = {
    'PHPSESSID': 'RJX37Du3XfLxEeR8amX7rqQ4wdEManhs',
    'BITRIX_SM_GUEST_ID': '21045036',
    'USER_LANG': 'ru',
    'BX_USER_ID': '5e25fee2df7caed0d4c3498b07487938',
    '_ym_uid': '1730960236385157996',
    '_ym_d': '1730960236',
    '_ym_isad': '2',
    '_gid': 'GA1.3.339262156.1730960237',
    '_ga': 'GA1.3.422977174.1730960236',
    'cookies_accepted': 'true',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'referer': 'https://nalog.gov.by/news/?PAGEN_1=73',
    'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
}

data_entries = []
# Function to save data to an Excel file
def save_to_excel(filename='nalog_data.xlsx'):
    df = pd.DataFrame(data_entries)
    df.to_excel(filename, index=False, engine='openpyxl')
    print(f"Data saved to {filename}")

# Function to split content into parts of up to 3000 characters each
def split_text(text, max_length=3000):
    parts = []
    while len(text) > max_length:
        split_index = text.rfind(" ", 0, max_length)
        split_index = split_index if split_index != -1 else max_length
        parts.append(text[:split_index].strip())
        text = text[split_index:].strip()
    parts.append(text)
    return parts

# Function to parse and format the date to yyyy-mm-dd
def format_date(date_str):
    for fmt in ("%d %B %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str  # Return original if parsing fails

# Function to extract phone number
def extract_phone(content):
    phone = 'N/A'  # Default if phone not found
    if 'Contact phone: ' in content:
        phone = content.split('Contact phone: ')[-1].strip()
    elif 't.: ' in content:
        phone = content.split('t.: ')[-1].strip()
    return phone

# Initial request to get total pages
response = requests.get('https://nalog.gov.by/news/', cookies=cookies, headers=headers)
parsed_data = Selector(response.text)
total_pages = int(parsed_data.xpath('(//li[@class]//a//span)[4]//text()').get())

# Loop through pages
for page_num in range(1, total_pages + 1):
    page_url = f'https://nalog.gov.by/news/?PAGEN_1={page_num}'
    print(f"Processing page: {page_url}")
    response2 = requests.get(page_url, cookies=cookies, headers=headers)
    parsed_data2 = Selector(response2.text)
    home_page_url = "https://nalog.gov.by"

    # Extract each news link
    news_links = parsed_data2.xpath('.//div[@class="item-list-news "]//a[not(contains(@href, "?tag="))]/@href').getall()
    for news_link in news_links:
        if 'news' not in news_link:
            print(f"Skipping URL (does not contain 'news'): {news_link}")
            continue  # Skip this link if 'news' is not in the URL
        news_url = home_page_url + news_link
        response3 = requests.get(news_url, cookies=cookies, headers=headers)
        parsed_data3 = Selector(response3.text)

        # Extract data fields
        heading_name = parsed_data3.xpath('//h2//text()').get()
        news_date_raw = parsed_data3.xpath('//div[@class="item-news__date mb-4"]//text()').get()
        news_date = format_date(translate_text(news_date_raw)['TranslatedText'])

        # Extract and clean article content
        texts = parsed_data3.xpath('//div[@class="item-news__body mb-4 mb-md-5"]//p//text()').getall()
        final_text = ' '.join(re.sub(r'\s+', ' ', text).strip().rstrip('.') for text in texts if text.strip())

        # Translate content in parts
        translated_content = ''
        for part in split_text(final_text):
            translated_part = translate_text(part)['TranslatedText']
            translated_content += translated_part + "\n"

        # Check if content is empty and assign "N/A" if necessary
        if not translated_content.strip():
            translated_content = "N/A"

        # Extract contract (phone number)
        contract = extract_phone(translated_content)

        # Add the formatted entry
        data_entries.append({
            "url": news_url,
            "News_date": news_date,
            "Heading": translate_text(heading_name)['TranslatedText'],
            "Contract": contract,  # Add phone number under 'Contract'
            "Content": translated_content.strip()

        })

        print(data_entries[-1])  # Display the latest entry
        print("---------------------------------------------------------------")

# Save data to Excel
save_to_excel()
