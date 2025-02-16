import json
import unittest
from unittest.mock import patch

from app.lambda_handler import create_post, fetch_comics


class TestLambdaHandlers(unittest.TestCase):

    @patch("app.lambda_handler.SchedulerService")
    def test_fetch_comics_success(self, MockSchedulerService):
        mock_scheduler = MockSchedulerService.return_value
        mock_scheduler.fetch_new_comics.return_value = 5

        event, context = {}, {}
        response = fetch_comics(event, context)

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIn("Successfully fetched 5 comics", body["message"])

    @patch("app.lambda_handler.SchedulerService")
    def test_fetch_comics_failure(self, MockSchedulerService):
        mock_scheduler = MockSchedulerService.return_value
        mock_scheduler.fetch_new_comics.side_effect = Exception("Fetch error")

        event, context = {}, {}
        response = fetch_comics(event, context)

        self.assertEqual(response["statusCode"], 500)

    @patch("app.lambda_handler.SchedulerService")
    def test_create_post_success(self, MockSchedulerService):
        mock_scheduler = MockSchedulerService.return_value
        mock_scheduler.create_post.return_value = {"uri": "post123"}

        event, context = {}, {}
        response = create_post(event, context)

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIn("Successfully created post", body["message"])
        self.assertEqual(body["postId"], "post123")

    @patch("app.lambda_handler.SchedulerService")
    def test_create_post_no_posts_available(self, MockSchedulerService):
        mock_scheduler = MockSchedulerService.return_value
        mock_scheduler.create_post.return_value = None

        event, context = {}, {}
        response = create_post(event, context)

        self.assertEqual(response["statusCode"], 400)

    @patch("app.lambda_handler.SchedulerService")
    def test_create_post_failure(self, MockSchedulerService):
        mock_scheduler = MockSchedulerService.return_value
        mock_scheduler.create_post.side_effect = Exception("Post creation error")

        event, context = {}, {}
        response = create_post(event, context)

        self.assertEqual(response["statusCode"], 500)
