import re

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import dateutil.parser

from .latest_posts_sidebar import LatestPostsSidebarItem


def test_string_node(node, output_document):
    if type(node) is NavigableString:
        # EXACT comparison to the NavigableString class so that comments etc
        # (which are subclasses of NavigableString) don't count
        return str(node)


def test_br(node, output_document):
    if isinstance(node, Tag) and node.name == 'br':
        return output_document.new_tag('br')


def test_emoticon(node, output_document):
    try:
        is_emoticon = (
            isinstance(node, Tag)
            and node.name == 'span'
            and 'Emoticon' in node['class']
        )
    except KeyError:
        is_emoticon = False

    if is_emoticon:
        return output_document.new_tag('emoticon', value=node.text)


def test_plain_tag(node, output_document):
    # a plain tag with no attributes which should be preserved, and its
    # contents converted recursively
    if isinstance(node, Tag) and node.name in ('i', 'b', 'u', 'p', 'div') and not node.attrs:
        tag = output_document.new_tag(node.name)
        convert_message(node, output_document, tag)
        return tag


def test_user_quote(node, output_document):
    try:
        is_user_quote = (
            isinstance(node, Tag)
            and node.name == 'blockquote'
            and 'UserQuote' in node['class']
        )
    except KeyError:
        is_user_quote = False

    if is_user_quote:
        tag = output_document.new_tag(
            'blockquote',
        )

        quote_author = node.select_one('> .QuoteAuthor')
        if quote_author:
            author_link = quote_author.a
            if author_link:
                tag['author-name'] = author_link.text
                tag['author-id'] = author_link['href'].split('/')[-2]

            quote_link = quote_author.find('a', class_='QuoteLink')
            if quote_link:
                tag['post-id'] = quote_link['href'].split('#')[-1]

        quote_text = node.select_one('> .QuoteText')
        convert_message(quote_text, output_document, tag)
        return tag


def test_font_style(node, output_document):
    is_style_span = (
        isinstance(node, Tag)
        and node.name == 'span'
        and list(node.attrs.keys()) == ['style']
    )
    if is_style_span:
        tag = output_document.new_tag('font')
        styles = re.findall(r'([\w\-]+):\s*([^\;]+);', node['style'])
        for key, val in styles:
            if key in ('font-size', 'font-family'):
                tag[key] = val

        convert_message(node, output_document, tag)
        return tag


def test_link(node, output_document):
    if isinstance(node, Tag) and node.name == 'a' and 'href' in node.attrs:
        tag = output_document.new_tag('a', href=node['href'])
        convert_message(node, output_document, tag)
        return tag


def test_bbcode_center(node, output_document):
    if isinstance(node, Tag) and node.name == 'div' and 'class' in node.attrs and 'bbcode_center' in node['class']:
        tag = output_document.new_tag('center')
        convert_message(node, output_document, tag)
        return tag


def test_bbcode_hr(node, output_document):
    if isinstance(node, Tag) and node.name == 'hr' and 'class' in node.attrs and 'bbcode_rule' in node['class']:
        return output_document.new_tag('hr')


def test_bbcode_ul(node, output_document):
    if isinstance(node, Tag) and node.name == 'ul' and 'class' in node.attrs and 'bbcode_list' in node['class']:
        ul = output_document.new_tag('ul')
        for child_node in node.children:
            if isinstance(child_node, Tag) and child_node.name == 'li' and not child_node.attrs:
                li = output_document.new_tag('li')
                ul.append(li)
                convert_message(child_node, output_document, li)
            elif isinstance(child_node, NavigableString) and not child_node.strip():
                # ignore whitespace between <li> tags
                pass
            else:
                # invalid child node
                return

        return ul


def test_video_wrap(node, output_document):
    if isinstance(node, Tag) and node.name == 'span' and 'class' in node.attrs and 'VideoWrap' in node['class']:
        tag = output_document.new_tag('video')
        video_element = node.find(class_='Video')

        if 'YouTube' in video_element['class']:
            tag['type'] = 'YouTube'

        tag['id'] = video_element['id']

        link_node = node.a
        tag['href'] = link_node['href']

        img = link_node.img
        tag['preview-image'] = img['src']
        tag['width'] = img['width']
        tag['height'] = img['height']

        return tag


def test_video_iframe(node, output_document):
    if isinstance(node, Tag) and node.name == 'div' and 'class' in node.attrs and 'Video' in node['class']:
        iframe = node.iframe
        if iframe:
            tag = output_document.new_tag('video')
            url = iframe['src']
            tag['href'] = url

            match = re.match(r'https?://(?:www\.)?youtube\.com/embed/([^/]+)', url)
            if match:
                tag['type'] = 'YouTube'
                tag['id'] = 'youtube-%s' % match.group(1)

            tag['width'] = iframe['width']
            tag['height'] = iframe['height']

            return tag


def test_img(node, output_document):
    if isinstance(node, Tag) and node.name == 'img':
        tag = output_document.new_tag('img')
        tag['src'] = node['src']

        for attr in ('width', 'height', 'alt'):
            try:
                tag[attr] = node[attr]
            except KeyError:
                pass

        return tag


def test_pre(node, output_document):
    if isinstance(node, Tag) and node.name == 'pre':
        tag = output_document.new_tag('pre')
        tag.append(str(node.text))

        return tag


def test_spoiler(node, output_document):
    if isinstance(node, Tag) and node.name == 'div' and 'class' in node.attrs and 'UserSpoiler' in node['class']:
        tag = output_document.new_tag('spoiler')
        spoiler_text = node.select_one('> .SpoilerText')
        convert_message(spoiler_text, output_document, tag)
        return tag


NODE_TESTS = [
    test_string_node,
    test_br,
    test_emoticon,
    test_plain_tag,
    test_user_quote,
    test_font_style,
    test_link,
    test_bbcode_center,
    test_bbcode_hr,
    test_bbcode_ul,
    test_video_wrap,
    test_video_iframe,
    test_img,
    test_pre,
    test_spoiler,
]


def convert_message(source, output_document=None, output_target=None):
    if output_document is None:
        output_document = BeautifulSoup('<message></message>', 'html5lib')
    if output_target is None:
        output_target = output_document.message

    for node in source.children:
        identified = False

        for test in NODE_TESTS:
            output_node = test(node, output_document)
            if output_node is not None:
                identified = True
                output_target.append(output_node)
                break

        if not identified:
            raise ValueError("Unsupported node type: %r" % node)

    return str(output_target)


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

        self.body = convert_message(soup.find(class_='Message'))


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

        self.body = convert_message(soup.find(class_='Message'))


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
