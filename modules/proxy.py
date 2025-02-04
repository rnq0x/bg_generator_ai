import sys
import requests
import socks
import socket
from modules.config import ConfigManager


class ProxyManager:
    def __init__(self, c_m: ConfigManager):
        self.test_url = "https://httpbin.org/ip"
        self.proxy = c_m.get_proxy()
        
        self._configure_socks_proxy()
        res = self.check_proxy()
        if not res:
            print('[X] Прокси невалид')
            sys.exit()
        else:
            print(f'[V] Прокси валид. IP - {res}')
            
    

    def _configure_socks_proxy(self):
        l_p, i_p = self.proxy.split('@')
        proxy_username, proxy_password = l_p.split(':')
        proxy_host, proxy_port = i_p.split(':')
        
        self.proxies = {
            'http': f'socks5://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}',
            'https': f'socks5://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}',
        }
        
        
    def check_proxy(self):
        try:
            response = requests.get(self.test_url, proxies=self.proxies)
            if response.status_code == 200:
                return response.json()['origin']
            return False
        except:
            return False