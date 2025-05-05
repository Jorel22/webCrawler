import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime


class Crawler:
    def __init__(self, url):
        self.url = url
        self.titles = []
        self.points = []
        self.comments = []

    def clean_title(self, title):
        re_str = r"\n(\d+\.) "
        return re.sub(re_str, "", title.rsplit(" (", 1)[0])

    def clean_data(self, data):
        re_points_str = r"\n(\d+)"
        re_comments_str = r"(\d+)\xa0comments \n$"
        search_points = re.search(re_points_str, data)
        if search_points is None:
            points = 0
        else:
            points = int(search_points.group(1))
        search_comments = re.search(re_comments_str, data)
        if search_comments is None:
            comments = 0
        else:
            comments = int(search_comments.group(1))
        return points, comments

    def get_raw_data(self):
        r = requests.get(self.url)
        soup = BeautifulSoup(r.content, "html.parser")
        for child in soup.find_all("table")[2].contents:
            try:
                texto = child.get_text()
                if not texto:
                    continue
                if "hide" in texto:
                    point, comment = self.clean_data(texto)
                    self.points.append(point)
                    self.comments.append(comment)
                else:
                    self.titles.append(self.clean_title(texto))
            except AttributeError:
                pass
        return 0

    def print_data(self):
        print("Printing method")
        print("len_titles: ", len(self.titles))
        print(self.titles)
        print("-------")
        print("len_points: ", len(self.points))
        print(self.points)
        print("-------")
        print("len_comments: ", len(self.comments))
        print(self.comments)

    def filter(self, filter_id=1):
        """
        filter_id = 1 means filter 1, filter_id = 2 means filter 2 \n
        Filter 1 = More than five words in title, sorted by number of comments \n
        Filter 2 = Less or equal to five words in title, sorted by points
        """

        filtered = []
        usage = {}
        for i in range(len(self.comments)):
            clean_title = self.titles[i].replace("+", "")
            if filter_id == 1:
                condition = len(clean_title.split()) > 5
                sorting_key = lambda x: x["comments"]
                applied_filter = "More"
            elif filter_id == 2:
                condition = len(clean_title.split()) <= 5
                sorting_key = lambda x: x["points"]
                applied_filter = "Less"
            clean_title = self.titles[i].replace("+", "")
            if condition:
                filtered.append(
                    {
                        "title": self.titles[i],
                        "points": self.points[i],
                        "comments": self.comments[i],
                    }
                )
        usage = {
            "timestamp": datetime.now(),
            "filter": applied_filter,
            "count": len(filtered),
        }

        ordered = sorted(filtered, key=sorting_key, reverse=True)
        return ordered, usage


URL = "https://news.ycombinator.com"
crawler = Crawler(URL)
crawler.get_raw_data()
filtered_entries, usage = crawler.filter(1)
print("Entries: ", filtered_entries)
print("Usage: ", usage)
