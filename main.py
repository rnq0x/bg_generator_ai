import asyncio
import json
from pathlib import Path
import random
import time
import uuid
import requests
import os
import socks
import socket
import urllib3

urllib3.disable_warnings()

class PromptGenerator():
    datasets = {
        'objects': None,
        'adjs': None,
        'colors': None,
        'verbs': None
    }

    def __init__(self):
        self.datasets = {
            'objects': self.load_objects_from_dataset(),
            'adjs': self.load_adjs_from_dataset(),
            'colors': self.load_colors_from_dataset(),
            'verbs': self.load_verbs_from_dataset()
        }

    def load_objects_from_dataset(self):
        with open('datasets/objects.json') as f:
            dataset = json.load(f)
            return dataset['objects']

    def load_adjs_from_dataset(self):
        with open('datasets/adjs.json') as f:
            dataset = json.load(f)
            return dataset['adjs']

    def load_colors_from_dataset(self):
        with open('datasets/colors.json') as f:
            dataset = json.load(f)
            ds_colors = []
            for color in dataset['colors']:
                ds_colors.append(color['color'])
            return ds_colors

    def load_verbs_from_dataset(self):
        with open('datasets/verbs.json') as f:
            dataset = json.load(f)
            ds_verbs = []
            for verb in dataset['verbs']:
                choiced_time = random.choice(['present', 'past'])
                ds_verbs.append(verb[choiced_time])
            return ds_verbs

    def generate_prompt(self) -> str:
        components = [
            f"{random.choice(self.datasets['adjs'])} {random.choice(self.datasets['objects'])}",
            f"{random.choice(self.datasets['verbs'])}",
            f"color palette: {random.choice(self.datasets['colors'])}",
            "trending on ArtStation, 4K resolution"
        ]
        return ", ".join(components)

# Добавляем класс для работы с прокси


class ProxyManager:
    def __init__(self):
        self.proxy_file = 'proxylist.txt'
        self.proxy_url = 'https://proxyleet.com/proxy/type=socks5&speed=200&key=e8b228425086fbdfdb5d91d21a1b9693'
        self.proxies = []
        self.working_proxies = []
        self.timeout = 10
        self.test_url = "https://httpbin.org/ip"

        # Скачиваем актуальный прокси-лист при инициализации
        self.download_proxy_list()
        self.load_proxies()

    def download_proxy_list(self):
        try:
            response = requests.get(self.proxy_url, timeout=15, verify=False)
            response.raise_for_status()

            # Сохраняем свежие прокси
            with open(self.proxy_file, 'w') as f:
                f.write(response.text)

            print(
                f"[✓] Прокси-лист успешно обновлен ({len(response.text.splitlines())} записей)")

        except Exception as e:
            print(f"[!] Ошибка при загрузке прокси-листа: {str(e)}")
            if not Path(self.proxy_file).exists():
                raise SystemExit(
                    "[X] Нет локальной копии прокси-листа. Программа завершена.")

    def load_proxies(self):
        try:
            with open(self.proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]

            # Фильтрация невалидных записей
            self.proxies = [p for p in self.proxies if self.is_valid_proxy(p)]

            if not self.proxies:
                raise ValueError("Нет валидных прокси в файле")

            print(f"[✓] Загружено {len(self.proxies)} прокси")

        except Exception as e:
            print(f"[!] Ошибка загрузки прокси: {str(e)}")
            raise SystemExit("[X] Критическая ошибка. Программа завершена.")

    def is_valid_proxy(self, proxy: str) -> bool:
        parts = proxy.split(':')
        if len(parts) not in [2, 4]:
            return False
        if not parts[1].isdigit():
            return False
        return True

    def check_proxy(self, proxy):
        try:
            # Устанавливаем прокси
            proxy_parts = proxy.split(':')
            if len(proxy_parts) == 2:
                host, port = proxy_parts
                socks.set_default_proxy(socks.SOCKS5, host, int(port))
                socket.socket = socks.socksocket
            else:
                raise ValueError(
                    "Некорректный формат прокси. Ожидается host:port")

            # Проверяем соединение через прокси
            response = requests.get(self.test_url, timeout=self.timeout, verify=False)
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"[!] Ошибка при проверке прокси {proxy}: {str(e)}")
            return False
        finally:
            socks.set_default_proxy()
            socket.socket = socket.socket
        return False

    def get_random_proxy(self):
        if not self.working_proxies:
            print("[~] Проверяем рабочие прокси...")
            for proxy in self.proxies:
                if self.check_proxy(proxy):
                    self.working_proxies.append(proxy)
            if not self.working_proxies:
                print("[!] Не найдено рабочих прокси")
                return None
        return random.choice(self.working_proxies)


