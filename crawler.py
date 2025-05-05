import requests
import re
import os
from pymongo import MongoClient
from bs4 import BeautifulSoup
from datetime import datetime, timezone


class Crawler:
    def __init__(self, url, db_uri, db_name):
        self.url = url
        self.titles = []
        self.points = []
        self.comments = []
        self.usage_collection = MongoClient(db_uri)[db_name]["usage"]

    def clean_title(self, title):
        re_str = r"\n(\d+\.) "
        return re.sub(re_str, "", title.rsplit(" (", 1)[0])

    def clean_data(self, data):
        re_points_str = r"\n(\d+)"
        re_comments_str = r"(\d+)\xa0comments \n$"
        search_points = re.search(re_points_str, data)
        search_comments = re.search(re_comments_str, data)
        points = 0 if search_points is None else int(search_points.group(1))
        comments = 0 if search_comments is None else int(search_comments.group(1))
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
        return None

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
        if filter_id == 1:
            condition_fun = lambda clean_title: len(clean_title.split()) > 5
            sorting_key = lambda x: x["comments"]
            applied_filter = "More"
        elif filter_id == 2:
            condition_fun = lambda clean_title: len(clean_title.split()) <= 5
            sorting_key = lambda x: x["points"]
            applied_filter = "Less"
        else:
            print("Invalid filter_id")
            return [], {}

        for i in range(len(self.comments)):
            clean_title = re.sub(r"[^a-zA-Z0-9\s]", "", self.titles[i])
            if condition_fun(clean_title):
                filtered.append(
                    {
                        "title": self.titles[i],
                        "points": self.points[i],
                        "comments": self.comments[i],
                    }
                )
        usage = {
            "timestamp": datetime.now(timezone.utc),
            "filter": applied_filter,
            "count": len(filtered),
        }

        ordered = sorted(filtered, key=sorting_key, reverse=True)
        return ordered, usage

    def save_in_db(self, usage):
        inserted_obj = self.usage_collection.insert_one(usage)
        return inserted_obj.inserted_id


if __name__ == "__main__":
    url = "https://news.ycombinator.com"
    db_uri = os.getenv("DB_URI", "")
    db_name = os.getenv("DB_NAME", "test")

    crawler = Crawler(url, db_uri, db_name)
    crawler.get_raw_data()
    filtered_entries, usage = crawler.filter(1)
    print("Entries: ", filtered_entries)
    print("Usage: ", usage)
    inserted_id = crawler.save_in_db(usage)
    print("Inserted id: ", inserted_id)
