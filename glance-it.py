import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
from bs4 import BeautifulSoup as bs
import requests
from streamlit_lottie import st_lottie
import re
from time import sleep

#******************************************************************************************************************
                                            #STREAMLIT SECTION
#********************************************************************************************************************
# Import logo animation from lotties
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


lottie_chart = load_lottieurl('https://assets3.lottiefiles.com/packages/lf20_kzbhn4td.json')
st_lottie(lottie_chart, speed=1, height=100, key="initial")

#Title column alignment manipulation
row0_spacer1, row0_1, row0_spacer2, row0_2  = st.columns((1.8,2.8,.2,5.3))
row0_1.title('GLANCE-IT ')

row0_1.markdown(':sunglasses:***_Your movie review at a glance_***:sunglasses:')
#with row0_1:
    #st.write('___')

row1_spacer1, row1_1, row1_spacer2 = st.columns((.1,7.3,.1))

with row1_1:

    st.write("""**Hello!** Welcome to **_Glance-it_!**. This app scrapes few  reviews of your favorite movie from imdb 
                (but do not store the data) and gives you nice graphs. The app lets you know (base on users review) if you
                if a movie worth your time and money. Also, the app shows how many users find the movie **_Ineteresting_**, **_Cool_**, 
                **_Not Cool_** or **_Boring_**.   """)
    st.markdown("**PS:** the reviews are based on individual's view about the movie and their opinions may not be final ")
    st.write("___")

#**************************************************************************
row2_spacer1, row2_1, row2_spacer2 = st.columns((3,7.3,3))

with row2_1:
    
    title = st.text_input("Search movie title", value= "red sparrow",max_chars=30, help="Clear the default title...Enter movie title and press ENTER")



st.write("**Reviews for the movie :  **", title)
st.write("___")


#SCRAPING AND DATA PROCESSING
#*************************************************************************

# This function loads the key in our text file as list
def get_keys ():
    '''Load pagination keys from a text file '''
    f = open("IMDB_key_a.txt", "r")
    key = f.read()
    f.close()
    items = key.split(',')
    return items
#Extract keys
keys=[i for i in get_keys()]
key = keys[0:5]

#Grab user movie title to search for
def join_string(string):
    '''Returns title entered by user'''
    user_query =string.split(' ')
    user_string=' '.join(user_query)
    return user_string

#Search user_query using IMDB search tool and
#Get the movie link to extract movie code
def get_movie_code():
    '''This method return movie code of movie title entered by user'''
    search_url = requests.get('https://www.imdb.com/find?q='+join_string(title))
    soup_search = bs(search_url.content)
    #soup_search.status_code == 200
        
    for item in soup_search:
        link= list(soup_search.find('td', class_="result_text").a['href'][7:-1])
        link_w = ''.join(link)
            
        if link_w.startswith('tt', 0, 2):
            return str(link_w)
        else:
            return 'Movie not found. Try another movie title \nEnter correct movie Title'
    

#Getting reviews from landing page
@st.cache
def get_review ():
    title_ = []
    text_ = []
    ratings =  []
    
    url = 'https://www.imdb.com/title/'+get_movie_code()+'/reviews'
    review_url = requests.get(url)
    #if (review_url.status_code == 200):
        
    soup_review = bs(review_url.content)

    content = soup_review.find('div', class_="lister-list")

    for titles in content.find_all('a', class_='title'):
        title = titles.get_text()
        title_.append(title)

    for texts  in content.find_all('div', class_="text show-more__control"):
        text = texts.get_text(separator=' ', strip=True)
        text_.append(text)

    for rating  in content.find_all('span',class_="rating-other-user-rating" ):
        rating_ = rating.get_text(separator=' ',strip=True)
        ratings.append(rating_[0:2])
    
    data = {'Title': title_, 'Review': text_, 'Ratings': ratings}
    return data

df_1 = pd.concat([pd.Series(v, name=k) for k, v in get_review().items()], axis=1)

