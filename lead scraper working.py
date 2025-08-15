import tkinter as tk
from tkinter import ttk, scrolledtext
import csv
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime
import re

class UntraceableLeadScraper:
    def __init__(self):
        self.ua = UserAgent()
        # regex patterns
        self.email_re = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
        # very permissive phone regex (international/US)
        self.phone_re = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?){1,4}\d{3,4}")
        # social domains to look for
        self.social_domains = ["facebook.com", "twitter.com", "linkedin.com", "instagram.com", "youtube.com"]

    def scrape(self, url):
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': 'https://www.google.com',
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return {"error": f"HTTP {resp.status_code}"}

            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)

            # emails
            emails = set(self.email_re.findall(text))
            # also catch mailto: links
            for a in soup.find_all('a', href=True):
                if a['href'].startswith("mailto:"):
                    addr = a['href'].split("mailto:")[1].split("?")[0]
                    emails.add(addr)

            # phones
            phones = set(self.phone_re.findall(text))

            # social links
            socials = set()
            for a in soup.find_all('a', href=True):
                href = a['href']
                for d in self.social_domains:
                    if d in href:
                        socials.add(href)

            return {
                "emails": sorted(emails),
                "phones": sorted(phones),
                "socials": sorted(socials)
            }
        except Exception as e:
            return {"error": str(e)}


class LeadScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Lead Scraper")
        self.scraper = UntraceableLeadScraper()
        self.results = {}  # url -> scrape dict or error
        self._build_ui()

    def _build_ui(self):
        tk.Label(self.root, text="Enter URLs (one per line):").pack(pady=4)
        self.url_text = tk.Text(self.root, height=8, width=60)
        self.url_text.pack()

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=4)
        tk.Button(btn_frame, text="Start Scraping", command=self.start_scraping).grid(row=0, column=0, padx=4)
        tk.Button(btn_frame, text="Export CSV",    command=self.export_csv).grid(row=0, column=1, padx=4)

        self.progress = ttk.Progressbar(self.root, length=400, mode='determinate')
        self.progress.pack(pady=4)

        self.output = scrolledtext.ScrolledText(self.root, height=16, width=80)
        self.output.pack(pady=4)

    def start_scraping(self):
        self.output.delete("1.0", tk.END)
        self.results.clear()
        urls = [u.strip() for u in self.url_text.get("1.0", tk.END).splitlines() if u.strip()]
        if not urls:
            self.output.insert(tk.END, "▶ Please enter at least one URL.\n")
            return

        total = len(urls)
        for idx, url in enumerate(urls, 1):
            self.output.insert(tk.END, f"Scraping {url} …\n")
            res = self.scraper.scrape(url)
            self.results[url] = res

            if "error" in res:
                self.output.insert(tk.END, f"  ✖ Error: {res['error']}\n\n")
            else:
                if res["emails"]:
                    self.output.insert(tk.END, "  ✉️ Emails:\n")
                    for e in res["emails"]:
                        self.output.insert(tk.END, f"    • {e}\n")
                else:
                    self.output.insert(tk.END, "  ✉️ Emails: (none found)\n")

                if res["phones"]:
                    self.output.insert(tk.END, "  📞 Phones:\n")
                    for p in res["phones"]:
                        self.output.insert(tk.END, f"    • {p}\n")
                else:
                    self.output.insert(tk.END, "  📞 Phones: (none found)\n")

                if res["socials"]:
                    self.output.insert(tk.END, "  🔗 Social Links:\n")
                    for s in res["socials"]:
                        self.output.insert(tk.END, f"    • {s}\n")
                else:
                    self.output.insert(tk.END, "  🔗 Social Links: (none found)\n")
                self.output.insert(tk.END, "\n")

            self.progress['value'] = (idx/total)*100
            self.root.update_idletasks()

    def export_csv(self):
        if not self.results:
            self.output.insert(tk.END, "▶ Nothing to export. Run scraping first.\n")
            return

        fname = f"contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(fname, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["URL", "Type", "Detail"])
                for url, res in self.results.items():
                    if "error" in res:
                        writer.writerow([url, "error", res["error"]])
                    else:
                        for e in res["emails"]:
                            writer.writerow([url, "email", e])
                        for p in res["phones"]:
                            writer.writerow([url, "phone", p])
                        for s in res["social",]:
                            writer.writerow([url, "social", s])
            self.output.insert(tk.END, f"\n✔ Exported all contacts to {fname}\n")
        except Exception as e:
            self.output.insert(tk.END, f"\n✖ Failed to export: {e}\n")


if __name__ == "__main__":
    root = tk.Tk()
    LeadScraperApp(root)
    root.mainloop()
