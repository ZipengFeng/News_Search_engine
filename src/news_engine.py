# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:30:40 2015

@author: bitjoy.net
"""

import jieba
import math
import operator
import sqlite3
import configparser
from datetime import *

class SearchEngine:
    stop_words = set()
    
    config_path = ''
    config_encoding = ''
    
    K1 = 0
    B = 0
    N = 0
    AVG_L = 0
    
    conn = None
    
    def __init__(self, config_path, config_encoding):
        self.config_path = config_path
        self.config_encoding = config_encoding
        config = configparser.ConfigParser()
        config.read(config_path, config_encoding)
        f = open(config['DEFAULT']['stop_words_path'], encoding = config['DEFAULT']['stop_words_encoding'])
        words = f.read()
        self.stop_words = set(words.split('\n'))
        self.conn = sqlite3.connect(config['DEFAULT']['db_path'])
        self.K1 = float(config['DEFAULT']['k1'])
        self.B = float(config['DEFAULT']['b'])
        self.N = int(config['DEFAULT']['n'])
        self.AVG_L = float(config['DEFAULT']['avg_l'])
        

    def __del__(self):
        self.conn.close()
    
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
            
    def clean_list(self, seg_list):
        cleaned_dict = {}
        n = 0
        for i in seg_list:
            i = i.strip().lower()
            if i != '' and not self.is_number(i) and i not in self.stop_words:
                n = n + 1
                if i in cleaned_dict:
                    cleaned_dict[i] = cleaned_dict[i] + 1
                else:
                    cleaned_dict[i] = 1
        return n, cleaned_dict

    def fetch_from_db(self, term):
        c = self.conn.cursor()
        c.execute('SELECT * FROM postings WHERE term=?', (term,))
        return(c.fetchone())

    #王琴琴
    def fetch_item_from_db(self, term):
        c = self.conn.cursor()
        term += '%'
        c.execute("SELECT term FROM postings WHERE term like ? ORDER BY df DESC LIMIT 10", (term,))
        return(c.fetchall())
    
    def result_by_BM25(self, sentence):
        seg_list = jieba.lcut(sentence, cut_all=False)
        n, cleaned_dict = self.clean_list(seg_list)
        BM25_scores = {}
        for term in cleaned_dict.keys():
            r = self.fetch_from_db(term)
            if r is None:
                continue
            df = r[1]
            w = math.log2((self.N - df + 0.5) / (df + 0.5))
            docs = r[2].split('\n')
            for doc in docs:
                docid, date_time, tf, ld, comments_num = doc.split('\t')
                docid = int(docid)
                tf = int(tf)
                ld = int(ld)
                s = (self.K1 * tf * w) / (tf + self.K1 * (1 - self.B + self.B * ld / self.AVG_L))
                if docid in BM25_scores:
                    BM25_scores[docid] = BM25_scores[docid] + s
                else:
                    BM25_scores[docid] = s
        BM25_scores = sorted(BM25_scores.items(), key = operator.itemgetter(1))
        BM25_scores.reverse()
        if len(BM25_scores) == 0:
            return 0, [], cleaned_dict
        else:
            return 1, BM25_scores, cleaned_dict
    
    def result_by_time(self, sentence):
        seg_list = jieba.lcut(sentence, cut_all=False)
        n, cleaned_dict = self.clean_list(seg_list)
        time_scores = {}
        for term in cleaned_dict.keys():
            r = self.fetch_from_db(term)
            if r is None:
                continue
            docs = r[2].split('\n')
            for doc in docs:
                docid, date_time, tf, ld, comments_num = doc.split('\t')
                if docid in time_scores:
                    continue
                news_datetime = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
                now_datetime = datetime.now()
                td = now_datetime - news_datetime
                docid = int(docid)
                td = (timedelta.total_seconds(td) / 3600) # hour
                time_scores[docid] = td
        time_scores = sorted(time_scores.items(), key = operator.itemgetter(1))
        if len(time_scores) == 0:
            return 0, [], cleaned_dict
        else:
            return 1, time_scores, cleaned_dict
    
    def result_by_hot(self, sentence):
        seg_list = jieba.lcut(sentence, cut_all=False)
        n, cleaned_dict = self.clean_list(seg_list)
        hot_scores = {}
        for term in cleaned_dict.keys():
            r = self.fetch_from_db(term)
            if r is None:
                continue
            df = r[1]
            w = math.log2((self.N - df + 0.5) / (df + 0.5))
            docs = r[2].split('\n')
            for doc in docs:
                docid, date_time, tf, ld, comments_num = doc.split('\t')
                docid = int(docid)
                tf = int(tf)
                ld = int(ld)
                comments_num = int(comments_num)
                news_datetime = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
                now_datetime = datetime.now()
                td = now_datetime - news_datetime
                BM25_score = (self.K1 * tf * w) / (tf + self.K1 * (1 - self.B + self.B * ld / self.AVG_L))
                td = (timedelta.total_seconds(td) / 3600) # hour
                hot_score = math.log(BM25_score) + 3000 / td + 0.1*comments_num
                # print (str(math.log(BM25_score)),str(3000 / td),str(0.1*comments_num))
                # hot_score = comments_num
                if docid in hot_scores:
                    hot_scores[docid] = hot_scores[docid] + hot_score
                else:
                    hot_scores[docid] = hot_score
        hot_scores = sorted(hot_scores.items(), key = operator.itemgetter(1))
        hot_scores.reverse()
        if len(hot_scores) == 0:
            return 0, [], cleaned_dict
        else:
            return 1, hot_scores, cleaned_dict

    def process_bool(self, seg_list):
        if 'OR' in seg_list:
            return 'OR'
        elif 'AND' in seg_list:
            return 'AND'
        else:
            return False

    def intersection(self, doc1, doc2):
        doc = [val for val in doc1 if val in doc2]
        return doc

    def unionset(self, doc1, doc2):
        return list(doc1.union(doc2))

    def clean(self,clean_list):
        final_list = {}
        for term in clean_list.keys():
            if term.lower() != 'or' and term.lower() != 'and':
                final_list[term] = clean_list[term]
        return final_list

    def result_by_bool(self, sentence):
        seg_list = jieba.lcut(sentence, cut_all=False)
        n, cleaned_dict = self.clean_list(seg_list)
        Bool_results = {}
        docid1 = []
        docid2 = []
        docid = []
        i = 0
        for term in cleaned_dict.keys():
            if term == 'AND':
                print('call')
            if term != 'OR' and term != 'AND':
                r = self.fetch_from_db(term)
                if r is None:
                    continue
                docs = r[2].split('\n')
                for doc in docs:
                    docid, datetime, tf, ld = doc.split('\t')
                    if i == 0:
                        docid1.append(docid)
                    if i == 1:
                        docid2.append(docid)
                i = i + 1
        if self.process_bool(seg_list) == 'AND':
            docid = self.intersection(docid1, docid2)
        docid = self.intersection(docid1, docid2)
        for line in docid:
            Bool_results[line] = 1
        Bool_results = sorted(Bool_results.items(), key=operator.itemgetter(1))
        final_list=self.clean(cleaned_dict)
        if len(Bool_results) == 0:
            return 0, [], final_list
        else:
            return 1, Bool_results, final_list

    def search(self, sentence, sort_type = 0):
        if sort_type == 0:
            return self.result_by_BM25(sentence)
        elif sort_type == 1:
            return self.result_by_time(sentence)
        elif sort_type == 2:
            return self.result_by_hot(sentence)
        elif sort_type == 3:
            return self.result_by_bool(sentence)

if __name__ == "__main__":
    se = SearchEngine('../config.ini', 'utf-8')
    flag, rs = se.search('南京', 0)
    print(rs[:10])
