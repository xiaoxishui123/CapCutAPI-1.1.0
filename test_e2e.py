
import unittest
import requests
import json
import time
import os

class E2ETest(unittest.TestCase):
    BASE_URL = "http://localhost:9000"

    def test_full_workflow(self):
        # 1. Create a new draft
        response = requests.post(f"{self.BASE_URL}/create_draft")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        draft_id = data["output"]["draft_id"]

        # 2. Add a video
        video_url = "https://example.com/video.mp4"
        response = requests.post(f"{self.BASE_URL}/add_video", json={
            "draft_id": draft_id,
            "video_url": video_url,
            "start": 0,
            "end": 5
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # 3. Add an audio
        audio_url = "https://example.com/audio.mp3"
        response = requests.post(f"{self.BASE_URL}/add_audio", json={
            "draft_id": draft_id,
            "audio_url": audio_url,
            "start": 0,
            "end": 5
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # 4. Add a text
        response = requests.post(f"{self.BASE_URL}/add_text", json={
            "draft_id": draft_id,
            "text": "Hello, World!",
            "start": 1,
            "end": 4
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # 5. Save the draft
        response = requests.post(f"{self.BASE_URL}/save_draft", json={"draft_id": draft_id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        task_id = data["task_id"]

        # 6. Poll for task completion
        while True:
            response = requests.post(f"{self.BASE_URL}/query_draft_status", json={"task_id": task_id})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            if data["status"] == "completed":
                break
            elif data["status"] == "failed":
                self.fail("Draft saving failed")
            time.sleep(2)

        # 7. Generate download URL
        response = requests.post(f"{self.BASE_URL}/generate_draft_url", json={"draft_id": draft_id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("draft_url", data["output"])

if __name__ == '__main__':
    unittest.main()
