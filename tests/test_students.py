# tests/test_students.py
import pytest
import numpy as np
from unittest.mock import MagicMock
from io import BytesIO
from PIL import Image


def make_fake_image() -> bytes:
    """Create a minimal valid JPEG image for upload tests."""
    img = Image.new("RGB", (100, 100), color=(100, 150, 200))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestStudents:

    def test_enroll_student_success(self, client, auth_headers, test_org):
        """Enroll a new student with valid data and photo."""
        # Mock pipeline to return a valid embedding
        fake_embedding = np.random.rand(512).astype(np.float32)
        fake_embedding /= np.linalg.norm(fake_embedding)
        client.app.state.pipeline.get_embedding_for_enrollment.return_value = fake_embedding
        client.app.state.pipeline.index = MagicMock()
        client.app.state.pipeline.index.add = MagicMock()
        client.app.state.pipeline.index.get_total.return_value = 1

        response = client.post(
            "/api/v1/students/enroll",
            headers=auth_headers,
            data={
                "name": "Ahmed Mohamed",
                "student_code": "TEST001",
                "organization_id": test_org.id,
            },
            files={"face_photo": ("test.jpg", make_fake_image(), "image/jpeg")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["student"]["name"] == "Ahmed Mohamed"
        assert data["student"]["student_code"] == "TEST001"
        assert data["faces_in_index"] == 1

    def test_enroll_duplicate_code_fails(self, client, auth_headers, test_org):
        """Enrolling a student with existing code returns 409."""
        fake_embedding = np.random.rand(512).astype(np.float32)
        client.app.state.pipeline.get_embedding_for_enrollment.return_value = fake_embedding
        client.app.state.pipeline.index.add = MagicMock()
        client.app.state.pipeline.index.get_total.return_value = 1

        response = client.post(
            "/api/v1/students/enroll",
            headers=auth_headers,
            data={
                "name": "Ahmed Mohamed",
                "student_code": "TEST001",  # same code as above
                "organization_id": test_org.id,
            },
            files={"face_photo": ("test.jpg", make_fake_image(), "image/jpeg")},
        )
        assert response.status_code == 409

    def test_enroll_no_auth_fails(self, client, test_org):
        """Enrolling without auth returns 401."""
        response = client.post(
            "/api/v1/students/enroll",
            data={
                "name": "Test",
                "student_code": "NOAUTH",
                "organization_id": test_org.id,
            },
            files={"face_photo": ("test.jpg", make_fake_image(), "image/jpeg")},
        )
        assert response.status_code == 401

    def test_list_students(self, client, auth_headers, test_org):
        """List students returns enrolled students."""
        response = client.get(
            f"/api/v1/students/organization/{test_org.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "students" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_get_student_by_id(self, client, auth_headers, test_org):
        """Get student by ID returns correct student."""
        # Get the list first to find a valid ID
        list_response = client.get(
            f"/api/v1/students/organization/{test_org.id}",
            headers=auth_headers,
        )
        students = list_response.json()["students"]
        assert len(students) > 0
        student_id = students[0]["id"]

        response = client.get(
            f"/api/v1/students/{student_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["id"] == student_id

    def test_get_nonexistent_student(self, client, auth_headers):
        """Get non-existent student returns 404."""
        response = client.get("/api/v1/students/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_student(self, client, auth_headers, test_org):
        """Delete an existing student succeeds."""
        # Enroll a student to delete
        fake_embedding = np.random.rand(512).astype(np.float32)
        client.app.state.pipeline.get_embedding_for_enrollment.return_value = fake_embedding
        client.app.state.pipeline.index.add = MagicMock()
        client.app.state.pipeline.index.get_total.return_value = 1
        client.app.state.pipeline.index.remove = MagicMock(return_value=True)

        enroll = client.post(
            "/api/v1/students/enroll",
            headers=auth_headers,
            data={
                "name": "To Delete",
                "student_code": "DELETE001",
                "organization_id": test_org.id,
            },
            files={"face_photo": ("test.jpg", make_fake_image(), "image/jpeg")},
        )
        student_id = enroll.json()["student"]["id"]

        # Now delete
        response = client.delete(
            f"/api/v1/students/{student_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "removed" in response.json()["message"].lower()

    def test_delete_nonexistent_student(self, client, auth_headers):
        """Delete non-existent student returns 404."""
        response = client.delete("/api/v1/students/99999", headers=auth_headers)
        assert response.status_code == 404