# Модифицируем функции запросов
def make_request(method, url, proxy_manager, **kwargs):
    max_retries = 3
    for _ in range(max_retries):
        proxy = proxy_manager.get_random_proxy()
        if not proxy:
            return None

        proxy_url = f"socks5://{proxy}"
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                proxies=proxies,
                timeout=60,
                verify=False,
                **kwargs
            )
            if response.status_code == 200:
                return response
        except Exception as e:
            print(f"[!] Ошибка при использовании прокси {proxy}: {str(e)}")
            if proxy in proxy_manager.working_proxies:
                proxy_manager.working_proxies.remove(proxy)
    return None


def req_generate_photo(prompt: str, proxy_manager):
    url = "https://image-generation.perchance.org/api/generate"

    querystring = {"prompt": prompt, "seed": -1, "resolution": "512x768", "guidanceScale": "7", "negativePrompt": "bad lighting, low-quality, deformed, text, poorly drawn, holding camera, bad art, bad angle, boring, low-resolution, worst quality, bad composition, disfigured",
                   "channel": "ai-text-to-image-generator", "subChannel": "public", "userKey": "69df24aca2df0a4789fd320447708a5c4d1cb617e63c281a15dc256966096ff9", "adAccessCode": "", "requestId": random.uniform(0, 1), "__cacheBust": random.uniform(0, 1)}

    payload = ""
    headers = {
        "accept": "*/*",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "content-length": "0",
        "cookie": "_ga_YJWJRNESS5=GS1.1.1738624648.1.0.1738624648.60.0.0; _ga=GA1.2.184378698.1738624649; _gid=GA1.2.967970531.1738624649; _gat_gtag_UA_36798824_24=1",
        "origin": "https://image-generation.perchance.org",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://image-generation.perchance.org/embed",
        "sec-ch-ua": 'Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": 'macOS',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }

    response = make_request("POST", url, proxy_manager,
                            headers=headers, params=querystring)
    return response.json() if response else None


def req_get_photo(imageId: str, proxy_manager):
    url = "https://image-generation.perchance.org/api/downloadTemporaryImage"

    querystring = {"imageId": imageId}

    payload = ""
    headers = {
        "accept": "*/*",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "cookie": "_ga_YJWJRNESS5=GS1.1.1738624648.1.0.1738624648.60.0.0; _ga=GA1.2.184378698.1738624649; _gid=GA1.2.967970531.1738624649; _gat_gtag_UA_36798824_24=1",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://image-generation.perchance.org/embed",
        "sec-ch-ua": 'Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": 'macOS',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }

    response = requests.request(
        "GET", url, data=payload, headers=headers, params=querystring)
    if response.status_code == 404:
        return None
    response = make_request("GET", url, proxy_manager,
                            params={"imageId": imageId})
    return response if response else None


def generate_background(prompt: str, proxy_manager):
    print(f'[V] Запускаю генерацию фото для промпта - {prompt}')
    gen_object = req_generate_photo(prompt, proxy_manager)

    if not gen_object or 'imageId' not in gen_object:
        print('[X] Не удалось получить фото')
        return

    photo = req_get_photo(gen_object['imageId'], proxy_manager)

    if photo and photo.status_code == 200:
        filename = f'output/{uuid.uuid4()}.jpeg'
        with open(filename, 'wb') as f:
            f.write(photo.content)
        print(f'[V] {filename} сохранено')


def main():
    folder_path = 'output'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    proxy_manager = ProxyManager()
    gen = PromptGenerator()

    photos_required = int(input('Введите количество фонов для генерации: '))
    for i in range(photos_required):
        prompt = gen.generate_prompt()
        generate_background(prompt, proxy_manager)

    print('Успешно')


if __name__ == '__main__':
    main()
