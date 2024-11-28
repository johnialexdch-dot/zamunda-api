from bs4 import BeautifulSoup as bs
from requests import Session
from login_headers import login_headers
class Zamunda:
    def __init__(self) -> None:
        self.session = Session()
        self.base = 'https://zamunda.net'

    def login(self,user,password):
        self.session.get(f'{self.base}/login.php')
        payload = f'username={user}&password={password}'
        self.session.post(f"{self.base}/takelogin.php",headers=login_headers, data=payload)


    def search(self, ss:str, user:str, password:str, provide_magnet:bool=False):
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
            audio = True if any([i.get('src').endswith("bgaudio.png") for i in imgs]) else False
            for href in hrefs:
                href = href['href']
                if href.startswith('/magnetlink'):
                    data.append(
                        {
                            "name": name, 
                            "magnetlink": self.get_download_link(href) if provide_magnet else f"{self.base}{href}", 
                            'seeders': seeds, 
                            'bg_audio': audio
                            })
        return data
    
    def get_download_link(self,href):
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
            