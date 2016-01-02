import requests
from bs4 import BeautifulSoup
import dateutil.parser


class CategoryLatestPost(object):
    def __init__(self, soup):
        title_link = soup.find('a', class_='LatestPostTitle')
        self.title = title_link['title']
        self.url = title_link['href']

        user_link = soup.find('a', class_='UserLink')
        self.author_username = user_link.text
        self.author_url = user_link['href']

        self.avatar_url = soup.find('img', class_='ProfilePhoto')['src']

        date_link = soup.find('a', class_='CommentDate')
        self.datetime = dateutil.parser.parse(date_link.time['datetime'])

    def __str__(self):
        return self.title

    def __repr__(self):
        return "<CategoryLatestPost: %s>" % str(self)


class Category(object):
    def __init__(self, soup):
        name_cell = soup.find('td', class_='CategoryName')
        self.url = name_cell.h3.a['href']
        self.name = name_cell.h3.text

        discussion_count_cell = soup.find('td', class_='CountDiscussions')
        discussion_count_text = discussion_count_cell.span['title'].split()[0]
        self.discussion_count = int(discussion_count_text.replace(',', ''))

        comment_count_cell = soup.find('td', class_='CountComments')
        comment_count_text = comment_count_cell.span['title'].split()[0]
        self.comment_count = int(comment_count_text.replace(',', ''))

        latest_post_cell = soup.find('td', class_='LatestPost')
        self.latest_post = CategoryLatestPost(latest_post_cell)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Category: %s>" % str(self)


class CategoryGroup(object):
    def __init__(self, soup):
        self.id = soup['id']
        self.name = soup.h2.text
        self.categories = [
            Category(item)
            for item in soup.table.tbody.find_all('tr', class_='Item')
        ]

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<CategoryGroup: %s>" % str(self)


class LatestPostsSidebarItem(object):
    def __init__(self, soup):
        title_link = soup.find('a', class_='PostTitle')
        self.title = title_link.text
        self.url = title_link['href']

        author_link = soup.find('a', class_='PostAuthor')
        self.author_username = author_link.text
        self.author_url = author_link['href']

        self.datetime_text = soup.find('span', class_='PostDate').text

    def __str__(self):
        return self.title

    def __repr__(self):
        return "<LatestPostsSidebarItem: %s>" % str(self)


class HomePage(object):
    def __init__(self, url):
        soup = self.fetch(url)
        self.category_groups = [
            CategoryGroup(item)
            for item in soup.find_all(class_='CategoryGroup')
        ]
        self.latest_posts = [
            LatestPostsSidebarItem(item)
            for item in soup.select('#LatestPostList > ul > li')
        ]

    def fetch(self, url):
        r = requests.get(url)
        return BeautifulSoup(r.text, 'html.parser')
