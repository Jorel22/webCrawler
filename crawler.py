import os
import sys
import re
import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup
from datetime import datetime, timezone


class Crawler:
    def __init__(self, url, db_uri, db_name):
        self.url = url
        self.titles = []
        self.points = []
        self.comments = []
        try:
            self.usage_collection = MongoClient(db_uri)[db_name]["usage"]
        except Exception as e:
            print("Error connecting to db: ", e)
            sys.exit(1)

    def clean_title(self, title):
        re_str = r"\n(\d+\.) "
        return re.sub(re_str, "", title.rsplit(" (", 1)[0])

    def get_points_comments_from_subtitle(self, subtitle):
        try:
            re_points_str = r"\n(\d+) point"
            re_comments_str = r"(\d+)\xa0comment[s]? \n$"
            search_points = re.search(re_points_str, subtitle)
            search_comments = re.search(re_comments_str, subtitle)
            points = 0 if search_points is None else int(search_points.group(1))
            comments = 0 if search_comments is None else int(search_comments.group(1))
        except Exception as e:
            print("Error in clean_subtitle: ", str(e))
            return 0, 0
        return points, comments

    def get_raw_data(self):
        try:
            r = requests.get(self.url)
            soup = BeautifulSoup(r.content, "html.parser")
        except Exception as e:
            print("Error in get_raw_data: ", str(e))
            return None
        for child in soup.find_all("table")[2].contents:
            try:
                data_text = child.get_text()
                if not data_text:
                    continue
                if (
                    "hide" in data_text
                ):  # depending if "hide" is present in the text, it is a title or a subtitle
                    point, comment = self.get_points_comments_from_subtitle(data_text)
                    self.points.append(point)
                    self.comments.append(comment)
                else:
                    self.titles.append(self.clean_title(data_text))
            except AttributeError:  # a simple way to check if the child is a tag or not
                pass
        return None

    def print_data(self):
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

        try:
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
        except Exception as e:
            print("Error in filter: ", str(e))
            return [], {}
        return ordered, usage

    def save_in_db(self, usage):
        try:
            inserted_obj = self.usage_collection.insert_one(usage)
        except Exception as e:
            print("Error in save_in_db: ", str(e))
            return ""
        return inserted_obj.inserted_id


if __name__ == "__main__":
    url = "https://news.ycombinator.com"
    db_uri = os.getenv("DB_URI", "")
    db_name = os.getenv("DB_NAME", "test")

    filter_id = int(sys.argv[1])
    crawler = Crawler(url, db_uri, db_name)
    crawler.get_raw_data()
    filtered_entries, usage = crawler.filter(filter_id)
    print("Entries: ", filtered_entries)
    print("Usage: ", usage)
    inserted_id = crawler.save_in_db(usage)
    print("Inserted id: ", inserted_id)
