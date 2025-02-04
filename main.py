

import os
from queue import Queue
import sys
import threading

from modules.config import ConfigManager
from modules.methods import generate_background
from modules.prompt import PromptGenerator
from modules.proxy import ProxyManager
from modules.reqwests import RequestsManager



def main():
    folder_path = 'output'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    print('[!] Проверяю прокси')
    config_manager = ConfigManager()
    proxy = config_manager.get_proxy()
    
    if proxy == 'None':
        print('[X] Не обнаружены прокси в конфигурационном файле')
        sys.exit()
    
    proxy_manager = ProxyManager(config_manager)
    requests_manager = RequestsManager(proxy_manager)
    gen = PromptGenerator()

    task_queue = Queue()

    photos_required = int(input('Введите количество фонов для генерации: '))
    for i in range(photos_required):
        prompt = gen.generate_prompt()
        task_queue.put(prompt)
        # generate_background(prompt, proxy_manager, requests_manager)
    
    requests_manager.create_session()
    
    # Создаем и запускаем потоки
    threads = []
    for _ in range(config_manager.get_threads()):  # 10 потоков
        thread = threading.Thread(target=generate_background, args=(task_queue, proxy_manager, requests_manager,))
        thread.start()
        threads.append(thread)
    
    print('Останавливаю потоки')
    # Останавливаем потоки
    for thread in threads:
        thread.join()
    print('Успешно')

if __name__ == '__main__':
    main()
