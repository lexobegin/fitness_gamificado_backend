import pytest
from core.models import Usuario
from core.serializers import UsuarioRegisterSerializer  # <-- cambiar aquí

@pytest.mark.django_db
class TestUsuarioRegisterSerializer:

    def test_serializer_valido_creacion_usuario(self):
        """Prueba que el serializer crea un usuario con datos válidos"""
        data = {
            "email": "usuario@test.com",
            "nombre_usuario": "Usuario1",
            "nombre_completo": "Usuario de Prueba",
            "password": "123456",
            "password_confirm": "123456",
            "tipo_usuario": "usuario_final",
            "fecha_nacimiento": "2000-01-01"
        }

        serializer = UsuarioRegisterSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        usuario = serializer.save()
        assert usuario.email == data["email"]
        assert usuario.nombre_usuario == data["nombre_usuario"]
        assert usuario.tipo_usuario == data["tipo_usuario"]
        # Verifica que la contraseña se haya guardado correctamente
        assert usuario.check_password("123456") is True

    def test_password_no_coincide(self):
        """Prueba que falle si las contraseñas no coinciden"""
        data = {
            "email": "usuario@test.com",
            "nombre_usuario": "Usuario1",
            "nombre_completo": "Usuario de Prueba",
            "password": "123456",
            "password_confirm": "654321",
            "tipo_usuario": "usuario_final",
            "fecha_nacimiento": "2000-01-01"
        }

        serializer = UsuarioRegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_campos_requeridos(self):
        """Prueba que se generen errores si faltan campos obligatorios"""
        data = {}
        serializer = UsuarioRegisterSerializer(data=data)
        assert not serializer.is_valid()
        required_fields = ["email", "nombre_usuario", "password", "password_confirm", "tipo_usuario"]
        for field in required_fields:
            assert field in serializer.errors
