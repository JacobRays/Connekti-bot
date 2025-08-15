import re
import csv

def extract_email(text):
    # Basic email pattern
    pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    emails = re.findall(pattern, text)
    return emails[0] if emails else ""

def extract_phone(text):
    # Extract phone numbers in different formats
    pattern = r'(\+?\d[\d\s\-]{7,}\d)'
    phones = re.findall(pattern, text)
    return phones[0].strip() if phones else ""

def extract_website(text):
    # Extract URLs
    pattern = r'(https?://[^\s]+|www\.[^\s]+)'
    urls = re.findall(pattern, text)
    return urls[0] if urls else ""

def clean_text(text):
    # Remove extra spaces and line breaks
    return re.sub(r'\s+', ' ', text).strip()

def parse_lead(raw_text):
    """
    Attempt to parse a single lead block of text.
    The function tries to guess first name, last name, company, location from remaining text.
    """
    # Extract email, phone, website
    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    website = extract_website(raw_text)

    # Remove email, phone, website from text for easier name/company extraction
    text = raw_text
    if email:
        text = text.replace(email, '')
    if phone:
        text = text.replace(phone, '')
    if website:
        text = text.replace(website, '')

    # Clean remaining text
    text = clean_text(text)

    # Split remaining text by commas or line breaks or pipes
    parts = re.split(r'[,|\n]', text)
    parts = [p.strip() for p in parts if p.strip()]

    # Initialize defaults
    first_name = last_name = company = location = ""

    # Try to guess name and company
    if parts:
        # Assume first part could be full name
        name_parts = parts[0].split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])
        else:
            first_name = parts[0]

        # Try to get company and location from remaining parts
        if len(parts) > 1:
            company = parts[1]
        if len(parts) > 2:
            location = parts[2]

    return {
        "first_name": first_name,
        "last_name": last_name,
        "company": company,
        "website": website,
        "email": email,
        "phone": phone,
        "location": location
    }

def main():
    print("Paste your raw leads below (enter 'DONE' on a new line when finished):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == 'DONE':
            break
        lines.append(line)

    raw_data = "\n".join(lines)
    # Split raw data into blocks - assuming leads separated by blank lines
    lead_blocks = re.split(r'\n\s*\n', raw_data.strip())

    leads = []
    for block in lead_blocks:
        lead = parse_lead(block)
        leads.append(lead)

    # Output CSV filename
    filename = "arranged_leads.csv"

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["first_name", "last_name", "company", "website", "email", "phone", "location"])
        writer.writeheader()
        for lead in leads:
            writer.writerow(lead)

    print(f"\nArranged {len(leads)} leads saved to {filename}")

if __name__ == "__main__":
    main()