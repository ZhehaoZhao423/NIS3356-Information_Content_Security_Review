# ContentReview/middleware.py
# import re
# from .sensitive_words import SENSITIVE_WORDS
# from .sensitive_words import load_sensitive_words
import re
from collections import Counter
from .sensitive_words import SensitiveWords
# ContentReview/middleware.py

class Node(object):
    """字典树节点"""

    def __init__(self):
        self.children = None  # dict格式 {u'char1':node1, u'char2':node2...}
        self.sensitive_word = None
        self.sensitive_word_type = None

class TextFilter(object):
    """文本过滤"""

    # Singleton
    _instance = None

    def __new__(cls, *args, **kw):
        """单例模式"""
        if not cls._instance:
            cls._instance = super(TextFilter, cls).__new__(cls, *args, **kw)
        return cls._instance

    def __init__(self):
        self.root = Node()
        self.sensitive_word = SensitiveWords().sensitive_word_dict
        for word_type in self.sensitive_word.keys():
            for word in self.sensitive_word[word_type]:
                self.add_word(word, word_type)

    def add_word(self, word, word_type=u'common'):
        """向字典树里添加敏感词汇及敏感词类型"""
        # 向tire树添加节点
        node = self.root
        for i in range(len(word)):
            if not node.children:  # 该节点是叶节点
                node.children = {word[i]: Node()}
            elif word[i] not in node.children:  # note : 监测dict中是否有某个key, 用 k in d 比用 k in d.keys() 快三倍
                node.children[word[i]] = Node()
            node = node.children[word[i]]
        node.sensitive_word = word  # 在最后一个节点上记录整个词
        node.sensitive_word_type = word_type

    def is_contain(self, message):
        """监测文本是否含有字典树的敏感词
        返回一个列表,每一个元祖都是敏感词(出现在字符串文中的位置,敏感词,类型)"""
        # 初始化结果变量
        result = []
        i, j, message_length = 0, 0, len(message)
        # tire树 查找
        while i < message_length:
            j = i
            p = self.root
            while j < message_length and p.children is not None and message[j] in p.children:  # 匹配最长的词
                p = p.children[message[j]]
                j = j + 1
            if p.sensitive_word:  # 查找时最后落到了敏感词叶节点上
                result.append((j - len(p.sensitive_word),
                               p.sensitive_word,
                               p.sensitive_word_type))
                i += len(p.sensitive_word)  # 直接跳跃到敏感词下一个字符进行继续匹配
            else:
                i += 1
        return result

    def filter(self, message, replace_char=u'*'):
        """过滤文本,将其中的敏感词替换为过滤字符(默认为*)"""
        res = self.is_contain(message)
        for (i, word, _) in res:
            message = message[:i] + u"".join([replace_char for _ in range(len(word))]) + message[i + len(word):]
        return message

    def classifie(self, message):
        """过滤字符串,获取字符串分类及恶意程度"""
        result = []
        # 去除各种标点符号
        message = re.sub("[\s+\.\!\/_,$%^*(+\"\']+|[+——！，。？、~@#￥%……&*（）]+", "", message)
        res = self.is_contain(message)
        # 聚合语句中的敏感词信息及权重
        for _, _, word_type in res:
            result.append(word_type)
        d = dict(Counter(result))
        d = sorted(d.items(), key=lambda x: x[1], reverse=True)
        return d

class SensitiveWordsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # 在中间件初始化时加载敏感词
        # self.sensitive_words = load_sensitive_words('ContentReview/sensitive_words.txt')
        self.textfilter = TextFilter()

    def __call__(self, request):
        if request.method == "POST":
            # 复制 POST 数据，使其可变
            mutable_post = request.POST.copy()

            for key, value in mutable_post.items():
                if isinstance(value, str):
                    mutable_post[key] = self.textfilter.filter(value, replace_char='*')

            # 替换原始不可变 POST 数据
            request.POST = mutable_post

        return self.get_response(request)

    # def censor_content(self, content):
    #     for word in SENSITIVE_WORDS:
    #         pattern = re.compile(re.escape(word), re.IGNORECASE)
    #         content = pattern.sub('**', content)
    #     return content