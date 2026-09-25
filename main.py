from src.tools.tools import web_search, scrape_url

r = web_search.invoke("https://www.reddit.com/r/artificial/")
print(r)