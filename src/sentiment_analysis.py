# -*- coding: utf-8 -*-

import text_process as tp
import numpy as np

# 1.读取情感词典和待处理文件
# 情感词典
print("reading...")
sentiment_path = "./Sentiment_dict/"
posdict = tp.read_lines(sentiment_path + "emotion_dict/pos_all_dict.txt")
negdict = tp.read_lines(sentiment_path + "emotion_dict/neg_all_dict.txt")
# 程度副词词典
mostdict = tp.read_lines(sentiment_path + 'degree_dict/most.txt')   # 权值为2
verydict = tp.read_lines(sentiment_path + 'degree_dict/very.txt')   # 权值为1.5
moredict = tp.read_lines(sentiment_path + 'degree_dict/more.txt')   # 权值为1.25
ishdict = tp.read_lines(sentiment_path + 'degree_dict/ish.txt')   # 权值为0.5
insufficientdict = tp.read_lines(sentiment_path + 'degree_dict/insufficiently.txt')  # 权值为0.25
inversedict = tp.read_lines(sentiment_path + 'degree_dict/inverse.txt')  # 权值为-1

# 情感级别
emotion_level1 = "悲伤"
emotion_level2 = "愤怒"
emotion_level3 = "淡定"
emotion_level4 = "平和"
emotion_level5 = "喜悦"
# 情感波动级别
emotion_level6 = "情感波动很小"
emotion_level7 = "情感波动较大"


# 2.程度副词处理，根据程度副词的种类不同乘以不同的权值
def match(word, sentiment_value):
	if word in mostdict:
		sentiment_value *= 2.0
	elif word in verydict:
		sentiment_value *= 1.75
	elif word in moredict:
		sentiment_value *= 1.5
	elif word in ishdict:
		sentiment_value *= 1.2
	elif word in insufficientdict:
		sentiment_value *= 0.5
	elif word in inversedict:
		#print "inversedict", word
		sentiment_value *= -1
	return sentiment_value


# 3.情感得分的最后处理，防止出现负数
# Example: [5, -2] →  [7, 0]; [-4, 8] →  [0, 12]
def transform_to_positive_num(poscount, negcount):
	pos_count = 0
	neg_count = 0
	if poscount < 0 and negcount >= 0:
		neg_count += negcount - poscount
		pos_count = 0
	elif negcount < 0 and poscount >= 0:
		pos_count = poscount - negcount
		neg_count = 0
	elif poscount < 0 and negcount < 0:
		neg_count = -poscount
		pos_count = -negcount
	else:
		pos_count = poscount
		neg_count = negcount
	return (pos_count, neg_count)


# 求单条评论语句的情感倾向总得分
def single_review_sentiment_score(comment_sent):
	single_review_senti_score = []
	cuted_review = tp.cut_sentence(comment_sent)  # 句子切分，单独对每个句子进行分析

	for sent in cuted_review:
		seg_sent = tp.segmentation(sent)   # 分词
		seg_sent = tp.del_stopwords(seg_sent)[:]
		#for w in seg_sent:
		#	print w,
		i = 0    # 记录扫描到的词的位置
		s = 0    # 记录情感词的位置
		poscount = 0    # 记录该分句中的积极情感得分
		negcount = 0    # 记录该分句中的消极情感得分

		for word in seg_sent:   # 逐词分析
			#print word
			if word in posdict:  # 如果是积极情感词
				#print "posword:", word
				poscount += 1   # 积极得分+1
				for w in seg_sent[s:i]:
					poscount = match(w, poscount)
				#print "poscount:", poscount
				s = i + 1  # 记录情感词的位置变化

			elif word in negdict:  # 如果是消极情感词
				#print "negword:", word
				negcount += 1
				for w in seg_sent[s:i]:
					negcount = match(w, negcount)
				#print "negcount:", negcount
				s = i + 1

			# 如果是感叹号，表示已经到本句句尾
			elif word == "！" or word == "!":
				for w2 in seg_sent[::-1]:  # 倒序扫描感叹号前的情感词，发现后权值+2，然后退出循环
					if w2 in posdict:
						poscount += 2
						break
					elif w2 in negdict:
						negcount += 2
						break
			i += 1
		#print "poscount,negcount", poscount, negcount
		single_review_senti_score.append(transform_to_positive_num(poscount, negcount))   # 对得分做最后处理
	pos_result, neg_result = 0, 0   # 分别记录积极情感总得分和消极情感总得分
	for res1, res2 in single_review_senti_score:  # 每个分句循环累加
		pos_result += res1
		neg_result += res2
	#print pos_result, neg_result
	result = pos_result - neg_result   # 该条评论情感的最终得分
	result = round(result, 1)
	return result


# 分析该条新闻中的所有评论，返回一个列表，列表中元素为（分值，评论）元组
def get_score(contents):
	results = []
	results_list = []
	for content in contents:
		content = content.strip()
		if content=="" or content is "NULL":
			continue
		else:
			content=content.replace("#","")
			score = single_review_sentiment_score(content)  # 对每条评论调用函数求得打分
		    #print(score)
			s="["+str(score)+"]"+content
			results.append(s)   # 形成（分数，评论）元组
			results_list.append((score, content))
	return results,results_list


