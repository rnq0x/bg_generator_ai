import json
import queue
import random
import string
import uuid
import requests

from modules.proxy import ProxyManager
from modules.reqwests import RequestsManager


def generate_session_hash(length=11) -> str:
    characters = string.ascii_lowercase + string.digits

    session_hash = ''.join(random.choice(characters) for _ in range(length))
    return session_hash


def req_join_queue(prompt: str, requests_manager: RequestsManager):
    url = "https://andyaii-flux-1-emd.hf.space/queue/join"
    s_hash = generate_session_hash()
    payload = {
        "data": [prompt, random.randint(0, 2147483000), True, 512, 1024, 2],
        "event_data": None,
        "fn_index": 2,
        "trigger_id": 4,
        "session_hash": s_hash
    }
    headers = {
        "accept": "*/*",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://flux-1.ai",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://flux-1.ai/",
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": requests_manager.fake_ua.random
    }

    response = requests_manager.make_request(
        "POST", url, json=payload, headers=headers)
    try:
        if response.json()['event_id']:
            return {
                'event_id': response.json()['event_id'],
                's_hash': s_hash
            }
        else:
            return False
    except Exception as ex:
        print(ex)
        return False
        
        
def req_data_stream(join_dict: dict, requests_manager: RequestsManager):
    url = "https://andyaii-flux-1-emd.hf.space/queue/data"
    querystring = {"session_hash":join_dict['s_hash']}

    payload = ""
    headers = {
        "accept": "text/event-stream",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://flux-1.ai",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://flux-1.ai/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": requests_manager.fake_ua.random
    }

    response = requests_manager.make_request("GET", url, data=payload, headers=headers, params=querystring, stream=True)
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8').strip()
            if decoded_line.startswith('data:'):
                try:
                    data = json.loads(decoded_line[5:])
                    msg = data.get('msg')
                    if msg == 'process_completed':
                        output_data = data.get('output', {}).get('data', [])
                        if output_data:
                            final_url = output_data[0].get('url')
                            break
                except json.JSONDecodeError as e:
                    print(f"JSONDecodeError: {e}")
                except Exception as e:
                    print(f"Error processing line: {e}")
    return final_url


def generate_background(queue: queue.Queue, proxy_manager: ProxyManager, requests_manager: RequestsManager):
    while not queue.empty():
        prompt = queue.get()
        print(f'[V] Запускаю генерацию фото для промпта - {prompt}')
        join_dict = req_join_queue(prompt, requests_manager)

        if not join_dict:
            print('[X] Не удалось получить фото')
            return

        photo_url = req_data_stream(join_dict, requests_manager)
        
        photo = requests_manager.make_request('GET', photo_url)

        if photo and photo.status_code == 200:
            filename = f'output/{uuid.uuid4()}.jpeg'
            with open(filename, 'wb') as f:
                f.write(photo.content)
            print(f'[V] {filename} сохранено')
