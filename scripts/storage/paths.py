import os


def get_data_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
