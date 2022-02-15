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

#loading all the csv files required for the file
def load_data():
    #users data
    users_df = pd.read_csv(BASE_DIR + "data/user_data.csv")
    users_df = users_df.drop(["Unnamed: 0"],axis=1)

    #moviesdata
    movies_df = pd.read_csv(BASE_DIR+"data/movies_df.csv")
    
    #rating data
    ratings_df = pd.read_csv(BASE_DIR + "data/ratings_df.csv")

    #community data
    communities = None
    with open(BASE_DIR + "data/communityresults.pkl","rb") as f:
        communities = pickle.load(f)

    return users_df,movies_df,ratings_df,communities

#preparing user's data before passing to the users_df
def prepare_user(columns,user_data):
    new_user = dict()
    for col in columns:
        new_user[col] = 0

    user_data['age'] = int(user_data['age'])    
    if 4 < user_data['age'] < 13:
        new_user['Group_Kid'] = 1

    elif 13 < user_data['age'] < 20:
        new_user["Group_Teen"] = 1

    else:
        new_user["Group_Adult"] = 1

    new_user["Occupation_"+user_data['occupation']]=1

    if(user_data['gender']=='male'):
        new_user['Gender_M'] = 1 
    else:
        new_user["Gender_F"] = 1

    return new_user

#getting the cosine similarity values for the new user
def new_user_similarity_results(users_df):
    similarity_matrix = pd.DataFrame(cosine_similarity(users_df), columns= ["user"+str(i) for i in range(len(users_df))]) 
   
    #returning the similarity results for the new user
    return similarity_matrix.loc[len(similarity_matrix)-1].values

#calculate the best community for the user based on the user's cosine similarity results
def calculateBestCommunity(communities,new_user_results):
    avg_per_community = [] * len(communities)
    max_avg = 0
    chosen_community = None

    for community in communities:
        sum = 0
        for user in communities[community]:
            sum = sum + new_user_results[int(user[4:])-1]

        avg = sum / len(communities[community])

        if avg > max_avg:
            chosen_community = community
            max_avg = avg

    return chosen_community

#helper function (for extracting user ids)
def extract(n):
    return int(n[4:])

#fetching the top k movies for the new user
def get_top_k_movies(movies_for_user, k):
    group_movies = movies_for_user.groupby(['movie_title','IMDb_URL'])
    by_rating = group_movies.mean().sort_values('rating',ascending=False).head(k)
    by_popularity = group_movies.sum().sort_values('user_id',ascending=False).head(k)

    return by_rating,by_popularity

#clean the data
def clean_data(df):
    df = df.drop(['Unnamed: 0_y','user_id','rating'],axis=1)
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

#main function
def get_movies(user_data):
    #loading the data
    users_df, movies_df, ratings_df, communities = load_data()
   
    #adding the column attributes for the new user
    new_user = prepare_user(users_df.columns.values, user_data)

    #adding to the users_df and saving it
    users_df = users_df.append(new_user,ignore_index=True)
    users_df.to_csv(BASE_DIR + "data/user_data.csv")

    #fething the similarity results for the new user
    new_user_results = new_user_similarity_results(users_df)

    #retreiving the best community for the user
    chosen_community = calculateBestCommunity(communities,new_user_results)
    
    #extracting the movies of that community
    user_ids = list(map(extract,communities[chosen_community]))
    filtered_ratings = ratings_df[ratings_df['user_id'].isin(user_ids)] 
    movies_for_user = pd.merge(filtered_ratings,movies_df,on="movie_id")

    #removing unwanted columns
    movies_for_user = movies_for_user.drop(['Unnamed: 0_x','movie_id','timestamp','video_release date'],axis=1)

    #getting the top 20 movies categorized by highest ratings and most popular
    by_rating , by_popularity = get_top_k_movies(movies_for_user,20) 

    #cleaning unwanted data before sending response to server
    by_ratings = clean_data(by_rating)
    by_popularity = clean_data(by_popularity)

    #returning the data to the server
    result = {"rating":by_ratings,"popularity":by_popularity}
    print(json.dumps(result))

user_data = {
    "name":sys.argv[1],
    "email":sys.argv[2],
    "age":sys.argv[3],
    "gender":sys.argv[4],
    "occupation":sys.argv[5],
    "country":sys.argv[6]
}
# user_data = {"occupation":"doctor","age":27,"gender":"female"}
get_movies(user_data)