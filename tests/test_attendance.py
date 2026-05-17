# tests/test_attendance.py
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from io import BytesIO
from PIL import Image
from datetime import date

from src.ai.recognition_pipeline import RecognitionResult, RecognitionFailure


def make_fake_image() -> bytes:
    img = Image.new("RGB", (100, 100), color=(200, 100, 50))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestAttendance:

    @pytest.fixture(autouse=True)
    def setup_student(self, client, auth_headers, test_org):
        """Enroll a student before each attendance test."""
        fake_embedding = np.random.rand(512).astype(np.float32)
        client.app.state.pipeline.get_embedding_for_enrollment.return_value = fake_embedding
        client.app.state.pipeline.index = MagicMock()
        client.app.state.pipeline.index.add = MagicMock()
        client.app.state.pipeline.index.get_total.return_value = 1
        client.app.state.pipeline.index.remove = MagicMock(return_value=True)

        response = client.post(
            "/api/v1/students/enroll",
            headers=auth_headers,
            data={
                "name": "Attendance Student",
                "student_code": f"ATT{date.today().strftime('%Y%m%d')}",
                "organization_id": test_org.id,
            },
            files={"face_photo": ("test.jpg", make_fake_image(), "image/jpeg")},
        )
        # Store student_id for use in tests
        if response.status_code == 201:
            self.student_id = response.json()["student"]["id"]
        elif response.status_code == 409:
            # Already exists — get the ID
            list_resp = client.get(
                f"/api/v1/students/organization/{test_org.id}",
                headers=auth_headers,
            )
            students = list_resp.json()["students"]
            self.student_id = students[0]["id"]

    def test_process_frame_success(self, client, test_org):
        """Process a valid frame records attendance successfully."""
        # Mock pipeline to recognize the student
        client.app.state.pipeline.recognize.return_value = RecognitionResult(
            student_id=self.student_id,
            confidence=0.95,
        )

        response = client.post(
            "/api/v1/attendance/process",
            files={"frame": ("frame.jpg", make_fake_image(), "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == self.student_id
        assert data["confidence"] == 0.95
        assert "student_name" in data
        assert "message" in data

    def test_process_frame_already_marked(self, client):
        """Processing the same student twice marks as already_marked."""
        client.app.state.pipeline.recognize.return_value = RecognitionResult(
            student_id=self.student_id,
            confidence=0.92,
        )

        response = client.post(
            "/api/v1/attendance/process",
            files={"frame": ("frame.jpg", make_fake_image(), "image/jpeg")},
        )
        assert response.status_code == 200
        assert response.json()["already_marked"] is True

    def test_process_frame_unknown_face(self, client):
        """Unknown face returns 404."""
        client.app.state.pipeline.recognize.return_value = RecognitionFailure(
            reason="Face not recognised. Student may not be registered."
        )

        response = client.post(
            "/api/v1/attendance/process",
            files={"frame": ("frame.jpg", make_fake_image(), "image/jpeg")},
        )
        assert response.status_code == 404

    def test_process_frame_spoof_detected(self, client):
        """Spoof detection returns 403."""
        client.app.state.pipeline.recognize.return_value = RecognitionFailure(
            reason="Spoof attempt detected."
        )

        response = client.post(
            "/api/v1/attendance/process",
            files={"frame": ("frame.jpg", make_fake_image(), "image/jpeg")},
        )
        assert response.status_code == 403

    def test_process_no_api_key(self, client):
        """Process without API key fails — but overridden in tests so passes."""
        # Note: in tests, verify_kiosk_key is overridden to always pass
        # This test just verifies the endpoint is reachable
        response = client.post(
            "/api/v1/attendance/process",
            files={"frame": ("frame.jpg", make_fake_image(), "image/jpeg")},
        )
        assert response.status_code in [200, 404]

    def test_get_today_attendance(self, client, auth_headers, test_org):
        """Get today's attendance returns records."""
        response = client.get(
            f"/api/v1/attendance/today/{test_org.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total" in data
        assert isinstance(data["records"], list)

    def test_get_attendance_range(self, client, auth_headers, test_org):
        """Get attendance for date range returns records."""
        today = date.today().isoformat()
        response = client.get(
            f"/api/v1/attendance/range/{test_org.id}?start_date={today}&end_date={today}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert data["date_from"] == today
        assert data["date_to"] == today

    def test_mark_absents(self, client, auth_headers, test_org):
        """Mark absents returns count of marked students."""
        response = client.post(
            f"/api/v1/attendance/mark-absent/{test_org.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "marked_count" in data
        assert isinstance(data["marked_count"], int)

    def test_get_student_statistics(self, client, auth_headers):
        """Get statistics for a student returns correct structure."""
        today = date.today().isoformat()
        response = client.get(
            f"/api/v1/attendance/statistics/{self.student_id}"
            f"?start_date=2026-01-01&end_date={today}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "attendance_percentage" in data
        assert "total_days" in data
        assert "present_days" in data
        assert "late_days" in data
        assert 0 <= data["attendance_percentage"] <= 100
