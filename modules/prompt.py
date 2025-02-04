import json
import random


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