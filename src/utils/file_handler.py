# src/utils/file_handler.py

import os

class FileHandler:
    @staticmethod
    def read_file(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        return content

    @staticmethod
    def write_file(file_path, content):
        with open(file_path, 'w') as file:
            file.write(content)

    @staticmethod
    def append_to_file(file_path, content):
        with open(file_path, 'a') as file:
            file.write(content)

    @staticmethod
    def delete_file(file_path):
        if os.path.exists(file_path):
            os.remove(file_path)

    @staticmethod
    def file_exists(file_path):
        return os.path.exists(file_path)