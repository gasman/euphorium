import requests
from bs4 import BeautifulSoup
import dateutil.parser

from .latest_posts_sidebar import LatestPostsSidebarItem


class DiscussionParticipant(object):
    def __init__(self, soup):
        user_link = soup.find('a', class_='UserLink')
        self.username = user_link.text
        self.user_url = user_link['href']

        self.avatar_url = soup.find('img', class_='ProfilePhoto')['src']

        date_link = soup.find('a', class_='CommentDate')
        self.datetime = dateutil.parser.parse(date_link.time['datetime'])
        self.post_url = date_link['href']

    def __str__(self):
        return self.username

    def __repr__(self):
        return "<DiscussionParticipant: %s>" % str(self)


class Discussion(object):
    def __init__(self, soup):
        self.is_sticky = ('Announcement-Everywhere' in soup['class'])

        title_cell = soup.find('td', class_='DiscussionName')
        title_link = title_cell.find('a', class_='Title')
        self.title = title_link.text
        self.url = title_link['href']

        pager = title_cell.find(class_='MiniPager')
        if pager:
            self.page_count = int(pager.find_all('a')[-1].text)
        else:
            self.page_count = 1

        category_link = title_cell.select_one('.Category > a')
        self.category_name = category_link.text
        self.category_url = category_link['href']

        topic_starter_cell = soup.find('td', class_='FirstUser')
        self.topic_starter = DiscussionParticipant(topic_starter_cell)

        last_poster_cell = soup.find('td', class_='LastUser')
        self.last_poster = DiscussionParticipant(last_poster_cell)

        reply_count_cell = soup.find('td', class_='CountComments')
        reply_count_text = reply_count_cell.span['title'].split()[0]
        self.reply_count = int(reply_count_text.replace(',', ''))

        view_count_cell = soup.find('td', class_='CountViews')
        view_count_text = view_count_cell.span['title'].split()[0]
        self.view_count = int(view_count_text.replace(',', ''))

    def __str__(self):
        return self.title

    def __repr__(self):
        return "<Discussion: %s>" % str(self)


class RecentDiscussionsPage(object):
    def __init__(self, base_url, page_number=1):
        self.url = "%sdiscussions/p%d" % (base_url, page_number)

        soup = self.fetch(self.url)

        pager = soup.find(id='PagerBefore')
        self.max_page_number = int(pager.find_all('a')[-2].text)

        discussions_table = soup.find('table', class_='DiscussionsTable')
        self.discussions = [
            Discussion(row)
            for row in discussions_table.tbody.find_all('tr', class_='Item')
        ]

        self.latest_posts = [
            LatestPostsSidebarItem(item)
            for item in soup.select('#LatestPostList > ul > li')
        ]

    def fetch(self, url):
        r = requests.get(url)
        return BeautifulSoup(r.text, 'html.parser')
