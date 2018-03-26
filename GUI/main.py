#!congding = utf-8
import sys
sys.path.append('../src')
from flask import Flask, render_template, request, jsonify
from news_engine import SearchEngine
import xml.etree.ElementTree as ET
import sqlite3
import configparser
import time
import re

import jieba

app = Flask(__name__)

doc_dir_path = ''
db_path = ''
global page
global keys


def init():
    config = configparser.ConfigParser()
    config.read('../config.ini', 'utf-8')
    global dir_path, db_path
    dir_path = config['DEFAULT']['sorted_doc_dir_path']
    db_path = config['DEFAULT']['db_path']


@app.route('/')
def main():
    init()
    return render_template('search.html', error=True, hot_news=True)


# 读取表单数据，获得doc_ID
@app.route('/search/', methods=['POST'])
def search():

    try:
        global keys
        global checked
        checked = ['checked="true"', '', '']
        keys = request.form['key_word']
        #print(keys)
        if keys not in ['']:
            start_time = time.clock()

            flag,page = searchidlist(keys)
            if flag==0:   # 代表无结果，返回查询无结果的页面
                return render_template('search.html', error=False, hot_news=False)
            docs = cut_page(page, 0)

            end_time = time.clock()
            time_used = round((end_time - start_time),3)
            
            return render_template('high_search.html', checked=checked, key=keys, docs=docs, page=page,
                                   error=True, hot_news=False, time_used=time_used)
        else:
            return render_template('search.html', error=False, hot_news=False)

    except:
        print('search error')


def searchidlist(key, selected=0):
    global page
    global doc_id
    global cleaned_dict
    se = SearchEngine('../config.ini', 'utf-8')
    flag, id_scores, cleaned_dict = se.search(key, selected) # selected值用来指定排序方式
    # 返回docid列表
    doc_id = [i for i, s in id_scores]
    page = []
    for i in range(1, (len(doc_id) // 10 + 2)):
        page.append(i)
    page = page[:32]
    return flag,page


def cut_page(page, no):
    docs = find(doc_id[no*10:page[no]*10])
    return docs


# 将需要的数据以字典形式打包传递给search函数
def find(docid, extra=False):
    docs = []
    global dir_path, db_path
    for id in docid:
        print(dir_path + '%s.xml',id)
        root = ET.parse(dir_path + '%s.xml' % id).getroot()
        url = root.find('url').text
        title = root.find('title').text
        body = root.find('body').text
        snippet = root.find('selected_snippet').text
        snippet = snippet.replace("\t","").replace("\r","").replace("\n","").replace(" ","")
        time = root.find('datetime').text.split(' ')[0]
        datetime = root.find('datetime').text
        comments_result = root.find('comments_result').text
        if comments_result == "NULL":
            comment_show = ["休息一下~","暂时没有评论"]
            comments_dict = ["没有评论~","当然也就没有分析了233333"]
        else:
            comments_dict = root.find('comments_dict').text
            comment_list = comments_result.split('\n')
            comment_show = comment_list[:5]
            comment_ana = comments_dict.split('\n')
            comment_analysis = comment_ana[:3]
            comments_dict = []
            for i in comment_analysis:
                tmp  = i.split('r')[1]
                comments_dict.append(tmp)
            comments_dict[0] = comments_dict[0][1:]
        
        snippet_new=""
        body_seg = re.split(u"。|？|！|#|，|……|~|；|：|～|,", body)
        ct=0
        #print(body_seg)
        for istr in body_seg:
            for term in cleaned_dict.keys():
                if term in istr:
                    snippet_new = snippet_new + istr + "……"
                    add = True
                    ct=ct+1
                    break
            if ct==5:
                break
        doc = {'url': url, 'title': title, 'snippet': snippet_new, 'preview': snippet, 'datetime': datetime, 'time': time, 'body': body,
               'id': id, 'extra': [], 'comment_show':comment_show, 'comment_analysis':comments_dict}
        if extra:
            temp_doc = get_k_nearest(db_path, id)
            for i in temp_doc:
                root = ET.parse(dir_path + '%s.xml' % i).getroot()
                title = root.find('title').text
                doc['extra'].append({'id': i, 'title': title})
        docs.append(doc)
    return docs

@app.route('/search/page/<page_no>/', methods=['GET'])
def next_page(page_no):
    try:
        page_no = int(page_no)
        docs = cut_page(page, (page_no-1))
        return render_template('high_search.html', checked=checked, key=keys, docs=docs, page=page,
                               error=True, hot_news=False)
    except:
        print('next error')

@app.route('/search/<key>/', methods=['POST'])
def high_search(key):
    try:
        selected = int(request.form['order'])
        for i in range(3):
            if i == selected:
                checked[i] = 'checked="true"'
            else:
                checked[i] = ''
        flag,page = searchidlist(key, selected)
        if flag==0:
            return render_template('search.html', error=False, hot_news=False)
        docs = cut_page(page, 0)
        return render_template('high_search.html',checked=checked ,key=keys, docs=docs, page=page,
                               error=True, hot_news=False)
    except:
        print('high search error')


@app.route('/search/<id>/', methods=['GET', 'POST'])
def content(id):
    try:
        doc = find([id], extra=True)
        return render_template('content.html', doc=doc[0])
    except:
        print('content error')


def get_k_nearest(db_path, docid, k=5):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM knearest WHERE id=?", (docid,))
    docs = c.fetchone()
    #print(docs)
    conn.close()
    return docs[1: 1 + (k if k < 5 else 5)]  # max = 5

#王琴琴
@app.route('/hint', methods = ['GET', 'POST'])
def hint():
    if request.method == 'GET':
        keyword = request.args.get('keyword')
    else:
        keyword = request.json.get('keyword')
    se = SearchEngine('../config.ini', 'utf-8')
    terms = [t[0] for t in se.fetch_item_from_db(keyword)]
    if terms:
        print(terms)
        return jsonify(terms)
    return jsonify(list())


if __name__ == '__main__':
    jieba.initialize()
    app.run(host='127.0.0.1', port=2333)
