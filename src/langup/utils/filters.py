from langup import config
from langup.utils.utils import DFA, singleton


@singleton
class BanWordsFilter(DFA):
    default_path = config.root + 'data/ban_words.txt'

    def __init__(self, file_path_list=None):
        file_path_list = file_path_list or [] + [self.default_path]
        keyword_list = []
        for path in file_path_list:
            keyword_list += [
                line.strip()
                for line in open(file=path, encoding='utf-8', mode='r').readlines()
            ]
        super().__init__(keyword_list)