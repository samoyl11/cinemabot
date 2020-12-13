import abc
import aiohttp
import typing as tp

from aiogram import types
from bs4 import BeautifulSoup
from Levenshtein import distance as levenshtein_distance
from typing import NamedTuple


class MovieReport(NamedTuple):
    title: tp.Optional[str] = None
    alternative_title: tp.Optional[str] = None
    poster_link: tp.Optional[str] = None
    description: tp.Optional[str] = None
    movie_link: tp.Optional[str] = None


class BaseSearcher:
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    async def get_link_from_message(message: types.message) -> str:
        """Method to obtain movie link from user message"""
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    async def get_movie_info_from_link(link: str) -> MovieReport:
        """Method to obtain movie info from link (e.g. name, description)"""
        raise NotImplementedError

    @staticmethod
    def title_matches(message_text: str, title: str, lev_distance: int = 3) -> bool:
        """Calculate levenshtein distance between two strings"""
        return levenshtein_distance(message_text, title) < lev_distance

    async def __call__(self, message: types.message) -> MovieReport:
        link = await self.get_link_from_message(message)
        if link == "":
            return MovieReport()
        report = await self.get_movie_info_from_link(link)
        alternative_title_match = False
        title_match = False

        if report.title is not None:
            title_match = self.title_matches(message.text.lower(), report.title.lower())
        if report.alternative_title is not None:
            alternative_title_match = self.title_matches(message.text.lower(), report.alternative_title.lower())
        if title_match or alternative_title_match:
            return report
        return MovieReport()


class OkkoSearcher(BaseSearcher):
    @staticmethod
    async def get_link_from_message(message: types.message) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://okko.tv/search/{message.text.lower()}') as response:
                search_html = await response.text()

        soup = BeautifulSoup(search_html, "lxml")

        # check that page is found
        for paragraph in soup.findAll('p'):
            if 'Увы, мы ничего не нашли' in paragraph.getText():
                return ""

        link: str = ""
        for val in soup.findAll('a'):
            if '/movie/' in val.get('href'):
                link = 'https://okko.tv' + val.get('href')
                break
        return link

    @staticmethod
    async def get_movie_info_from_link(movie_link: str) -> MovieReport:
        async with aiohttp.ClientSession() as session:
            async with session.get(movie_link) as response:
                movie_html = await response.text()
        soup_movie = BeautifulSoup(movie_html, "lxml")

        # title
        title = soup_movie.find("h1", {"class": "LOjIO"})
        if title is not None:
            title = title.getText()
            if title[0] == '«' and title.rfind('»') != -1:
                title = title[1: title.rfind('»')]

        alternative_title = soup_movie.find("h2", {"class": "_1lODb"})
        if alternative_title is not None:
            alternative_title = alternative_title.getText()

        # poster
        poster_link = soup_movie.find("source", {"type": "image/jpeg"})
        if poster_link is not None:
            poster_link = "https://" + poster_link.get("srcset").split()[0][2:]

        # description
        description = None
        description_paragraph = soup_movie.find('p', {"class": "_3Zh7s"})
        if description_paragraph is not None:
            description_span = description_paragraph.find("span")
            if description_span is not None:
                description = description_span.getText()
        if description is not None:
            description = " ".join([x for x in description.split(' ') if x][:50]) + '...'
        return MovieReport(title, alternative_title, poster_link, description, movie_link)
