import re
import jieba


def cut_word(data:list):
    """
    进行中文分词
    :param data: 待分词的数据，列表类型
    :return: 分词后的数据，列表类型
    """
    res = []
    jieba.load_userdict("utils/dict.txt")
    for s in data:

        word_cut = ' '.join(list(jieba.cut(s.lower().strip())))
        res.append(word_cut)
    return res


def rep_invalid_char(old:str):
    """只保留字符串中的大小写字母，数字，汉字"""
    invalid_char_re = r"[^0-9A-Za-z\u4e00-\u9fa5]"
    return re.sub(invalid_char_re, "", old)
