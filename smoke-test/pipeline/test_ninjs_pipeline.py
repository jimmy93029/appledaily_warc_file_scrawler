#!/usr/bin/env python3
"""Small self-contained tests for canonical formatting and disk-backed dedup."""

from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from extract_text import extract_text, valid_url
from organize_deduplicate import PreflightError, convert_record, organize


def record(version: str, body: str = "正文") -> dict:
    return {
        "uri": "https://www.appledaily.com.tw/local/20200901/ABC123?tracking=yes",
        "standard": {"name": "ninjs", "version": "2.1"},
        "firstcreated": "2020-09-01",
        "versionCreated": version,
        "contentCreated": "2026-06-24T16:44:23+08:00",
        "type": "text",
        "language": "zh-Hant-TW",
        "headlines": [{"role": "main", "value": "標題"}],
        "subjects": [{"name": "local"}],
        "bodies": [{"role": "main", "value": body}],
        "associations": [
            {
                "name": "picture0",
                "uri": "https://static.example/20200901/ABC123/img/a.jpg",
                "type": "picture",
                "headlines": [{"value": "照片說明"}],
                "renditions": [{"href": "./ABC123/img/a.jpg"}],
            }
        ],
        "by": "李奕緯",
        "located": "台北報導",
        "altids": [{"role": "internal", "value": "ABC123"}],
    }


class NinjsPipelineTest(unittest.TestCase):
    def test_real_appledaily_subdomain_and_query_id_are_accepted(self) -> None:
        self.assertTrue(
            valid_url(
                "text/html; charset=utf-8",
                "https://tw.appledaily.com/local/20200901/ABC123?utm_campaign=x",
            )
        )
        self.assertTrue(
            valid_url(
                "text/html",
                "https://360view.appledaily.com.tw/local/20200901/ABC123",
            )
        )
        self.assertFalse(
            valid_url("text/html", "https://notappledaily.com/local/20200901/ABC123")
        )
        self.assertFalse(
            valid_url("text/html", "https://appledaily.com.tw/search/ABC123")
        )

    @patch("extract_text.trafilatura.extract")
    def test_invalid_nonempty_trafilatura_falls_back_to_article(self, mocked) -> None:
        mocked.return_value = json.dumps({"text": "navigation only", "title": ""})
        html = """
        <html><head><title>測試標題</title></head>
        <body><article><p>這是有效的中文新聞正文。</p></article></body></html>
        """
        extracted = extract_text(html)
        self.assertEqual(extracted["method"], "article-elements")
        self.assertEqual(extracted["content"], "這是有效的中文新聞正文。")

    @patch("extract_text.trafilatura.extract")
    def test_invalid_nonempty_trafilatura_falls_back_to_meta(self, mocked) -> None:
        mocked.return_value = json.dumps({"text": "navigation only", "title": ""})
        html = """
        <html><head><title>測試標題</title>
        <meta property="og:description" content="這是有效的中文新聞摘要。">
        </head><body></body></html>
        """
        extracted = extract_text(html)
        self.assertEqual(extracted["method"], "meta-description")
        self.assertEqual(extracted["content"], "這是有效的中文新聞摘要。")

    @patch("extract_text.trafilatura.extract")
    def test_trafilatura_exception_does_not_block_fallback(self, mocked) -> None:
        mocked.side_effect = RuntimeError("engine failed")
        html = """
        <html><head><title>測試標題</title></head>
        <body><article><p>主要引擎失敗後仍應取回中文正文。</p></article></body></html>
        """
        extracted = extract_text(html)
        self.assertEqual(extracted["method"], "article-elements")
        self.assertTrue(extracted["extraction_warnings"])

    def test_conversion_matches_project_form(self) -> None:
        converted, article_id, date = convert_record(record("2022-09-23T18:40:09+08:00"), Path("ABC123.json"))
        self.assertEqual((article_id, date), ("ABC123", "20200901"))
        self.assertEqual(converted["standard"]["version"], "3.2")
        self.assertEqual(converted["type"], "composite")
        self.assertEqual(converted["profile"], "text-photo")
        self.assertEqual(converted["located"], "台北")
        self.assertEqual(converted["altIds"][0]["value"], "ABC123")
        self.assertEqual(converted["bodies"][0]["contentType"], "text/plain")
        self.assertNotIn("renditions", converted["associations"][0])
        self.assertNotIn("firstCreated", converted)  # never invent time from a date-only value

    def test_newer_duplicate_replaces_older_without_id_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            output = root / "output"
            output.mkdir()
            for shard, version, body in (
                (0, "2022-09-03T10:00:00+08:00", "舊正文"),
                (1, "2022-09-23T10:00:00+08:00", "新正文"),
            ):
                article_dir = source / f"file{shard}" / "ABC123"
                article_dir.mkdir(parents=True)
                (article_dir / "ABC123.json").write_text(
                    json.dumps(record(version, body), ensure_ascii=False), encoding="utf-8"
                )
            args = argparse.Namespace(
                source=source,
                output=output,
                start=None,
                end=None,
                resume=False,
                report=None,
                max_occurrences=None,
            )
            counts = organize(args)
            result_path = output / "2020" / "09" / "01" / "ABC123" / "ABC123.json"
            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(result["bodies"][0]["value"], "新正文")
            self.assertEqual(counts["occurrences"], 2)
            self.assertEqual(counts["duplicates"], 1)
            self.assertEqual(counts["unique"], 1)
            self.assertEqual(counts["replaced"], 1)

    def test_missing_output_stops_before_processing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            args = argparse.Namespace(
                source=source,
                output=root / "human_must_create_this",
                start=None,
                end=None,
                resume=False,
                report=None,
                max_occurrences=None,
            )
            with self.assertRaisesRegex(PreflightError, "HUMAN ACTION REQUIRED"):
                organize(args)
            self.assertFalse(args.output.exists())


if __name__ == "__main__":
    unittest.main()
