# -*- coding: utf-8 -*-
"""Copy of HW.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1z1jEtNcX4rLxthT3qF31nNX3CqHblYte
"""

import numpy as np
import pandas as pd
import torch
import zipfile

# if this link does not work please get a new one from: https://www.kaggle.com/datasets/fabiochiusano/medium-articles
!wget -cO - "https://storage.googleapis.com/kaggle-data-sets/2123951/3531703/bundle/archive.zip?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kaggle-161607.iam.gserviceaccount.com%2F20220620%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20220620T103753Z&X-Goog-Expires=259199&X-Goog-SignedHeaders=host&X-Goog-Signature=93ce3874b529b38a9c4cdeb5ca19729ed6dc480b1696f636127d24b0d481c99a27cac48f47dc8718e19c549b095ba783a9acdf8e4885448e020a429ddd3eff71880b173c13b71a87df4174a4781f0b4ce3fcfd99314b9532832666c390511d70c57dab072efe378bdf3f606c5001511f997c8bbec84dd9317b3fd4c3f3a152ffd66485dd891bbd85fc0946c0af36c6156563dcfc76c928827b1edc4f904f46e8a165370faf4ab7f7894a99d9c9189166d305ec16de2489b50dba2ef40096b3c53012b9e767e52f758bd5faff0d50525286d46353fb67448a28dce4797178e60aae4472bbaac131887e9c6032b9e1b0503331a8200f8477ebf1b9656d0ca77153" > data.zip

unzipped = zipfile.ZipFile('data.zip') 
for file in unzipped.namelist():
     unzipped.extract(file, 'data')

data = pd.read_csv('/content/data/medium_articles.csv')
data = data.iloc[:20000, :][['text', 'tags']]
data.head()

import nltk
nltk.download('stopwords')
nltk.download('wordnet')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
ps = PorterStemmer()
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

import re
import string
def process_data(text):
    text = text.lower()
    text = re.sub('https:\/\/\S+', ' ', text) 
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text) 
    text = re.sub(r'[^ \w\.]', ' ', text) 
    text = re.sub('\w*\d\w*', ' ', text)
    temp = [ps.stem(w) for w in text.split() if not w.lower() in stop_words]
    test = ''
    for word in temp:
      test += word + ' '
    return test

def find_class(tags):
  tags = tags.split(',')
  sample = list()
  for text in tags:

    text = text.lower()
    text = re.sub('https:\/\/\S+', ' ', text) 
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text) 
    text = re.sub(r'[^ \w\.]', ' ', text) 
    text = re.sub('\w*\d\w*', ' ', text)
    sample.append(text)
  sample = [word for word in sample if not word.lower() in stop_words]
  return sample

data['text'] = data.text.apply(lambda x: process_data(x))
data['tags'] = data.tags.apply(lambda x: find_class(x))
data.head()

#count occurance of each tag in data
tag_occurance = dict()

#set for diffrent tags
tag_set = set()

for i in range(len(data)):
  for tag in data.iloc[i]['tags']:
    tag_set.add(tag)

all_tags = [tag for tags_list in data["tags"] for tag in tags_list]

for tag in tag_set:
  tag_occurance.update({tag:all_tags.count(tag)})

new_tags = list()
for i in range(len(data)):
  temp = list()
  for tag in data.iloc[i]['tags']:
    if tag_occurance[tag] > 3:
      temp.append(tag)
  new_tags.append(temp)
data['tags'] = new_tags

# find new diffrent tags
new_tags = set()
for i in range(len(data)):
  for cat in data.iloc[i]['tags']:
    new_tags.add(cat)
len(new_tags)

temp = list()
for i in range(len(data)):
  temp.append(len(data.iloc[i]['tags']))

data['len'] = temp
data = data[data['len'] != 0]
data.drop('len', axis = 1, inplace = True)
data.head()

!pip install --upgrade transformers
from transformers import AutoTokenizer, BertModel
tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')

bert = BertModel.from_pretrained('bert-base-uncased', output_hidden_states = True)

bert.eval()

for i in range(len(data)):
  data.iloc[i]['tags'].sort(key = len)

encoded_tags = list()
tag_set = set()
for tag in new_tags:
    id = tokenizer.convert_tokens_to_ids(tokenizer.tokenize(tag))
    encoded_tags.append(id)
    if len(id)> 0:
      tag_set.add(tag)
new_tags = tag_set
del tag_set

encoded_tags = [id for id in encoded_tags if len(id)>0]

max_len = max([len(tag) for tag in encoded_tags])

