
# TESTEAR QUE LA URL RESULEVE A LA VISTA CORRECTA

import pytest
from django.urls import resolve, reverse
from core.views import LoginView  # Cambia por tu vista real


@pytest.mark.django_db
def test_login_url_resuelve_correctamente():
    """
    Verifica que la URL 'login/' resuelve a la vista LoginView.
    """
    url = reverse("login")  # Usar el nombre de la ruta
    resolved = resolve(url)

    assert resolved.func.view_class == LoginView


# Testear que la URL responde correctamente a un request

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_login_url_respuesta(client):
    """
    Verifica que la URL 'login/' devuelve código HTTP 200 o 405
    dependiendo si usa POST.
    """
    url = reverse("login")
    response = client.get(url)

    # Si la vista solo acepta POST, Django devuelve 405 Method Not Allowed
    assert response.status_code in [200, 405]


# Testear URL protegida (requiere autenticación)

@pytest.mark.django_db
def test_url_protegida_sin_autenticacion(client):
    url = reverse("dashboard")  # Cambia por tu URL protegida
    response = client.get(url)

    assert response.status_code == 401 or response.status_code == 403



# Testear URL protegida con usuario autenticado

from django.contrib.auth import get_user_model
import pytest

@pytest.mark.django_db
def test_url_protegida_con_autenticacion(client):
    User = get_user_model()
    
    # Crear usuario con todos los campos obligatorios
    user = User.objects.create_user(
        email="test@example.com",
        nombre_usuario="Test User",
        password="1234"
    )

    # Login con client de Django
    client.login(email="test@example.com", password="1234")

    # Acceder a la URL protegida
    url = reverse('dashboard')
    response = client.get(url)

    assert response.status_code == 200

