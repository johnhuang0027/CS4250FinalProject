import re
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pymongo import MongoClient

#DB connection
client = MongoClient("mongodb://localhost:27017/")
db = client['biology_research']
faculty_collection = db['faculty']

base_url = "https://www.cpp.edu/sci/biological-sciences/index.shtml"

def fetch_html(url):
    try:
        response = urlopen(url)
        return response.read().decode('utf-8')
    except Exception as e:
        print(f"Not a valid URL")
        return None

def extract_faculty_links(base_html):
    soup = BeautifulSoup(base_html, 'html.parser')
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag['href']
        #URL should match faculty website pattern
        if any(pattern in href for pattern in ["/faculty/index.shtml", "/faculty/lecturers.shtml", "/faculty/emeriti.shtml"]):
            full_url = href if href.startswith("http") else base_url + href
            links.append(full_url)
    return links

#the faculty is still on the same webpage, but we are only interested on the ones with personlized websites     --There should be 19 of them
def extract_faculty_websites(faculty_html):
    soup = BeautifulSoup(faculty_html, 'html.parser')
    faculty_data = []

    #follows same pattern for each card
    for faculty_card in soup.find_all("div", class_="card-body"):
        name_tag = faculty_card.find("h3")
        title_tag = faculty_card.find("div", class_="text-muted")
        website_tag = faculty_card.find("a", title=True)
        
        if name_tag and title_tag and website_tag:
            name = name_tag.get_text(strip=True)
            title = title_tag.get_text(strip=True)
            website_url = website_tag['href']
            
            #adds to list
            faculty_data.append({
                "name": name,
                "title": title,
                "url": website_url
            })
    return faculty_data

#this acts as the main method, calls all other methods
def crawl_faculty_websites(base_url):
    #starts from the base url
    base_html = fetch_html(base_url)
    if not base_html:
        return

    #Since the links to all the faculty are under dropdown menus, we need to get all relevant ones and leave out the rest
    faculty_links = extract_faculty_links(base_html)
    print(f"Found {len(faculty_links)} faculty directory links.")

    for link in faculty_links:
        print(f"Processing: {link}")
        faculty_html = fetch_html(link)
        if not faculty_html:
            continue

        #get faculty website
        faculty_data = extract_faculty_websites(faculty_html)
        print(f"Found {len(faculty_data)} faculty websites.")

        #inserts into db
        for entry in faculty_data:
            if not faculty_collection.find_one({"url": entry["url"]}):  # Avoid duplicates
                faculty_collection.insert_one(entry)
                print(f"Stored: {entry['name']} - {entry['url']}")


crawl_faculty_websites(base_url)