#Getting paginated reviews
@st.cache(suppress_st_warning = True)
def get_review_paginated ():
    title_ = []
    text_ = []
    ratings =  []
    
    
    for x in key:
            url2 = 'https://www.imdb.com/title/'+get_movie_code()+'/reviews/_ajax?ref_=undefined&paginationKey='+x
            
            review_url2 = requests.get(url2)
            sleep(0.2)
            #if (review_url2.status_code==200):
            soup_review2 = bs(review_url2.content)

            content2 = soup_review2.find('div', class_="lister-list") #review-container

            for titles2 in content2.find_all('a', class_='title'):
                title2 = titles2.get_text()
                title_.append(title2)

            for texts2  in content2.find_all('div', class_="text show-more__control"):
                text2 = texts2.get_text(separator=' ', strip=True)
                text_.append(text2)

            for rating2  in content2.find_all('span',class_="rating-other-user-rating" ):
                rating_2 = rating2.get_text(separator=' ',strip=True)
                ratings.append(rating_2[0:2])
                
    data = {'Title': title_, 'Review': text_, 'Ratings': ratings}
    return data

df_2 = pd.concat([pd.Series(v, name=k) for k, v in get_review_paginated().items()], axis=1)

#Merge data from landing page review and paginated reviews
main_df = pd.concat([df_1, df_2], ignore_index = True)
#Remove duplicates and drop empty rows
main_df = main_df.dropna().drop_duplicates()
#Reset index
main_df=main_df.reset_index(drop=True)
#remove next line character
main_df.replace(r'\n',' ', regex=True, inplace=True) 

# LABEL RATING AS INTERESTING (8-10)...COOL (5-7)...NOT COOL (3-4)...OR BORING (1-2)
def recommender (word):
   
    if int(word) >= 8 :
        return "Interesting"  
    elif int(word) >= 5 and int(word) < 8 :
        return "Cool"
    elif int(word) >= 3 and int(word) < 5 :
        return "Not Cool"   
    else :
        return "Boring"

main_df ['Recommendation'] = main_df['Ratings'].apply(lambda x: recommender(x))

# ADD SIDEBAR
add_selectbox = st.sidebar.selectbox(
    "What would you like to see?",
    ("Recommendation", "Ratings", "Wordcloud","Table")
)

if add_selectbox == "Recommendation":
    st.write("**_Recommendation base on review_**")
        ## BAR CHART for Recommendation
    labels = main_df['Recommendation'].unique()
    colors = sns.color_palette("Set2") #choosing color

    fig, ax = plt.subplots(figsize=(10,4)) 
    wedges = ax.bar(x=main_df['Recommendation'].unique(), height=main_df["Recommendation"].value_counts(), width=0.8, color= colors)

        #ax.legend(wedges, labels,
            # title="Recommendation",
            # loc="center left",
                #bbox_to_anchor=(1, 0, 1, 1.5))

        #plt.ylim(10, 120,20)
        #plt.xlabel("Recommendations")    plt.ylabel("Count")
        #plt.title("Recommendation base on review")
        #plt.xticks(rotation=45)
    plt.show()
    st.pyplot(fig)
    st.write("___")

if add_selectbox == "Ratings":
    st.write("**_Rating Distribution_**")
    labels = main_df['Ratings'].unique()

    fig1, ax1 = plt.subplots(figsize=(4,4))

    colors = sns.color_palette("bright") #choosing color

    wedges, texts, autotexts = ax1.pie(main_df.Ratings.value_counts(), autopct='%1.1f%%',wedgeprops = { 'linewidth' : 1, 'edgecolor' : 'white' },
                shadow=False, startangle=180, pctdistance=0.7, radius=1.0, colors=colors)

    ax1.legend(wedges, labels,
            title="Ratings",
            loc="center left",
            bbox_to_anchor=(1, -0.5, 1, 2.0))

    plt.setp(autotexts, size=10, weight="bold")


    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        #plt.title("Ratings Distribution")
    plt.show()
    st.pyplot(fig1)

if add_selectbox == "Wordcloud":
    st.write("**_Frequent words mentioned in review title_**")
    text = main_df['Title'].values

    stopwords = set(STOPWORDS)
    stopwords.add('film thus')
    stopwords.add("movie")

    fig2, ax2 = plt.subplots(figsize=(4,4))
    ax2 = WordCloud(width=400, height=200, max_words=25, stopwords=stopwords, random_state=20).generate(str(text).lower())
    
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.imshow(ax2)
    #plt.title('Popular words in Title')
    st.pyplot(fig2)


if add_selectbox == "Table":
    df = main_df.head(10)
    st.write("**Top ten reviews**")
    st.dataframe(df)


