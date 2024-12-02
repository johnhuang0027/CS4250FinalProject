from bs4 import BeautifulSoup
from pymongo import MongoClient
from urllib.request import urlopen
#from nltk.stem import WordNetLemmatizer

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client['biology_research']
faculty_collection = db['faculty']
terms_collection = db['terms']

# NLTK Setup
#lemmatizer = WordNetLemmatizer()

# Function to fetch HTML from a URL
def fetch_html(url):
    try:
        response = urlopen(url)
        return response.read().decode('utf-8')
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None
    
""" Reads through the p tags, since those are the only ones with the info """
# Function to extract research content from faculty pages
def extract_research_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for the main research container
    research_div = soup.find("div", class_="section-intro")
    if not research_div:
        print("Research content not found in 'section-intro'.")
        return ""
    
    # Collect all text from the nested elements
    research_text = []
    for p_tag in research_div.find_all(["p", "div"], recursive=True):
        text = p_tag.get_text(strip=True)
        if text:
            research_text.append(text)
    
    # Join all the extracted text
    return " ".join(research_text)

# Function to extract, process, and store research terms
#def preprocess_text(text):
#    tokens = text.lower().split()
#    return [lemmatizer.lemmatize(token) for token in tokens if len(token) > 2]

# Function to generate n-grams from tokens
#def generate_Ngrams(tokens, n=1):
#    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def process_faculty_research():
    faculty_entries = list(faculty_collection.find())
    
    # Extract research content
    for faculty in faculty_entries:
        url = faculty['url']
        html = fetch_html(url)
        if not html:
            continue
        
        # Extracting
        research_text = extract_research_content(html)
        if not research_text:
            print(f"No research content found for: {url}")
            continue
        
        faculty_collection.update_one(
            {"_id": faculty["_id"]},
            {"$set": {"research_areas": research_text}}
        )
        print(f"Updated research content for: {faculty['name']}")
'''        
        # Processing
        tokens = preprocess_text(research_text)
        unigrams = generate_Ngrams(tokens, 1)
        bigrams = generate_Ngrams(tokens, 2)
        trigrams = generate_Ngrams(tokens, 3)
        ngrams = unigrams + bigrams + trigrams

        # Inserting
        for term in ngrams:
            if not terms_collection.find_one({"term": term}):  # Avoid duplicates
                terms_collection.insert_one({
                    "term": term,
                    "faculty_id": faculty["_id"],
                    "url": url
                })
                print(f"Stored term: {term} (Faculty: {faculty['name']})")
                
    # Compute TF-IDF
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 3))
    tfidf_matrix = vectorizer.fit_transform(research_texts)
    feature_names = vectorizer.get_feature_names_out()

    # Store TF-IDF results
    for i, faculty_id in enumerate(faculty_ids):
        for term_idx, tfidf_value in enumerate(tfidf_matrix[i].toarray()[0]):
            term = feature_names[term_idx]
            terms_collection.update_one(
                {"term": term, "faculty_id": faculty_id},
                {"$set": {"tfidf": tfidf_value}},
                upsert=True
            )
            
    #TODO: i think we have to rate them and stuff, so that when the user queries, we can return the best professor or whatever
    #so we should probably do another separate file for that. Keep it encapsulated... or smth
'''

if __name__ == "__main__":
    process_faculty_research()
