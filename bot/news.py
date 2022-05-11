from typing import NamedTuple, List
from requests import exceptions
import requests
import json
import exceptions


class Message(NamedTuple):
    img: str
    file: str
    text: List[str]


class News(NamedTuple):
    title: str
    intro: str
    text: str
    author: str
    img: str
    file: str
    date: str
    category: str


def get_all_posts() -> List:
    news = list()
    domen = 'http://127.0.0.1:5000'

    try:
        response = requests.get(f'{domen}/api/news').text
    except BaseException as err:
        print(err)
    else:
        posts = json.loads(response)['news']
        for post in posts:
            parse_post: News = _parse_get_posts_response(post)
            news.append(parse_post)
        return news
    return None


def get_category_posts(category: str) -> List:
    news = list()
    domen = 'http://127.0.0.1:5000'

    try:
        response = requests.get(f'{domen}/api/news/category/{category}').text
    except BaseException as err:
        print(err)
    else:
        posts = json.loads(response)['news']
        for post in posts:
            parse_post: News = _parse_get_posts_response(post)
            news.append(parse_post)
        return news
    return None


def create_message_posts(posts: List[News]) -> List[Message]:
    data: List = list()
    for post in posts:
        message_text: str = f'*{post.title}*\n{post.intro}\n{post.text}\nКатегория: {post.category}\n' \
                            f'Автор: {post.author}\nДата публикации: {post.date}'
        if len(message_text) > 200:
            message_text = f'{message_text[:200]}...'

        response = requests.get(post.img)
        if response.status_code == 200:
            message_img = response.content
        else:
            message_img = None

        data.append(Message(text=message_text, file=post.file, img=message_img))
    return data


def _parse_get_posts_response(post) -> News:
    return News(title=post['title'], intro=post['intro'], text=post['text'],
                author=post['author'], img=post['img'], file=post['file_url'], date=post['date'],
                category=post['category'])



