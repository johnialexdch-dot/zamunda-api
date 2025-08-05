import re
import requests
from bs4 import BeautifulSoup as bs

# Headers за логин в Zamunda (актуални към 2025)
login_headers = {
    'authority': 'zamunda.net',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9,bg;q=0.8,de;q=0.7',
    'cache-control': 'max-age=0',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://zamunda.net',
    'referer': 'https://zamunda.net/login.php',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

class zamunda():
    def __init__(self, base_url, user, password):
        self.user = user
        self.password = password
        self.session = requests.Session()
        self.base_url = base_url
        self.login()

    def login(self):
        response = self.session.post(
            f'{self.base_url}/takelogin.php',
            data={
                'username': self.user,
                'password': self.password
            },
            headers=login_headers
        )

        if response.status_code == 200 and re.search(self.user, response.text, re.IGNORECASE):
            print('Login Successful')
            self._use_log = True
            return True
        else:
            print('Login Error')
            raise Exception("LoginFail")

    def search(self, query):
        url = f"{self.base_url}/bananas"
        params = {
            "search": query,
            "gotonext": "1",
            "field": "name",
            "sort": "9",
            "type": "desc"
        }

        response = self.session.get(url, params=params)
        if response.status_code != 200:
            print(f"Search error: HTTP {response.status_code}")
            return []

        soup = bs(response.text, "html.parser")
        table = soup.find("table", {"id": "zbtable"})
        if not table:
            print("No results table found.")
            return []

        results = []

        for tr in table.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) < 5:
                continue

            title_tag = tds[1].find("a")
            title = title_tag.text.strip() if title_tag else "Без заглавие"

            download_links = [
                a['href'] for a in tds[1].find_all('a') if a['href'].startswith('/download.php')
            ]

            size = tds[-4].get_text(strip=True)
            seeds = tds[-2].get_text(strip=True)

            audio = any("bgaudio.png" in img.get("src", "") for img in tds[1].find_all("img"))

            results.append({
                "title": title,
                "download_links": download_links,
                "size": size,
                "seeds": seeds,
                "bg_audio": audio
            })

        return results


# ТЕСТ:
if __name__ == "__main__":
    zamunda_instance = zamunda(
        base_url="https://zamunda.net",
        user="coyec75395",
        password="rxM6N.h2N4aYe7_"
    )

    results = zamunda_instance.search("john wick")
    for r in results:
        print(r)
