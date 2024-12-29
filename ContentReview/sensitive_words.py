# import re

# # 定义一个函数来从文件加载敏感词列表
# def load_sensitive_words(filepath):
#     with open(filepath, 'r', encoding='utf-8') as f:
#         words = f.read().splitlines()
#     return words
#
# # 在需要使用的地方加载敏感词
# SENSITIVE_WORDS = load_sensitive_words('ContentReview/sensitive_words.txt')
#
# def censor_content(content):
#     """
#     审查内容，替换敏感词为**
#     :param content: 用户提交的内容
#     :return: 审查后的内容
#     """
#     for word in SENSITIVE_WORDS:
#         pattern = re.compile(re.escape(word), re.IGNORECASE)
#         content = pattern.sub('**', content)
#     return content


import os

SENSITIVE_WORDS_DATA_PATH = "ContentReview/SensitiveWords/"  # 敏感词数据文件


class SensitiveWords(object):
    # Singleton
    _instance = None

    def __new__(cls, *args, **kw):
        """单例模式"""
        if not cls._instance:
            cls._instance = super(SensitiveWords, cls).__new__(cls, *args, **kw)
        return cls._instance

    def __init__(self):
        """构造函数:读取敏感词文件并初始化字典"""
        global SENSITIVE_WORDS_DATA_PATH
        self.file_name_list = os.listdir(SENSITIVE_WORDS_DATA_PATH)
        self.file_path_list = map(lambda s: SENSITIVE_WORDS_DATA_PATH + s, self.file_name_list)
        self.sensitive_word_dict = {}
        for file_path in self.file_path_list:
            self.get_sensitive_word(file_path)

    def __str__(self):
        """输出敏感词类详细信息"""
        res = "共 " + str(len(self.sensitive_word_dict.keys())) + " 类 (" + ",".join(self.sensitive_word_dict.keys())
        res += ")类敏感词:\n"
        for k in self.sensitive_word_dict.keys():
            res += k + "\t-\t" + str(len(self.sensitive_word_dict[k])) + " 个 \n"
        return res

    def get_sensitive_word(self, path):
        """从文件中读取敏感词(每个一行)"""
        global SENSITIVE_WORDS_DEFAULT_WEIGHT
        with open(path, 'rb') as f:
            sensitive_word_type = str(path).split('/')[-1].replace('.txt', '')
            self.sensitive_word_dict[sensitive_word_type] = []
            for line in f:
                if line.strip():
                    word = line.strip().decode('utf-8')
                self.sensitive_word_dict[sensitive_word_type].append(word)

    def add_sensitive_word(self, word, word_type='default', word_weight='10'):
        """添加敏感词"""
        if type(word) == str:  # str -> unicode
            word = word.decode('utf-8')
        if word_type in self.sensitive_word_dict.keys() or word_type == 'default':
            self.sensitive_word_dict[word_type][word] = word_weight

    def save_data(self):
        """存储数据到文件中(读取地址)"""
        for word_type in self.sensitive_word_dict.keys():
            file_path = filter(lambda x: word_type in x, self.file_path_list)[0]
            with open(file_path, 'wb') as f:
                for word in self.sensitive_word_dict[word_type]:
                    f.write(word.encode("utf-8"))
                    f.write("\n")