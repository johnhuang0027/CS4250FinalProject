import re
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pymongo import MongoClient
import nltk
nltk.download('wordnet')    #downloads a set of stop words so we dont have to do it manually, i think
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

client = MongoClient("mongodb://localhost:27017/")
db = client['biology_research']
faculty_collection = db['faculty']
terms_collection = db['terms']

# NLTK Setup
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))

def fetch_html(url):
    try:
        response = urlopen(url)
        return response.read().decode('utf-8')
    except Exception as e:
        print(f"Not a valid URL")
        return None

#reads through the p tags, since those are the only ones with the info
def extract_research_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    content_div = soup.find("div", {"class": "section-intro"})
    if content_div:
        return content_div.get_text(strip=True)
    return ""

def preprocess_text(text):
    tokens = re.findall(r'\b\w+\b', text.lower())
    filtered_tokens = [
        lemmatizer.lemmatize(word) for word in tokens if word not in stop_words and len(word) > 2       #hopefully we dont have to do it manually
    ]
    return filtered_tokens

def generate_Ngrams(tokens, n=1):
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def process_faculty_research():
    faculty_entries = list(faculty_collection.find())
    for faculty in faculty_entries:
        url = faculty['url']
        html = fetch_html(url)
        if not html:
            continue
        
        #extracting
        research_text = extract_research_content(html)
        if not research_text:
            continue
        
        #processing
        tokens = preprocess_text(research_text)
        unigrams = generate_Ngrams(tokens, 1)
        bigrams = generate_Ngrams(tokens, 2)
        trigrams = generate_Ngrams(tokens, 3)
        ngrams = unigrams+bigrams+trigrams

        #inserting
        for term in ngrams:
            if not terms_collection.find_one({"term": term}):  # Avoid duplicates
                terms_collection.insert_one({
                    "term": term,
                    "faculty_id": faculty["_id"],
                    "url": url
                })
                print(f"Stored term: {term} (Faculty: {faculty['name']})")

    #TODO: i think we have to rate them and stuff, so that when the user queries, we can return the best professor or whatever
    #so we should probably do another separate file for that. Keep it encapsulated... or smth


if __name__ == "__main__":
    process_faculty_research()
