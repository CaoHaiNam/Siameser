import unicodedata
import numpy as np
import Utils
import Parameters
import CRF
import tensorflow as tf
import keras
import json
from sentence_transformers import SentenceTransformer
import os
# import normalize_vietnamese_typing


class Siameser:
    def __init__(self, model_name, ranking_level=None):
        print('Load model')
        if model_name == 'AD':
            self.model = tf.keras.models.load_model(Parameters.AD_MODEL_FILE)
        elif model_name == 'Add':
            self.model = tf.keras.models.load_model(Parameters.Add_MODEL_FILE)
        elif model_name == 'Merge':
            self.model = tf.keras.models.load_model(Parameters.Merge_MODEL_FILE)
        elif model_name == 'ElementWise':
            self.model = tf.keras.models.load_model(Parameters.ElementWise_MODEL_FILE)
        
        print("Load sentence embedding model (If this is the first time you run this repo, It could be take time to download sentence embedding model)")
        # self.labse_model, self.labse_layer = LaBSE.get_model(model_url, max_seq_length)
        if os.path.isdir(Parameters.local_embedding_model):
            self.embedding_model = SentenceTransformer(Parameters.local_embedding_model)
        else:
            self.embedding_model = SentenceTransformer(Parameters.embedding_model)
            self.embedding_model.save(Parameters.local_embedding_model)

        print('Load standard address')
        with open(file=Parameters.NORM_ADDS_FILE, mode='r', encoding='utf-8') as f:
            self.NORM_ADDS = json.load(fp=f)
        
        if ranking_level == 'ward':
            print('Load standard address matrix')
            with open(Parameters.Ward_STD_EMBEDDING_FILE, 'rb') as f:
                self.std_embeddings = np.load(f)
                self.NT_std_embeddings = np.load(f)
            
            with open(file=Parameters.Ward_ID2id_FILE, mode='r', encoding='utf-8') as f:
                self.ID2id = json.load(fp=f)
        else:
            print('Load standard address matrix')
            with open(Parameters.STD_EMBEDDING_FILE, 'rb') as f:
                self.std_embeddings = np.load(f)
                self.NT_std_embeddings = np.load(f)
            # with open('Data/norm.npy', 'rb') as f:
            #     self.std_embeddings = np.load(f)[:34481]
            # with open('Data/NT_norm.npy', 'rb') as f:
            #     self.NT_std_embeddings = np.load(f)[:34481]

            
            with open(file=Parameters.ID2id_FILE, mode='r', encoding='utf-8') as f:
                self.ID2id = json.load(fp=f)

        self.num_of_norm = len(self.ID2id)        
        print('Done')

    def encode(self, input_text):
        return self.embedding_model.encode(input_text)

    def standardize(self, raw_add):  
        raw_add = unicodedata.normalize('NFC', raw_add)
        raw_ent_vector = Utils.gen_entity_vector_from_raw_add(raw_add)
        raw_add = Utils.remove_punctuation(CRF.get_better_add(raw_add)).lower()
        raw_add_vector = Utils.concat(np.array(self.encode([raw_add])), raw_ent_vector).reshape(Parameters.dim,)
        raw_add_vectors = np.full((self.num_of_norm, Parameters.dim), raw_add_vector)

        if raw_add == Utils.remove_tone_of_text(raw_add):
            x = self.model.predict([raw_add_vectors, self.NT_std_embeddings]).reshape(self.num_of_norm,)
        else:
            x = self.model.predict([raw_add_vectors, self.std_embeddings]).reshape(self.num_of_norm,)

        # print(x)
        x = np.argmax(x, axis=0)
        id = str(self.ID2id[str(x)])
        return self.NORM_ADDS[id]['std_add']

    def get_top_k(self, raw_add, k):  
        # raw_add = normalize_vietnamese_typing.chuan_hoa_dau_cau_tieng_viet(raw_add)
        raw_add = unicodedata.normalize('NFC', raw_add)
        raw_ent_vector = Utils.gen_entity_vector_from_raw_add(raw_add)
        raw_add = Utils.remove_punctuation(CRF.get_better_add(raw_add)).lower()
        raw_add_vector = Utils.concat(np.array(self.encode([raw_add])), raw_ent_vector).reshape(Parameters.dim,)
        raw_add_vectors = np.full((self.num_of_norm, Parameters.dim), raw_add_vector)

        if raw_add == Utils.remove_tone_of_text(raw_add):
            x = self.model.predict([raw_add_vectors, self.NT_std_embeddings]).reshape(self.num_of_norm,)
        else:
            x = self.model.predict([raw_add_vectors, self.std_embeddings]).reshape(self.num_of_norm,)

        # print(x)
        top_k = x.argsort()[-k:][::-1]
        # print(top_k)
        top_std_adds = []
        for i in top_k:
            id = str(self.ID2id[str(i)])
            top_std_adds.append(self.NORM_ADDS[id]['std_add'])
        return top_std_adds

