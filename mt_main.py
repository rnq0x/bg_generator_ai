import asyncio
import json
from queue import Queue
import random
import threading
import time
import uuid
import requests


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


def req_generate_photo(prompt: str):
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


    response = requests.request(
        "POST", url, data=payload, headers=headers, params=querystring)
    return response.json()

def req_get_photo(imageId: str):
    url = "https://image-generation.perchance.org/api/downloadTemporaryImage"

    querystring = {"imageId":imageId}

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

    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    if response.status_code == 404:
        return None
    return response

def generate_background(queue: Queue):
    while not queue.empty():
        prompt = queue.get()
        print(f'[V] Запускаю генерацию фото для промпта - {prompt}')
        gen_object = req_generate_photo(prompt)
        try:
            imageId = gen_object['imageId']
        except Exception as ex:
            print(ex)
            print('[X] Не удалось получить фото')
            queue.task_done()
            continue
        
        photo = req_get_photo(imageId)
        if photo is None:
            queue.task_done()
            continue
        
        with open(f'output/{uuid.uuid4()}.jpeg', 'wb') as f:
            f.write(photo.content)
        
        print(f'[V] {uuid.uuid4()}.jpeg сохранено')
        queue.task_done()
    


def main():
    gen = PromptGenerator()
    photos_required = int(input('Введите количество фонов для генерации: '))
    
    # Создаем очередь задач
    task_queue = Queue()
    for _ in range(photos_required):
        prompt = gen.generate_prompt()
        task_queue.put(prompt)
    
    # Создаем и запускаем потоки
    threads = []
    for _ in range(3):  # 10 потоков
        thread = threading.Thread(target=generate_background, args=(task_queue,))
        thread.start()
        threads.append(thread)
    
    # Ожидаем завершения всех задач
    task_queue.join()
    
    # Останавливаем потоки
    for thread in threads:
        thread.join()
    
    print('Успешно')


if __name__ == '__main__':
    main()
