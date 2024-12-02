
"""
zamunda.py
This module provides a class `Zamunda` 
to interact with the Zamunda website for logging in and searching for torrents.
Classes:
    Zamunda: A class to handle login and search operations on the Zamunda website.
"""
from bs4 import BeautifulSoup as bs
from requests import Session
from login_headers import login_headers

class Zamunda:
    """
    class Zamunda
    A class to handle login and search operations on the Zamunda website.
    """
    def __init__(self) -> None:
        self.session = Session()
        self.base = 'https://zamunda.net'

    def login(self,user,password):
        """
        Logs in to the Zamunda website.
        :param user: The username to log in with.
        :param password: The password to log in with.
        """
        self.session.get(f'{self.base}/login.php')
        payload = f'username={user}&password={password}'
        self.session.post(f"{self.base}/takelogin.php",headers=login_headers, data=payload)


    def search(self, ss:str, user:str, password:str, provide_magnet:bool=False):
        """
        Searches for torrents on the Zamunda website.
        :param ss: The search string to search for.
        :param user: The username to log in with.
        :param password: The password to log in with.
        :param provide_magnet: Whether to provide the magnet link or the download page link.
        """
        self.login(user,password)
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
                # if href.startswith('/magnetlink'):
                data.append(
                    {
                        "name": name, 
                        "magnetlink": self.get_download_link(href) if provide_magnet else f"{self.base}{href}", 
                        'seeders': seeds, 
                        'bg_audio': audio,
                        'size': size
                })
        return data
    def get_download_link(self,href):
        """
        Gets the download link for a torrent.
        :param href: The href to get the download link for.
        """
        url = f"{self.base}{href}"
        response = self.session.get(url)

        if response.status_code != 200:
            print("Error: ",response.status_code)
            return None
        soup = bs(response.text, 'html.parser')

        ass = soup.find_all('a')
        for a in ass:
            content = a.get('href')
            if content and content.startswith('magnet:?'):
                return content
            