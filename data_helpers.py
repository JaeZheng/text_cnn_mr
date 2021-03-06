import numpy as np
import re
import time
import pickle
# import word2vec
from collections import defaultdict, OrderedDict
from tqdm import tqdm
import pandas as pd


data_dir = 'data/rt-polaritydata/'


def clean_str(string):
    """
    Tokenization/string cleaning for all datasets except for SST.
    Original taken from https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " \( ", string)
    string = re.sub(r"\)", " \) ", string)
    string = re.sub(r"\?", " \? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip().lower()


def load_data_and_labels(positive_data_file, negative_data_file):
    """
    Loads MR polarity data from files, splits the data into words and generates labels.
    Returns split sentences and labels.
    """
    # Load data from files
    positive_examples = list(open(positive_data_file, "r", encoding='utf-8').readlines())
    positive_examples = [s.strip() for s in positive_examples]
    negative_examples = list(open(negative_data_file, "r", encoding='utf-8').readlines())
    negative_examples = [s.strip() for s in negative_examples]
    # Split by words
    x_text = positive_examples + negative_examples
    x_text = [clean_str(sent) for sent in x_text]
    # Generate labels
    positive_labels = [[0, 1] for _ in positive_examples]
    negative_labels = [[1, 0] for _ in negative_examples]
    y = np.concatenate([positive_labels, negative_labels], 0)
    return [x_text, y]


def batch_iter(data, batch_size, num_epochs, shuffle=True):
    """
    Generates a batch iterator for a dataset.
    """
    data = np.array(data)
    data_size = len(data)
    num_batches_per_epoch = int((len(data)-1)/batch_size) + 1
    for epoch in range(num_epochs):
        # Shuffle the data at each epoch
        if shuffle:
            shuffle_indices = np.random.permutation(np.arange(data_size))
            shuffled_data = data[shuffle_indices]
        else:
            shuffled_data = data
        for batch_num in range(num_batches_per_epoch):
            start_index = batch_num * batch_size
            end_index = min((batch_num + 1) * batch_size, data_size)
            yield shuffled_data[start_index:end_index]


# 返回格式化时间戳，打印日志用
def format_time():
    """
    返回"年月日时分"格式化时间戳，打印日志和创建文件夹用
    """
    timestamp = time.localtime(time.time())
    fmt_time = str(timestamp.tm_year)
    fmt_time += str(timestamp.tm_mon) if timestamp.tm_mon > 9 else '0' + str(timestamp.tm_mon)
    fmt_time += str(timestamp.tm_mday) if timestamp.tm_mday > 9 else '0' + str(timestamp.tm_mday)
    fmt_time += str(timestamp.tm_hour) if timestamp.tm_hour > 9 else '0' + str(timestamp.tm_hour)
    fmt_time += str(timestamp.tm_min) if timestamp.tm_min > 9 else '0' + str(timestamp.tm_min)
    return fmt_time


# 方式一，编写代码加载word2vec训练好的模型文件GoogleNews-vectors-negative300.bin
def load_binary_vec(fname, vocab):
    word_vecs = {}
    with open(fname, 'rb') as fin:
        header = fin.readline()
        vocab_size, vector_size = list(map(int, header.split()))
        binary_len = np.dtype(np.float32).itemsize * vector_size
        # vectors = []
        for i in tqdm(range(vocab_size)):
            # read word
            word = b''
            while True:
                ch = fin.read(1)
                if ch == b' ':
                    break
                word += ch
            # print(str(word))
            word = word.decode(encoding='ISO-8859-1')
            if word in vocab:
                word_vecs[word] = np.fromstring(fin.read(binary_len), dtype=np.float32)
            else:
                fin.read(binary_len)
            # vector = np.fromstring(fin.read(binary_len), dtype=np.float32)
            # vectors.append(vector)
            # if include:
            #     vectors[i] = unitvec(vector)
            fin.read(1)  # newline
        return word_vecs


# load MR data —— Movie reviews with one sentence per review.
# Classification involves detecting positive/negative reviews
def load_data_k_cv(folder, cv=10, clear_flag=True):
    pos_file = folder[0]
    neg_file = folder[1]

    # 训练集的语料词汇表,计数
    word_cab = defaultdict(float)
    revs = [] # 最后的数据
    with open(pos_file,'rb') as pos_f:
        for line in pos_f:
            rev = []
            rev.append(line.decode(encoding='ISO-8859-1').strip())
            if clear_flag:
                orign_rev = clean_str(" ".join(rev))
            else:
                orign_rev = " ".join(rev).lower()
            words = set(orign_rev.split())
            for word in words:
                word_cab[word] += 1
            datum = {"y": 1,
                     "text": orign_rev,
                     "num_words": len(orign_rev.split()),
                     "spilt": np.random.randint(0, cv)}
            revs.append(datum)

    with open(neg_file,'rb') as neg_f:
        for line in neg_f:
            rev = []
            rev.append(line.decode(encoding='ISO-8859-1').strip())
            if clear_flag:
                orign_rev = clean_str(" ".join(rev))
            else:
                orign_rev = " ".join(rev).lower()
            words = set(orign_rev.split())
            for word in words:
                word_cab[word] += 1
            datum = {"y": 0,
                     "text": orign_rev,
                     "num_words": len(orign_rev.split()),
                     "spilt": np.random.randint(0, cv)}
            revs.append(datum)

    return word_cab, revs


def add_unexist_word_vec(w2v, vocab):
    """
    将词汇表中没有embedding的词初始化()
    :param w2v:经过word2vec训练好的词向量
    :param vocab:总体要embedding的词汇表
    """
    for word in vocab:
        if word not in w2v and vocab[word]>=1:
            w2v[word] = np.random.uniform(-0.25,0.25,300)


def get_vec_by_sentence_list(word_vecs, sentence_list, maxlen=56, values=0.,vec_size = 300):
    """
    :param sentence_list:句子列表
    :return:句子对应的矩阵向量表示
    """
    data = []

    for sentence in sentence_list:
        # get a sentence
        sentence_vec = []
        words = sentence.split()
        for word in words:
            sentence_vec.append(word_vecs[word].tolist())

        # padding sentence vector to maxlen(w * h)
        sentence_vec = pad_sentences(sentence_vec,maxlen,values,vec_size)
        # add a sentence vector
        data.append(np.array(sentence_vec))
    return data


def get_index_by_sentence_list(word_ids, sentence_list, maxlen=56):
    indexs = []
    words_length = len(word_ids)
    for sentence in sentence_list:
        # get a sentence
        sentence_indexs = []
        words = sentence.split()
        for word in words:
            sentence_indexs.append(word_ids[word])
        # padding sentence to maxlen
        length = len(sentence_indexs)
        if length < maxlen:
            for i in range(maxlen - length):
                sentence_indexs.append(words_length)
        # add a sentence vector
        indexs.append(sentence_indexs)

    return np.array(indexs)


def pad_sentences(data, max_len=56, values=0., vec_size=300):
    """padding to max length
    :param data:要扩展的数据集
    :param maxlen:扩展的h长度
    :param values:默认的值
    """
    length = len(data)
    if length < max_len:
        for i in range(max_len - length):
            data.append(np.array([values]*vec_size))
    return data


def get_train_test_data1(word_vecs, revs, cv_id=0,sent_length=56, default_values=0., vec_size = 300):
    """
    获取的训练数据和测试数据是直接的数据
    :param revs:
    :param cv_id:
    :param sent_length:
    :return:
    """
    data_set_df = pd.DataFrame(revs)

    # DataFrame
    # y text num_words spilt
    # 1 'I like this movie' 4 3
    data_set_df = data_set_df.sample(frac=1)#打乱顺序

    data_set_cv_train = data_set_df[data_set_df['spilt'] != cv_id]  # 训练集
    data_set_cv_test = data_set_df[data_set_df['spilt'] == cv_id] #测试集

    # train
    train_y_1 = np.array(data_set_cv_train['y'].tolist(),dtype='int')
    train_y_2 = list(map(get_contrast,train_y_1))
    train_y = np.array([train_y_1,train_y_2]).T

    test_y_1 = np.array(data_set_cv_test['y'].tolist(),dtype='int')
    test_y_2 = list(map(get_contrast,test_y_1))
    test_y = np.array([test_y_1,test_y_2]).T

    train_sentence_list = data_set_cv_train['text'].tolist()
    test_sentence_list = data_set_cv_test['text'].tolist()

    train_x = get_vec_by_sentence_list(word_vecs,train_sentence_list,sent_length,default_values,vec_size)
    test_x = get_vec_by_sentence_list(word_vecs,test_sentence_list,sent_length,default_values,vec_size)

    return train_x, train_y, test_x, test_y


def get_train_test_data2(word_ids, revs, cv_id=0, sent_length=56):
    data_set_df = pd.DataFrame(revs)

    # DataFrame
    # y text num_words spilt
    # 1 'I like this movie' 4 3
    data_set_df = data_set_df.sample(frac=1)  # 打乱顺序

    data_set_cv_train = data_set_df[data_set_df['spilt'] != cv_id]  # 训练集
    data_set_cv_test = data_set_df[data_set_df['spilt'] == cv_id]  # 测试集

    # train
    train_y_1 = np.array(data_set_cv_train['y'].tolist(), dtype='int')
    train_y_2 = list(map(get_contrast, train_y_1))
    train_y = np.array([train_y_1, train_y_2]).T

    test_y_1 = np.array(data_set_cv_test['y'].tolist(), dtype='int')
    test_y_2 = list(map(get_contrast, test_y_1))
    test_y = np.array([test_y_1, test_y_2]).T

    train_sentence_list = data_set_cv_train['text'].tolist()
    test_sentence_list = data_set_cv_test['text'].tolist()

    train_x = get_index_by_sentence_list(word_ids,train_sentence_list,sent_length)
    test_x = get_index_by_sentence_list(word_ids,test_sentence_list,sent_length)

    return train_x, train_y, test_x, test_y


# 对0，1取反
def get_contrast(x):
    return 2+~x


def getWordsVect(W):
    word_ids = OrderedDict()
    W_list = []
    count = 0
    for word,vector in W.items():
        W_list.append(vector.tolist())
        word_ids[word] = count
        count = count + 1
    W_list.append([0.0]*300)
    return word_ids, W_list


if __name__ == '__main__':
    # Testing --------------------------------------------------------------------------
    data_folder = ['data/rt-polaritydata/rt-polarity.pos', 'data/rt-polaritydata/rt-polarity.neg']
    w2v_file = 'data/GoogleNews-vectors-negative300.bin'
    print('load data ...')
    word_cab, revs = load_data_k_cv(data_folder)
    print('data loaded !!!')
    print('number of sentences: ' + str(len(revs)))
    print('size of vocab: ' + str(len(word_cab)))
    sentence_max_len = np.max(pd.DataFrame(revs)['num_words'])
    print('dataset the sentence max length is {}'.format(sentence_max_len))

    print('load word2vec vectors...')
    word_vecs = load_binary_vec(w2v_file,word_cab)
    print (len(list(word_vecs.keys())))
    print('finish word2vec load !!!')

    # 对未登录词操作
    add_unexist_word_vec(word_vecs, word_cab)

    # CNN-rand对应的词向量表
    word_vecs_rand = {}
    add_unexist_word_vec(word_vecs_rand, word_cab)

    # 将数据数据集对应的词向量保存好
    pickle.dump([word_vecs_rand, word_vecs, word_cab, sentence_max_len, revs], open('data/word_vec.p', 'wb'))
    pass
