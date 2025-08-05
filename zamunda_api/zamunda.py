import re
import requests
from bs4 import BeautifulSoup as bs
from login_headers import login_headers


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
zamunda_instance = zamunda(
    base_url="https://zamunda.net",
    user="coyec75395",
    password="rxM6N.h2N4aYe7_"
)

results = zamunda_instance.search("john wick")
for r in results:
    print(r)
