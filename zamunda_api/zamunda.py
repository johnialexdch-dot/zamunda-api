"""
zamunda.py
This module provides a class `Zamunda` 
to interact with the Zamunda website for logging in and searching for torrents.
"""

import time
from bs4 import BeautifulSoup as bs
from requests import Session, Timeout
try:
    from login_headers import login_headers
except ImportError:
    from zamunda_api.login_headers import login_headers
from requests.exceptions import RequestException, ConnectionError
from torrentool.api import Torrent


class Zamunda:
    """
    A class to handle login and search operations on the Zamunda website.
    """

    def __init__(self) -> None:
        self.session = Session()
        self.base = 'https://zamunda.net'

    def login(self, user, password, retries=3, backoff_factor=2):
        """
        Logs in to Zamunda with retries and error handling.
        """
        if not user or not password:
            raise ValueError("Username and password cannot be empty.")

        takelogin_url = f"{self.base}/takelogin.php"
        payload = {
            'username': user,
            'password': password
        }

        attempt = 0
        while attempt <= retries:
            try:
                response = self.session.post(
                    takelogin_url,
                    headers=login_headers,
                    data=payload,
                    timeout=10
                )
                if response.status_code == 200:
                    print("Login successful.")
                    return
                else:
                    response.raise_for_status()
            except ConnectionError as e:
                attempt += 1
                if attempt > retries:
                    print("Max retries reached. Unable to connect.")
                    raise
                print(f"Connection error: {e}. Retrying in {backoff_factor ** attempt} seconds...")
                time.sleep(backoff_factor ** attempt)
            except Timeout as e:
                print(f"Request timed out: {e}")
                raise
            except RequestException as e:
                print(f"An error occurred: {e}")
                raise

        raise RuntimeError("Login failed after multiple attempts.")

    def get_torrent(self, href):
        """
        Fetches a torrent file from the given href and returns a Torrent object.
        """
        url = f"{self.base}{href}"
        response = self.session.get(url)
        if response.status_code == 200:
            torrent = Torrent.from_string(response.content)
            return torrent
        else:
            print(f"Error: Received status code {response.status_code} for {href}")

            class DummyTorrent:
                magnet_link = None
                info_hash = None

            return DummyTorrent()

    def search(self, ss: str, user: str, password: str, provide_infohash: bool = False):
        """
        Searches for torrents on Zamunda using the /bananas interface.
        """
        try:
            self.login(user, password)
        except Exception as e:
            print(f"Login error: {e}")
            return []

        data = []
        # The search string must be URL encoded properly; requests handles it via params.
        url = f"{self.base}/bananas"

        params = {
            "c5": "1",
            "c19": "1",
            "c20": "1",
            "c24": "1",
            "c25": "1",
            "c28": "1",
            "c31": "1",
            "c35": "1",
            "c42": "1",
            "c46": "1",
            "c7": "1",
            "c33": "1",
            "c1": "1",
            "c22": "1",
            "c26": "1",
            "c32": "1",
            "c37": "1",
            "search": ss,
            "gotonext": "1",
            "incldead": "",
            "field": "name",
            "sort": "9",
            "type": "desc"
        }

        response = self.session.get(url, params=params)
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            return data

        soup = bs(response.text, 'html.parser')

        table = soup.find('table', {'id': "zbtable"})
        if not table:
            print("No results table found.")
            return data

        trs = table.find_all('tr')[1:]  # skip header

        for tr in trs:
            tds = tr.find_all('td')
            if len(tds) < 5:
                continue

            # Названието
            name = tds[1].find('a').find('b').get_text(strip=True)

            # Линкове (магнит и download)
            hrefs = tds[1].find('div').find_all('a')
            seeds = tds[-2].get_text(strip=True)
            size = tds[-4].get_text(strip=True)

            imgs = tds[1].find_all('img')
            audio = any(i.get('src', '').endswith("bgaudio.png") for i in imgs)

            for href in hrefs:
                href_link = href['href']
                if href_link.startswith('/download.php'):
                    torrent = self.get_torrent(href_link)
                    data.append({
                        "name": name,
                        "magnetlink": torrent.magnet_link,
                        'seeders': seeds,
                        'bg_audio': audio,
                        'size': size,
                        'infohash': torrent.info_hash if provide_infohash else None
                    })

        return data
