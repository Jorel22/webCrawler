import os
from crawler import Crawler
import pytest

url = "https://news.ycombinator.com"
db_uri = os.getenv("DB_URI", "")
db_name = os.getenv("DB_NAME", "test")
crawler = Crawler(url, db_uri, db_name)

test_data = [
    ("\n28 points by Tomte 5 hours ago  | hide | 1\xa0comment \n", 28, 1),
    ("\n5 hours ago  | hide | 15\xa0comments \n", 0, 15),
    ("\n5 hours ago  | hide \n", 0, 0),
    ("\n33 points by Jenso 6 hours ago  | hide\n", 33, 0),
    ("\n1 point by Mark 3 hours ago  | hide | 12\xa0comments \n", 1, 12),
]


class TestCrawler:
    @pytest.mark.parametrize("subtitle, expected_points, expected_comments", test_data)
    def test_clean_subtitle(self, subtitle, expected_points, expected_comments):
        points, comments = crawler.get_points_comments_from_subtitle(subtitle)
        print(points, comments)
        assert points == expected_points
        assert comments == expected_comments
