import random
import requests
from fake_useragent import UserAgent

from modules.proxy import ProxyManager


class RequestsManager():
    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
        self.fake_ua: UserAgent  = UserAgent()
        self.session = None

    def create_session(self):
        self.session = None
        self.session = requests.Session()
        return True
    
    def make_request(self, method, url, **kwargs):
        response = self.session.request(
            method=method,
            url=url,
            proxies=self.proxy_manager.proxies,
            timeout=60,
            **kwargs
        )
        if response.status_code == 200:
            return response

    
        
