import pytest
from rest_framework.test import APIClient
from rest_framework import status

@pytest.mark.django_db
class TestLoginView:

    def test_login_incorrecto(self):
        client = APIClient()

        data = {
            "email": "noexiste@test.com",
            "password": "wrongpass"
        }

        response = client.post("/api/auth/login/", data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data or "non_field_errors" in response.data
