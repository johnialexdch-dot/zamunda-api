
"""
zamunda.py
This module provides a class `Zamunda` 
to interact with the Zamunda website for logging in and searching for torrents.
Classes:
    Zamunda: A class to handle login and search operations on the Zamunda website.
"""
import time
from bs4 import BeautifulSoup as bs
from requests import Session, Timeout
try:
    from login_headers import login_headers
except ImportError:
    from zamunda_api.login_headers import login_headers
from requests.exceptions import RequestException
from torrentool.api import Torrent


class Zamunda:
    """
    class Zamunda
    A class to handle login and search operations on the Zamunda website.
    """
    def __init__(self) -> None:
        self.session = Session()
        self.base = 'https://zamunda.net'

    def login(self, user, password, retries=3, backoff_factor=2):
        """
        Logs in to the Zamunda website with retry logic and error handling.
        :param user: The username to log in with.
        :param password: The password to log in with.
        :param retries: Number of retry attempts for connection errors.
        :param backoff_factor: Factor by which the wait time increases after each retry.
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
                # Post the login credentials
                response = self.session.post(
                    takelogin_url,
                    headers=login_headers,
                    data=payload,
                    timeout=10
                )
                
                # Check if login was successful
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
    
    def search(self, ss:str, user:str, password:str, provide_magnet:bool=False, provide_infohash:bool=False):
        """
        Searches for torrents on the Zamunda website.
        :param ss: The search string to search for.
        :param user: The username to log in with.
        :param password: The password to log in with.
        :param provide_magnet: Whether to provide the magnet link or the download page link.
        """
        try:
            self.login(user,password)
        except Exception as e:
            print(f"Error: {e}")
            return []
        data = []
        ss=ss.replace(" ","+")
        url = f"{self.base}/bananas?search={ss}&gotonext=1&incldead=&field=name&sort=9&type=desc"

        response = self.session.get(url)
        if response.status_code != 200:
            print("Error: ",response.status_code)
            return data

        soup = bs(response.text, 'html.parser')

        table = soup.find('table',{'id': "zbtable"})
        if not table:
            print("No table found")
            return data
        trs = table.find_all('tr')

        trs = trs[1:]
        for tr in trs:
            tds = tr.find_all('td')
            name = tds[1].find('a').find('b').get_text()
            hrefs = tds[1].find('div').find_all('a')
            seeds = tds[-2].get_text()
            imgs = tds[1].find_all('img')
            size = tds[-4].get_text()
            audio = True if any([i.get('src').endswith("bgaudio.png") for i in imgs]) else False
            for href in hrefs:
                href = href['href']
                if href.startswith('/download.php'):#must include magnetlink
                    torrent = self.get_torrent(href)
                    data.append(
                    {
                        "name": name, 
                        "magnetlink": torrent.magnet_link if provide_magnet else f"{self.base}{href}", 
                        'seeders': seeds, 
                        'bg_audio': audio,
                        'size': size,
                        'infohash': torrent.info_hash if provide_infohash else None
                    })
        return data
    
    def get_torrent(self,href):
        """
        Fetches a torrent file from the given href and returns a Torrent object.
        Args:
            href (str): The relative URL path to the torrent file.
        Returns:
            Torrent: A Torrent object if the request is successful.
            None: If the request fails or the status code is not 200.
        Raises:
            requests.exceptions.RequestException: If there is an issue with the HTTP request.
        """
        url = f"{self.base}{href}"
        response = self.session.get(url)
        if response.status_code == 200:
            torrent = Torrent.from_string(response.content)
            return torrent
        else:
            print(f"Error: Received status code {response.status_code}")
            return None


   