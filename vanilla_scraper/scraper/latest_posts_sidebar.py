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
