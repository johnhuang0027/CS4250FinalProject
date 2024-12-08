from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from bson import ObjectId  # Import ObjectId for MongoDB queries

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client['biology_research']
faculty_collection = db['faculty']
terms_collection = db['terms']


def fetch_faculty_data():
    try:
        faculty_entries = list(faculty_collection.find())
        if not faculty_entries:
            raise ValueError("No faculty data found in the database.")

        research_texts = []
        metadata = []

        for faculty in faculty_entries:
            # Convert the faculty _id to ObjectId for comparison
            faculty_id = faculty["_id"]

            # Fetch all terms associated with this faculty
            terms = list(terms_collection.find({"faculty_id": ObjectId(faculty_id)}))  # Correctly match ObjectId
            if terms:
                term_text = " ".join(term["term"] for term in terms)
                research_texts.append(term_text)
                metadata.append({"name": faculty.get("name", "Unknown"), "url": faculty.get("url", "#")})
            else:
                print(f"Warning: No terms found for faculty ID {faculty_id}")

        return research_texts, metadata
    except Exception as e:
        print(f"Error fetching faculty data: {e}")
        return [], []


# Rank faculty based on cosine similarity between query and research content
def rank_faculty(query, research_texts, metadata):
    try:
        if not research_texts:
            print("No research texts available for ranking.")
            return []

        vectorizer = TfidfVectorizer(
            stop_words="english", 
            ngram_range=(1, 3),
            min_df=1,
            max_features=5000,
            sublinear_tf=True
        )
        
        tfidf_matrix = vectorizer.fit_transform(research_texts)
        query_vector = vectorizer.transform([query])
        scores = cosine_similarity(query_vector, tfidf_matrix).flatten()

        def highlight_snippet(text, query):
            terms = re.split(r'\W+', query.lower())
            for term in terms:
                text = re.sub(f"({re.escape(term)})", r"**\1**", text, flags=re.IGNORECASE)
            return text[:200]

        ranked_results = [
            {
                "name": meta["name"],
                "url": meta["url"],
                "score": score,
                "snippet": highlight_snippet(text, query)
            }
            for meta, text, score in zip(metadata, research_texts, scores)
        ]

        ranked_results.sort(key=lambda x: -x["score"])
        return ranked_results
    except Exception as e:
        print(f"Error ranking faculty data: {e}")
        return []

# Display ranked search results with pagination
def display_results(query, page=1, results_per_page=5):
    research_texts, metadata = fetch_faculty_data()

    if not research_texts:
        print("No research texts found. Ensure terms are correctly processed and stored in the database.")
        return

    ranked_results = rank_faculty(query, research_texts, metadata)

    if not ranked_results:
        print("No relevant results found for the query.")
        return

    start = (page - 1) * results_per_page
    end = start + results_per_page
    paginated_results = ranked_results[start:end]

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
