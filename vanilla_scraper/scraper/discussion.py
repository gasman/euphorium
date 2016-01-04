import requests
from bs4 import BeautifulSoup
import dateutil.parser

from .latest_posts_sidebar import LatestPostsSidebarItem


class Message(object):
    def __init__(self, soup):
        self.text = soup.text  # temp!


class Discussion(object):
    def __init__(self, soup):
        self.id = soup['id']
        header = soup.find(class_='DiscussionHeader')
        author_element = header.find(class_='Author')
        author_link = author_element.find('a', class_='Username')

        self.author_username = author_link.text
        self.author_url = author_link['href']
        self.author_id = self.author_url.split('/')[-2]
        self.avatar_url = author_element.find('img', class_='ProfilePhoto')['src']

        date_element = header.find(class_='DateCreated')
        self.datetime = dateutil.parser.parse(date_element.a.time['datetime'])

        self.message = Message(soup.find(class_='Message'))


class Comment(object):
    def __init__(self, soup):
        self.id = soup['id']
        header = soup.find(class_='CommentHeader')
        author_element = header.find(class_='Author')
        author_link = author_element.find('a', class_='Username')

        self.author_username = author_link.text
        self.author_url = author_link['href']
        self.author_id = self.author_url.split('/')[-2]
        self.avatar_url = author_element.find('img', class_='ProfilePhoto')['src']

        date_element = header.find(class_='DateCreated')
        self.datetime = dateutil.parser.parse(date_element.a.time['datetime'])

        self.message = Message(soup.find(class_='Message'))


class DiscussionPage(object):
    def __init__(self, base_url, discussion_id, slug, page_number=1):
        self.url = "%sdiscussion/%s/%s/p%d" % (
            base_url, discussion_id, slug, page_number
        )

        soup = self.fetch(self.url)

        self.title = soup.select_one('.PageTitle h1').text

        self.posts = []

        for discussion_element in soup.find_all(class_='ItemDiscussion'):
            self.posts.append(Discussion(discussion_element))

        for comment_element in soup.find_all(class_='ItemComment'):
            self.posts.append(Comment(comment_element))

        pager = soup.find(id='PagerBefore')
        if pager:
            self.max_page_number = int(pager.find_all('a')[-2].text)
        else:
            self.max_page_number = 1

        self.latest_posts = [
            LatestPostsSidebarItem(item)
            for item in soup.select('#LatestPostList > ul > li')
        ]

    def fetch(self, url):
        r = requests.get(url)
        return BeautifulSoup(r.text, 'html5lib')
