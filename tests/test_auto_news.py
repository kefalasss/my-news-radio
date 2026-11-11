import datetime as dt
import json
import os
import unittest
from unittest import mock
from zoneinfo import ZoneInfo

from tools import auto_news as news


class TestNewsPipeline(unittest.TestCase):
    def test_rss2(self):
        payload = b"""<rss version="2.0"><channel><item>
<title>Blender release</title><link>https://example.org/a</link>
<description>Useful 3D features</description><pubDate>Tue, 10 Nov 2026 10:00:00 GMT</pubDate>
</item></channel></rss>"""
        items = news.parse_feed(payload, "sample")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://example.org/a")
        self.assertIsNotNone(items[0]["published"])

    def test_atom(self):
        payload = b"""<feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Game engine update</title><link rel="alternate" href="https://example.org/b"/>
<updated>2026-11-10T15:00:00Z</updated><summary>Renderer updated</summary>
</entry></feed>"""
        items = news.parse_feed(payload, "sample")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://example.org/b")

    def test_rdf(self):
        payload = b"""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<item><title>Graphics update</title><link>https://example.org/c</link>
<dc:date>2026-11-10T10:00:00+09:00</dc:date></item></rdf:RDF>"""
        items = news.parse_feed(payload, "sample")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://example.org/c")

    def test_no_key_fallback(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            self.assertIsNone(news.gemini_script([{"title": "X"}]))

    def test_stale_news_rejected_and_good_selected(self):
        now = dt.datetime(2026, 11, 11, 6, 20, tzinfo=ZoneInfo("Asia/Tokyo"))
        recent = {
            "title": "New Unity shader", "summary": "New rendering pipeline",
            "url": "https://example.org/shader", "source": "Game Watch",
            "published": now.astimezone(dt.timezone.utc),
        }
        with mock.patch.object(news, "previously_used", return_value=set()):
            self.assertEqual(news.select_news([recent], now), [recent])


if __name__ == "__main__":
    unittest.main()
