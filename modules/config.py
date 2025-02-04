import os
import configparser

class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def create_default_config(self):
        """Создает файл конфигурации с дефолтными значениями."""
        self.config['DEFAULT'] = {
            'proxy': 'None',
            'threads': '2'
        }
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def load_config(self):
        """Загружает конфигурацию из файла или создает новый, если файл не существует."""
        if not os.path.exists(self.config_file):
            self.create_default_config()
        else:
            self.config.read(self.config_file)

    def get_proxy(self):
        """Возвращает значение прокси из конфигурации."""
        return self.config['DEFAULT'].get('proxy', 'None')

    def get_threads(self):
        """Возвращает значение количества потоков из конфигурации."""
        return int(self.config['DEFAULT'].get('threads', 'None'))

    def set_proxy(self, proxy):
        """Устанавливает новое значение прокси."""
        self.config['DEFAULT']['proxy'] = proxy
        self.save_config()

    def set_threads(self, threads):
        """Устанавливает новое значение количества потоков."""
        self.config['DEFAULT']['threads'] = str(threads)
        self.save_config()

    def save_config(self):
        """Сохраняет текущую конфигурацию в файл."""
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

if __name__ == "__main__":
    config_manager = ConfigManager()
    print("Прокси:", config_manager.get_proxy())
    print("Потоки:", config_manager.get_threads())