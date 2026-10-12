import unittest
from unittest.mock import MagicMock, patch
import requests

from app.models.schema import MaterialInfo, VideoAspect
from app.services import material


class TestArchiveOrgIntegration(unittest.TestCase):
    def setUp(self):
        self.sample_search_response = {
            "responseHeader": {"status": 0, "QTime": 15},
            "response": {
                "numFound": 2,
                "start": 0,
                "docs": [
                    {
                        "identifier": "AboutBan1935",
                        "title": "About Bananas",
                        "description": "Educational short film about bananas.",
                        "downloads": 27201041,
                        "year": 1935,
                    },
                    {
                        "identifier": "ElectricPower1946",
                        "title": "Electric Power",
                        "description": "Documentary about electricity transmission.",
                        "downloads": 84120,
                        "year": 1946,
                    },
                ],
            },
        }

        self.sample_files_about_ban = {
            "result": [
                {"name": "AboutBan1935.mp3", "format": "MP3", "length": "11:03"},
                {"name": "AboutBan1935.avi", "format": "Cinepack", "length": "664.29"},
                {"name": "AboutBan1935.mp4", "format": "h.264", "length": "664.03", "size": 68512128},
                {"name": "AboutBan1935_512kb.mp4", "format": "512Kb MPEG4", "length": "664.03", "size": 45941165},
            ]
        }

        self.sample_files_electric = {
            "result": [
                {"name": "ElectricPower1946.mp4", "format": "MPEG4", "length": "120.0", "size": 15000000},
            ]
        }

    def _mock_requests_get(self, search_resp=None, files_resp_map=None, status_code=200):
        if search_resp is None:
            search_resp = self.sample_search_response
        if files_resp_map is None:
            files_resp_map = {
                "AboutBan1935": self.sample_files_about_ban,
                "ElectricPower1946": self.sample_files_electric,
            }

        def side_effect(url, *args, **kwargs):
            mock_res = MagicMock()
            mock_res.status_code = status_code

            if "advancedsearch.php" in url:
                mock_res.json.return_value = search_resp
                return mock_res

            for ident, files_data in files_resp_map.items():
                if f"metadata/{ident}/files" in url:
                    mock_res.json.return_value = files_data
                    return mock_res

            mock_res.status_code = 404
            mock_res.json.return_value = {"error": "not found"}
            return mock_res

        return side_effect

    @patch("app.services.material.requests.get")
    def test_search_videos_archiveorg_success(self, mock_get):
        mock_get.side_effect = self._mock_requests_get()

        results = material.search_videos_archiveorg("banana", minimum_duration=3)

        self.assertEqual(len(results), 2)

        first = results[0]
        self.assertIsInstance(first, MaterialInfo)
        self.assertEqual(first.provider, "archive_org")
        self.assertEqual(
            first.url,
            "https://archive.org/download/AboutBan1935/AboutBan1935_512kb.mp4",
        )
        self.assertEqual(first.duration, 664)
        self.assertIsNotNone(first.source_info)
        self.assertEqual(first.source_info["asset_id"], "AboutBan1935")
        self.assertEqual(first.source_info["title"], "About Bananas")
        self.assertEqual(first.source_info["downloads"], 27201041)
        self.assertEqual(first.source_info["year"], 1935)
        self.assertEqual(
            first.source_info["source_page"],
            "https://archive.org/details/AboutBan1935",
        )

        second = results[1]
        self.assertEqual(second.provider, "archive_org")
        self.assertEqual(
            second.url,
            "https://archive.org/download/ElectricPower1946/ElectricPower1946.mp4",
        )
        self.assertEqual(second.duration, 120)

    @patch("app.services.material.requests.get")
    def test_search_videos_archiveorg_query_url_formatting(self, mock_get):
        mock_get.side_effect = self._mock_requests_get()

        material.search_videos_archiveorg("vintage cars", minimum_duration=3)

        first_call_url = mock_get.call_args_list[0][0][0]
        self.assertIn("advancedsearch.php", first_call_url)
        self.assertIn("collection:(prelinger+OR+cinematicfilms+OR+stock_footage)", first_call_url)
        self.assertIn("format:(h.264)", first_call_url)
        self.assertIn("(vintage+cars)", first_call_url)
        self.assertIn("sort[]=downloads+desc", first_call_url)
        self.assertIn("rows=15", first_call_url)
        self.assertIn("output=json", first_call_url)

    @patch("app.services.material.requests.get")
    def test_search_videos_archiveorg_empty_query_fallback(self, mock_get):
        mock_get.side_effect = self._mock_requests_get()

        material.search_videos_archiveorg("   ", minimum_duration=3)

        first_call_url = mock_get.call_args_list[0][0][0]
        self.assertIn("(film)", first_call_url)

    @patch("app.services.material.requests.get")
    def test_search_videos_archiveorg_file_format_filtering(self, mock_get):
        # Doc 1 has no MP4 formats
        # Doc 2 has valid .mp4
        non_mp4_files = {
            "result": [
                {"name": "clip.avi", "format": "Cinepack", "length": "100"},
                {"name": "clip.ogv", "format": "Ogg Video", "length": "100"},
                {"name": "clip.gif", "format": "Animated GIF"},
            ]
        }
        mock_get.side_effect = self._mock_requests_get(
            files_resp_map={
                "AboutBan1935": non_mp4_files,
                "ElectricPower1946": self.sample_files_electric,
            }
        )

        results = material.search_videos_archiveorg("power", minimum_duration=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source_info["asset_id"], "ElectricPower1946")

    @patch("app.services.material.requests.get")
    def test_search_videos_archiveorg_duration_filtering(self, mock_get):
        short_clip = {
            "result": [
                {"name": "short.mp4", "format": "h.264", "length": "2.5"},
            ]
        }
        mm_ss_clip = {
            "result": [
                {"name": "medium.mp4", "format": "h.264", "length": "01:15"},
            ]
        }
        mock_get.side_effect = self._mock_requests_get(
            files_resp_map={
                "AboutBan1935": short_clip,
                "ElectricPower1946": mm_ss_clip,
            }
        )

        # Minimum duration is 5s -> short.mp4 (2.5s) filtered out, medium.mp4 (75s) accepted
        results = material.search_videos_archiveorg("film", minimum_duration=5)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source_info["asset_id"], "ElectricPower1946")
        self.assertEqual(results[0].duration, 75)

    @patch("app.services.material.requests.get")
    def test_search_videos_archiveorg_http_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        results = material.search_videos_archiveorg("banana")
        self.assertEqual(results, [])

    @patch("app.services.material.requests.get")
    def test_search_videos_archiveorg_network_exception(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        results = material.search_videos_archiveorg("banana")
        self.assertEqual(results, [])

    @patch("app.services.material.requests.get")
    def test_search_videos_archiveorg_per_item_file_lookup_failure_resilience(self, mock_get):
        def side_effect(url, *args, **kwargs):
            mock_res = MagicMock()
            if "advancedsearch.php" in url:
                mock_res.status_code = 200
                mock_res.json.return_value = self.sample_search_response
                return mock_res
            if "AboutBan1935" in url:
                raise requests.Timeout("Files lookup timeout")
            if "ElectricPower1946" in url:
                mock_res.status_code = 200
                mock_res.json.return_value = self.sample_files_electric
                return mock_res
            mock_res.status_code = 404
            return mock_res

        mock_get.side_effect = side_effect

        results = material.search_videos_archiveorg("test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source_info["asset_id"], "ElectricPower1946")

    @patch("app.services.material.search_videos_archiveorg")
    @patch("app.services.material.search_images_wikimedia", return_value=[])
    @patch("app.services.material.search_images_openverse", return_value=[])
    @patch("app.services.material.search_videos_nasa", return_value=[])
    @patch("app.services.material.search_gifs_wikimedia", return_value=[])
    def test_search_media_hybrid_includes_archiveorg(
        self, mock_gif, mock_nasa, mock_openverse, mock_wikimedia, mock_archive
    ):
        dummy_item = MaterialInfo()
        dummy_item.provider = "archive_org"
        dummy_item.url = "https://archive.org/download/test/test.mp4"
        dummy_item.duration = 10
        mock_archive.return_value = [dummy_item]

        results = material.search_media_hybrid("banana", minimum_duration=3)

        mock_archive.assert_called_once_with("banana", 3, VideoAspect.portrait)
        self.assertTrue(any(it.provider == "archive_org" for it in results))
        self.assertEqual(results[0].url, "https://archive.org/download/test/test.mp4")

    @patch("app.services.material.search_videos_archiveorg")
    def test_search_videos_source_archiveorg_dispatch(self, mock_archive):
        dummy_item = MaterialInfo()
        dummy_item.provider = "archive_org"
        dummy_item.url = "https://archive.org/download/test/test.mp4"
        mock_archive.return_value = [dummy_item]

        res1 = material.search_videos("cars", source="archiveorg")
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0].provider, "archive_org")

        res2 = material.search_videos("vintage", source="archive_org")
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0].provider, "archive_org")


if __name__ == "__main__":
    unittest.main()
