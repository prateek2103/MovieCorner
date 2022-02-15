import json
import sys
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from collections import defaultdict
import os
import re

#Base directory
BASE_DIR = os.getcwd()
BASE_DIR = re.sub(r"\\","/",BASE_DIR)+"/"

def clean_data(df):
    df = df.drop(['Unnamed: 0_x','user_id','movie_id','timestamp','Unnamed: 0_y','rating'],axis=1)
    df_dict = df.to_dict('index')
    movie_list = []

    for item in df_dict:
        movie_dict = dict()
        movie_dict['name'],movie_dict['link'] = item
        movie_dict['genre']=[]
        for more_item in df_dict[item]:
            if(df_dict[item][more_item]!=0.0 or df_dict[item][more_item]!=0):
                movie_dict['genre'].append(more_item)
        
        movie_list.append(movie_dict)

    return movie_list

movies_df = pd.read_csv(BASE_DIR+"data/movies_df.csv")
ratings_df = pd.read_csv(BASE_DIR + "data/ratings_df.csv")
new_df = pd.merge(ratings_df,movies_df,on="movie_id")

popular_movies = new_df.groupby(['movie_title','IMDb_URL']).sum().sort_values(by="user_id",ascending=False).head(50)
movie_list = clean_data(popular_movies)
print(json.dumps({"movie_list":movie_list}))