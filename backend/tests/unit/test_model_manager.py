import os
import unittest
from unittest.mock import MagicMock, patch
from services.model_manager import ModelManager

class TestModelManager(unittest.TestCase):
    def setUp(self):
        self.mm = ModelManager()

    @patch('services.model_manager.settings')
    @patch('services.model_manager.OpenAI')
    def test_llm_waterfall_success(self, mock_openai, mock_settings):
        # Setup mocks
        mock_settings.OPENROUTER_API_KEY = "fake_key"
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock successful response from the first model
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Hello, I am a friend."
        mock_client.chat.completions.create.return_value = mock_response

        response = self.mm.get_llm_response("hi", "you are a friend")
        
        self.assertEqual(response, "Hello, I am a friend.")
        self.assertTrue(mock_client.chat.completions.create.called)

    @patch('services.model_manager.settings')
    @patch('services.model_manager.OpenAI')
    @patch('services.model_manager._rate_tracker')
    def test_llm_waterfall_failover(self, mock_tracker, mock_openai, mock_settings):
        # Setup mocks
        mock_settings.OPENROUTER_API_KEY = "fake_key"
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_tracker.is_rate_limited.return_value = False

        # Mock failure for the first model and success for the second
        mock_response_success = MagicMock()
        mock_response_success.choices[0].message.content = "Failover success"
        
        mock_client.chat.completions.create.side_effect = [
            Exception("Model 1 failed"),
            mock_response_success
        ]

        response = self.mm.get_llm_response("hi", "you are a friend")
        
        self.assertEqual(response, "Failover success")
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)

    @patch('services.model_manager.settings')
    @patch('requests.post')
    def test_stt_openrouter_success(self, mock_post, mock_settings):
        # Setup mocks
        mock_settings.OPENROUTER_API_KEY = "fake_key"
        mock_response = MagicMock()
        mock_response.json.return_value = {"text": "Transcribed text"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Create a dummy audio file
        with open("test.wav", "w") as f:
            f.write("dummy")

        try:
            transcript = self.mm.get_transcription("test.wav")
            self.assertEqual(transcript, "Transcribed text")
            self.assertTrue(mock_post.called)
        finally:
            if os.path.exists("test.wav"):
                os.remove("test.wav")
