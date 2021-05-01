import io
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
import joblib
from utils.cut import cut_word, rep_invalid_char


class NaiveBayes(object):
    """朴素贝叶斯进行bug问题分类"""

    def __init__(self, title):
        # self.excel_reader = os.path.join(os.path.join(os.path.pardir, 'one_spider'), 'tx.xlsx')
        # 读取excel数据
        # self.excel_reader = 'D:\\分类\\test\\训练数据集合.xls'
        # self.excel_reader2 = 'D:\\分类\\test\\test.xls'
        # 把待预测数据的title和content连接起来进行数据预处理
        # self.data = cut_word([rep_invalid_char(str(title)+str(content))])
        # 发现加上问题内容，精度不高，只对标题进行处理，对英文字母小写化
        self.data = cut_word([rep_invalid_char(str(title.lower()))])

    def predict(self):
        """根据传入的文章标题和内容，预测该文章属于哪一个类别"""
        # 如果本地模型存在，则从本地模型读取，否则重新进入训练过程，训练并保存模型，得出准确率，并输出文章类别
        model = joblib.load('utils/model/train_model.m')
        self.tf = joblib.load('utils/model/tf_model.m')

        data = self.tf.transform(self.data)
        predict = model.predict(data)
        return predict[0]