temp_encoded_tags = list()
mask = list()
for i in range(len(encoded_tags)):
  temp = list()
  temp_mask = list()
  for j in range(max_len):
    if j < len(encoded_tags[i]):
      temp.append(encoded_tags[i][j])
      temp_mask.append(1)
    else:
      temp.append(0)
      temp_mask.append(0)
  temp_encoded_tags.append(temp)
  mask.append(temp_mask)

tags = pd.DataFrame()
tags['tag'] = temp_encoded_tags
tags['mask'] = mask
tags.head()

tokens_tensor = torch.tensor(tags['tag'].values[..., np.newaxis].tolist())
segments_tensors = torch.tensor(tags['mask'].values[..., np.newaxis].tolist())

ebmed_features = list()
for i in range(len(tokens_tensor)):
  with torch.no_grad():
      output_embedding = np.squeeze(bert(tokens_tensor[i], segments_tensors[i])[2][0].cpu().detach().numpy().flatten())
      ebmed_features.append(output_embedding)

ebmed_features = np.array(ebmed_features)
ebmed_features.shape

from sklearn.cluster import KMeans

kmeans = KMeans(n_clusters=100, random_state=0).fit(ebmed_features)
clu = kmeans.predict(ebmed_features)

del ebmed_features
temp = list()
for tag in new_tags:
  temp.append(tag)
tags.drop('mask', axis=1, inplace=True)
tags['tokens'] = temp
tags['cluster'] = clu
del clu

clu = list()
for i in range(len(data)):
  temp = list()
  for tag in data.iloc[i]['tags']:
    t = tags[tags['tokens']==tag]['cluster'].values
    if len(t)>0:
      temp.append(t)
  clu.append(temp)
data['Class'] = clu
data.head()

temp = [len(i) for i in data.Class.values]
data['tag-len'] = temp
data = data[data['tag-len'] != 0]
data.drop('tag-len', axis=1, inplace=True)

def unique(List):
    return max(set(List), key = List.count)

temp = list()
for i in range(len(data)):
  temp.append(unique([i for [i] in data.iloc[i, -1]]))
data['unique_class'] = temp
data.head()

data['unique_class'].nunique()

data.drop([ 'Class', 'tags'], axis = 1, inplace = True)
data.head()

"""## Tokenize"""

# tokenize features 
MAX_LEN = 1000
tokenized_text = tokenizer.batch_encode_plus(
                            # Sentences to encode
                            data.text.values.tolist(), 
                            # Add '[CLS]' and '[SEP]'
                            add_special_tokens = True,
                            # Add empty tokens if len(text)<MAX_LEN
                            padding = 'max_length',
                            # Truncate all sentences to max length
                            truncation=True,
                            # Set the maximum length
                            max_length = MAX_LEN, 
                            # Return attention mask
                            return_attention_mask = True,
                            # Return pytorch tensors
                            return_tensors = 'tf')

data['tokenized_text'] = [i for i in tokenized_text['input_ids'].numpy()]
data.drop('text', axis = 1, inplace = True)
data.head()

"""## Train Test Split"""

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

train_data , test_data = train_test_split(data, test_size = 0.2, random_state = 42)
train_data, val_data = train_test_split(train_data, test_size = 0.2, random_state = 42)

train_data.head()

import tensorflow as tf
from tensorflow.keras.layers import Embedding, LSTM, Dense, Flatten

train_label = tf.one_hot(train_data.unique_class.values.tolist(),  100)
val_label = tf.one_hot(val_data.unique_class.values.tolist(), 100)
test_label = tf.one_hot(test_data.unique_class.values.tolist(), 100)

train_data = tf.cast(train_data.tokenized_text.values.tolist(), tf.float32)
val_data = tf.cast(val_data.tokenized_text.values.tolist(), tf.float32)
test_data = tf.cast(test_data.tokenized_text.values.tolist(), tf.float32)

print(len(tokenizer))

model = tf.keras.Sequential()
model.add(Embedding(input_dim = 30522, output_dim = 256))
model.add(LSTM(512, return_sequences= True))
model.add(LSTM(256, return_sequences= True))
model.add(LSTM(128, return_sequences= False))
model.add(Dense(100, 'softmax'))

opt = tf.keras.optimizers.Adam(learning_rate=1e-3)
model.compile(optimizer=opt, loss= 'categorical_crossentropy', metrics='acc')
model.fit(train_data, train_label, validation_split=0.2, epochs=15, batch_size=64)

import matplotlib.pyplot as plt
t , = plt.plot(model.history.history['acc'])
v, = plt.plot(model.history.history['val_acc'])
plt.legend([t, v], ['Train', 'Validation'])