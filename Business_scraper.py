import requests
from bs4 import BeautifulSoup
import re
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

HEADERS = {"User-Agent": "Mozilla/5.0"}

SOCIAL_PATTERNS = {
    "facebook": re.compile(r"(https?://(www\.)?facebook\.com/[^\s\"']+)", re.I),
    "linkedin": re.compile(r"(https?://(www\.)?linkedin\.com/[^\s\"']+)", re.I),
    "instagram": re.compile(r"(https?://(www\.)?instagram\.com/[^\s\"']+)", re.I),
    "twitter": re.compile(r"(https?://(www\.)?(x\.com|twitter\.com)/[^\s\"']+)", re.I),
}

CONTACT_PATTERNS = re.compile(
    r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b.*?(CEO|Founder|Manager|Director|Owner|Principal|Partner)",
    re.I
)

# ---------- Social & Contact Extractor ----------
def scrape_socials_and_contact(website_url):
    socials = {}
    contact_person = ""

    if not website_url or not website_url.startswith("http"):
        return socials, contact_person

    try:
        r = requests.get(website_url, headers=HEADERS, timeout=8)
        html = r.text

        # socials
        for key, pattern in SOCIAL_PATTERNS.items():
            m = pattern.findall(html)
            if m:
                socials[key] = list({link[0] for link in m})

        # try to find contact person
        match = CONTACT_PATTERNS.search(html)
        if match:
            contact_person = f"{match.group(1)} ({match.group(2)})"

        # follow About/Team/Contact pages
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if any(x in href for x in ["about", "team", "staff", "management", "leadership", "contact"]):
                try:
                    sub_url = href if href.startswith("http") else website_url.rstrip("/") + "/" + href.lstrip("/")
                    r2 = requests.get(sub_url, headers=HEADERS, timeout=6)
                    m2 = CONTACT_PATTERNS.search(r2.text)
                    if m2:
                        contact_person = f"{m2.group(1)} ({m2.group(2)})"
                        break
                except:
                    continue

    except:
        pass

    return socials, contact_person

# ---------- Scraper Functions ----------
def scrape_yellowpages(query, location=""):
    url = f"https://www.yellowpages.com/search?search_terms={query}&geo_location_terms={location}"
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    businesses = []
    for div in soup.select(".result"):
        name = div.select_one(".business-name")
        phone = div.select_one(".phones")
        website = div.select_one("a.track-visit-website")
        address = div.select_one(".adr")
        email = ""  # YellowPages doesn’t expose emails directly

        if name:
            businesses.append({
                "name": name.get_text(strip=True),
                "phone": phone.get_text(strip=True) if phone else "",
                "email": email,
                "website": website["href"] if website else "",
                "address": address.get_text(strip=True) if address else "",
                "source": "YellowPages"
            })
    return businesses

def scrape_hotfrog(query, location=""):
    url = f"https://www.hotfrog.com/search/{location}/{query}"
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    businesses = []
    for div in soup.select(".search-result"):
        name = div.select_one("h3 a")
        website = div.select_one("a.website-link")
        address = div.select_one(".address")
        phone = div.select_one(".phone")

        if name:
            businesses.append({
                "name": name.get_text(strip=True),
                "phone": phone.get_text(strip=True) if phone else "",
                "email": "",
                "website": website["href"] if website else "",
                "address": address.get_text(strip=True) if address else "",
                "source": "Hotfrog"
            })
    return businesses

def scrape_foursquare(query, location=""):
    url = f"https://foursquare.com/v/{query}-{location}"
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    businesses = []
    for div in soup.select(".venueDetails"):
        name = div.select_one("h1")
        website = div.select_one("a[href*='http']")
        address = div.select_one(".venueAddress")
        phone = div.select_one(".phone")

        if name:
            businesses.append({
                "name": name.get_text(strip=True),
                "phone": phone.get_text(strip=True) if phone else "",
                "email": "",
                "website": website["href"] if website else "",
                "address": address.get_text(strip=True) if address else "",
                "source": "Foursquare"
            })
    return businesses

# ---------- Tkinter App ----------
class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Business Scraper")

        self.query_var = tk.StringVar()
        self.loc_var = tk.StringVar()
        self.results = []

        tk.Label(root, text="Search Query:").pack()
        tk.Entry(root, textvariable=self.query_var).pack(fill="x")
        tk.Label(root, text="Location:").pack()
        tk.Entry(root, textvariable=self.loc_var).pack(fill="x")

        tk.Button(root, text="Start Search", command=self.start_search).pack(pady=5)
        tk.Button(root, text="Export CSV", command=self.export_csv).pack(pady=5)

        self.progress = ttk.Progressbar(root, length=300, mode="determinate")
        self.progress.pack(pady=5)

        self.text = tk.Text(root, height=20)
        self.text.pack(fill="both", expand=True)

    def start_search(self):
        query = self.query_var.get()
        loc = self.loc_var.get()
        self.results = []

        sources = [scrape_yellowpages, scrape_hotfrog, scrape_foursquare]

        all_data = []
        for src in sources:
            try:
                data = src(query, loc)
                all_data.extend(data)
            except Exception as e:
                self._log(f"Error with {src.__name__}: {e}")

        self.results = all_data
        self.progress["maximum"] = len(self.results)

        for i, b in enumerate(self.results, start=1):
            if b.get("website"):
                socials, contact = scrape_socials_and_contact(b["website"])
                b["socials"] = socials
                b["contact_person"] = contact
            else:
                b["socials"] = {}
                b["contact_person"] = ""

            self._log(
                f"{i}. {b['name']} | 📞 {b['phone']} | 📧 {b['email']} | 🌐 {b['website']} "
                f"| 📍 {b['address']} | 👤 {b['contact_person']} | "
                f"Socials: {', '.join([f'{k}:{len(v)}' for k,v in b['socials'].items()])} "
                f"[{b['source']}]"
            )
            self.progress["value"] = i
            self.root.update_idletasks()

    def export_csv(self):
        if not self.results:
            messagebox.showwarning("No Data", "Please run a search first.")
            return

        file = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file:
            return

        with open(file, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Name","Phone","Email","Website","Address","Contact Person","Social Links","Source"])
            for b in self.results:
                socials_str = "; ".join([f"{k}:{','.join(v)}" for k,v in b.get("socials",{}).items()])
                w.writerow([
                    b.get("name",""),
                    b.get("phone",""),
                    b.get("email",""),
                    b.get("website",""),
                    b.get("address",""),
                    b.get("contact_person",""),
                    socials_str,
                    b.get("source","")
                ])
        messagebox.showinfo("Exported", f"Data saved to {file}")

    def _log(self, msg):
        self.text.insert("end", msg + "\n")
        self.text.see("end")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()