# 求取测试新闻中的正负极性的评论比，正负极性分值的平均值比，正负分数分别的方差
def handel_result(results):
	if len(results)==0:
		return "NULL"
	# 正极性评论数量，负极性评论数量，中性评论数量，正负极性比值
	pos_number, neg_number, mid_number, number_ratio = 0, 0, 0, 0
	# 正极性平均得分，负极性平均得分， 比值
	pos_mean, neg_mean, mean_ratio = 0, 0, 0
	# 正极性得分方差，负极性得分方差
	pos_variance, neg_variance, var_ratio = 0, 0, 0
	pos_list, neg_list, middle_list, total_list = [], [], [], []
	for result in results:
		total_list.append(result[0])
		if result[0] > 0:
			pos_list.append(result[0])   # 正极性分值列表
		elif result[0] < 0:
			neg_list.append(result[0])   # 负极性分值列表
		else:
			middle_list.append(result[0])
	#################################各种评论评论数量统计
	pos_number = len(pos_list)
	neg_number = len(neg_list)
	mid_number = len(middle_list)
	total_number = pos_number + neg_number + mid_number
	#number_ratio = pos_number/neg_number
	pos_number_ratio = round(float(pos_number)/float(total_number), 2)
	neg_number_ratio = round(float(neg_number)/float(total_number), 2)
	mid_number_ratio = round(float(mid_number)/float(total_number), 2)
	text_pos_number = "积极评论条数为 " + str(pos_number) + " 条，占全部评论比例的 %" + str(pos_number_ratio*100)
	text_neg_number = "消极评论条数为 " + str(neg_number) + " 条，占全部评论比例的 %" + str(neg_number_ratio*100)
	text_mid_number = "中性情感评论条数为 " + str(mid_number) + " 条，占全部评论比例的 %" + str(mid_number_ratio*100)
	##################################正负极性平均得分统计
	pos_array = np.array(pos_list)
	neg_array = np.array(neg_list)    # 使用numpy导入，便于计算
	total_array = np.array(total_list)
	if len(pos_array)==0:
		pos_mean=0
	else:
		pos_mean = np.mean(pos_array)
	if len(neg_array)==0:
		neg_mean=0
	else:
		neg_mean = np.mean(neg_array)
	total_mean = np.mean(total_array)   # 求单个列表的平均值
	#mean_ratio = pos_mean/neg_mean
	if pos_mean <= 6:                 # 赋予不同的情感等级
		text_pos_mean = emotion_level4
	else:
		text_pos_mean = emotion_level5
	if neg_mean >= -6:
		text_neg_mean = emotion_level2
	else:
		text_neg_mean = emotion_level1
	if total_mean <= 6 and total_mean >= -6:
		text_total_mean = emotion_level3
	elif total_mean > 6:
		text_total_mean = emotion_level4
	else:
		text_total_mean = emotion_level2
	##################################正负进行方差计算
	pos_variance = np.var(pos_array,axis=0)
	neg_variance = np.var(neg_array,axis=0)
	total_variance = np.var(total_array,axis=0)
	#var_ratio = pos_variance/neg_variance
	#print "pos_variance:", pos_variance, "neg_variance:", neg_variance, "var_ration:", var_ratio
	if total_variance > 10:            # 赋予不同的情感波动级别
		text_total_var = emotion_level7
	else:
		text_total_var = emotion_level6
	################################构成字典返回
	result_dict = ""
	'''
	result_dict['pos_number'] = pos_number   # 正向评论数
	result_dict['neg_number'] = neg_number   # 负向评论数
	result_dict['mid_number'] = mid_number   # 中性评论数
	result_dict['number_ratio'] = round(number_ratio, 1)  # 正负评论数之比，保留一位小数四舍五入
	result_dict['pos_mean'] = round(pos_mean, 1)  # 积极情感平均分
	result_dict['neg_mean'] = round(neg_mean, 1)  # 消极情感平均分
	result_dict['total_mean'] = round(total_mean, 1) # 总的情感平均得分
	result_dict['mean_ratio'] = abs(round(mean_ratio, 1))  # 积极情感平均分/消极情感平均分
	result_dict['pos_variance'] = round(pos_variance, 1)  # 积极得分方差
	result_dict['neg_variance'] = round(neg_variance, 1)  # 消极得分方差
	result_dict['total_variance'] = round(total_variance, 1) # 总的情感得分方差
	result_dict['var_ratio'] = round(var_ratio, 1)  # 积极得分方差/消极得分方差
    '''
	result_dict=result_dict+"text_pos_number:"+str(text_pos_number)+"\r\n"
	result_dict=result_dict+"text_neg_number"+str(text_neg_number)+"\r\n"
	result_dict=result_dict+"text_mid_number"+str(text_mid_number)+"\r\n"
	result_dict=result_dict+"text_pos_mean"+str(text_pos_mean)+"\r\n"
	result_dict=result_dict+"text_neg_mean"+str(text_neg_mean)+"\r\n"
	result_dict=result_dict+"text_total_mean"+str(text_total_mean)+"\r\n"
	result_dict=result_dict+"text_total_var"+str(text_total_var)

	"""
	for key in result_dict.keys():
		print 'key = %s , value = %s ' % (key, result_dict[key])
	"""
	return result_dict

