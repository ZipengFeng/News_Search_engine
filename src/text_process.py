# -*- coding: utf-8 -*-

import jieba
import jieba.posseg as pseg
import importlib,sys

# encoding=utf8
print("加载用户词典...")
#jieba.load_userdict('/data/user_dict/pos_dict.txt')
#jieba.load_userdict('/data/user_dict/neg_dict.txt')
sentiment_path = "./Sentiment_dict/"
# 分词，返回List
def segmentation(sentence):
    seg_list = jieba.cut(sentence)
    seg_result = []
    for w in seg_list:
        seg_result.append(w)
    #print seg_result[:]
    return seg_result

# 分词，词性标注，词和词性构成一个元组
def postagger(sentence):
    pos_data = pseg.cut(sentence)
    pos_list = []
    for w in pos_data:
        pos_list.append((w.word, w.flag))
    #print pos_list[:]
    return pos_list

# 句子切分
def cut_sentence(words):
    start = 0
    i = 0
    token = 'meaningless'
    sents = []
    punt_list = ',.!?;~，。！？；～… '
    #print "punc_list", punt_list
    for word in words:
        #print "word", word
        if word not in punt_list:   # 如果不是标点符号
            #print "word1", word
            i += 1
            token = list(words[start:i+2]).pop()
            #print "token:", token
        elif word in punt_list and token in punt_list:  # 处理省略号
            #print "word2", word
            i += 1
            token = list(words[start:i+2]).pop()
            #print "token:", token
        else:
            #print "word3", word
            sents.append(words[start:i+1])   # 断句
            start = i + 1
            i += 1
    if start < len(words):   # 处理最后的部分
        sents.append(words[start:])
    return sents

def read_lines(filename):
    fp = open(filename, 'r',encoding='utf-8')
    lines = []
    for line in fp.readlines():
        line = line.strip()
        lines.append(line)
    fp.close()
    return lines

# 去除停用词
def del_stopwords(seg_sent):
    stopwords = read_lines(sentiment_path + "emotion_dict/stop_words.txt")  # 读取停用词表
    new_sent = []   # 去除停用词后的句子
    for word in seg_sent:
        if word in stopwords:
            continue
        else:
            new_sent.append(word)
    return new_sent

# 获取六种权值的词，根据要求返回list，这个函数是为了配合Django的views下的函数使用
def read_quanzhi(request):
    result_dict = []
    if request == "one":
        result_dict = read_lines(sentiment_path + "degree_dict/most.txt")
    elif request == "two":
        result_dict = read_lines(sentiment_path + "degree_dict/very.txt")
    elif request == "three":
        result_dict = read_lines(sentiment_path + "degree_dict/more.txt")
    elif request == "four":
        result_dict = read_lines(sentiment_path + "degree_dict/ish.txt")
    elif request == "five":
        result_dict = read_lines(sentiment_path + "degree_dict/insufficiently.txt")
    elif request == "six":
        result_dict = read_lines(sentiment_path + "degree_dict/inverse.txt")
    else:
        pass
    return result_dict
