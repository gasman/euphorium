from .home_page import HomePage


def scrape(site):
    home_page = HomePage(site.origin_url)
    return home_page
