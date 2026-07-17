import unittest
from unittest.mock import MagicMock, patch

import drift


class DriftSdkContractTests(unittest.TestCase):
    def _mock_response(self, payload):
        response = MagicMock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        return response

    @patch("drift.client.httpx.Client.get")
    def test_load_returns_dataset_with_routes(self, mock_get):
        mock_get.return_value = self._mock_response(
            {
                "id": "jordy-v0",
                "routes": 2,
                "segments": 3,
            }
        )

        dataset = drift.load("jordy-v0", base_url="https://example.test")

        self.assertEqual(dataset.id, "jordy-v0")
        self.assertEqual(dataset.routes_count, 2)
        self.assertEqual(dataset.segments_count, 3)

    @patch("drift.client.httpx.Client.get")
    def test_route_and_segment_models_are_populated(self, mock_get):
        responses = [
            self._mock_response(
                {
                    "route_id": "route-1",
                    "num_segments": 2,
                    "created_at": "2024-01-01T00:00:00+00:00",
                    "dataset": "jordy-v0",
                    "segments": [
                        {"segment_id": "seg-1", "segment_index": 0},
                        {"segment_id": "seg-2", "segment_index": 1},
                    ],
                }
            ),
            self._mock_response(
                {
                    "segment_id": "seg-1",
                    "route_id": "route-1",
                    "segment_index": 0,
                    "files": {"fcamera": "https://example.test/file"},
                    "download_url": "https://example.test/file",
                }
            ),
        ]
        mock_get.side_effect = responses

        route = drift.route("route-1", base_url="https://example.test")
        segment = drift.segment("seg-1", base_url="https://example.test")

        self.assertEqual(route.route_id, "route-1")
        self.assertEqual(route.num_segments, 2)
        self.assertEqual(segment.segment_id, "seg-1")
        self.assertEqual(segment.download_url, "https://example.test/file")


if __name__ == "__main__":
    unittest.main()
