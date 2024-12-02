import re
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
#import numpy as np

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client['biology_research']
faculty_collection = db['faculty']

# Function fetches faculty research content and metadata from MongoDB.
def fetch_faculty_data():
    faculty_entries = list(faculty_collection.find({"research_areas": {"$exists": True, "$ne": ""}}))
    research_texts = [entry["research_areas"] for entry in faculty_entries]
    metadata = [{"name": entry["name"], "url": entry["url"]} for entry in faculty_entries]
    return research_texts, metadata

# Function ranks based on cosine similarity between query & research content
def rank_faculty(query, research_texts, metadata):
    # Compute TF-IDF for research content
    vectorizer = TfidfVectorizer(
        stop_words="english", 
        ngram_range=(1, 3),
        min_df=1,   # Consider terms that appear in at least 1 document
        max_features=5000,  # Limit vocabulary size
        sublinear_tf=True   # Scale term frequencies
    )
    
    # Fit the vectorizer
    tfidf_matrix = vectorizer.fit_transform(research_texts)
    
    # Debugging: Print the feature names
    print("TF-IDF Feature Names:")
    print(vectorizer.get_feature_names_out())

    # Transform the query into a TF-IDF vector
    query_vector = vectorizer.transform([query])

    # Compute cosine similarity between query and documents
    scores = cosine_similarity(query_vector, tfidf_matrix).flatten()
    
    def highlight_snippet(text, query):
        terms = re.split(r'\W+', query.lower())
        for term in terms:
            text = re.sub(f"({term})", r"**\1**", text, flags=re.IGNORECASE)
        return text[:200]

    # Update snippet generation in `rank_faculty`
    ranked_results = [
        {"name": meta["name"], "url": meta["url"], "score": score, "snippet": highlight_snippet(text, query)}
        for meta, text, score in zip(metadata, research_texts, scores)
    ]

    # Combine scores with metadata
    ranked_results = [
        {"name": meta["name"], "url": meta["url"], "score": score, "snippet": text[:200]}
        for meta, text, score in zip(metadata, research_texts, scores)
    ]

    # Sort results by descending score
    ranked_results.sort(key=lambda x: -x["score"])
    return ranked_results

# Function displays ranked search results with pagination
def display_results(query, page=1, results_per_page=5):
    # Fetch data from MongoDB
    research_texts, metadata = fetch_faculty_data()

    # Rank results
    ranked_results = rank_faculty(query, research_texts, metadata)

    # Pagination
    start = (page - 1) * results_per_page
    end = start + results_per_page
    paginated_results = ranked_results[start:end]

    # Display results
    print(f"\nResults for query: \"{query}\" (Page {page})")
    if not paginated_results:
        print("No results found.")
        return

    for result in paginated_results:
        print(f"Faculty: {result['name']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['snippet']}...")
        print(f"Relevance Score: {result['score']:.4f}")
        print("-" * 50)

# Main Search Function
if __name__ == "__main__":
    while True:
        print("\nEnter a query to search for faculty research (or type 'exit' to quit):")
        user_query = input("> ").strip()
        if user_query.lower() == "exit":
            break

        print("Enter the page number to view results:")
        try:
            page_number = int(input("> "))
        except ValueError:
            print("Invalid page number. Defaulting to page 1.")
            page_number = 1

        display_results(user_query, page=page_number)