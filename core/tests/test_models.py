import pytest
from django.utils import timezone
from core.models import Rutina
from core.models import Usuario
from core.models import Ejercicio
from core.models import RutinaEjercicio


@pytest.mark.django_db
class TestRutinaModel:

    def test_creacion_rutina(self):
        """Prueba que se pueda crear una Rutina correctamente"""
        admin = Usuario.objects.create_user(
            email="admin@test.com",
            nombre_usuario="Admin",
            password="123456",
            tipo_usuario="administrador"
        )

        rutina = Rutina.objects.create(
            nombre="Full Body Beginner",
            descripcion="Rutina inicial para todo el cuerpo",
            nivel_dificultad="principiante",
            duracion_minutos=45,
            tipo_ejercicio="completo",
            calorias_estimadas=300,
            es_publica=True,
            creador=admin
        )

        assert rutina.nombre == "Full Body Beginner"
        assert rutina.nivel_dificultad == "principiante"
        assert rutina.creador == admin
        assert rutina.esta_activa is True

    def test_str_method(self):
        """Prueba que __str__ retorne el formato correcto"""
        admin = Usuario.objects.create_user(
            email="admin4@test.com",
            nombre_usuario="Admin4",
            password="123456",
            tipo_usuario="administrador"
        )

        rutina = Rutina.objects.create(
            nombre="Cardio Intenso",
            descripcion="Rutina explosiva",
            nivel_dificultad="intermedio",
            duracion_minutos=30,
            tipo_ejercicio="cardio",
            calorias_estimadas=250,
            creador=admin
        )

        assert str(rutina) == "Cardio Intenso (intermedio)"

    def test_total_ejercicios_property(self):
        """Prueba que total_ejercicios cuente los ejercicios relacionados"""
        admin = Usuario.objects.create_user(
            email="admin2@test.com",
            nombre_usuario="Admin2",
            password="123456",
            tipo_usuario="administrador"
        )

        rutina = Rutina.objects.create(
            nombre="Rutina Mixta",
            descripcion="Rutina variada",
            nivel_dificultad="intermedio",
            duracion_minutos=60,
            tipo_ejercicio="mixto",
            calorias_estimadas=400,
            creador=admin
        )

        # Crear ejercicios
        e1 = Ejercicio.objects.create(nombre="Sentadillas", grupo_muscular="Piernas")
        e2 = Ejercicio.objects.create(nombre="Flexiones", grupo_muscular="Pecho")

        # Crear RutinaEjercicio con todos los campos obligatorios
        RutinaEjercicio.objects.create(
            rutina=rutina,
            ejercicio=e1,
            orden=1,
            series=3,
            repeticiones="10-12",
            descanso_segundos=60
        )
        RutinaEjercicio.objects.create(
            rutina=rutina,
            ejercicio=e2,
            orden=2,
            series=3,
            repeticiones="10-12",
            descanso_segundos=60
        )

        assert rutina.total_ejercicios == 2

    def test_grupos_musculares_property(self):
        """Prueba que grupos_musculares retorne grupos únicos"""
        admin = Usuario.objects.create_user(
            email="admin3@test.com",
            nombre_usuario="Admin3",
            password="123456",
            tipo_usuario="administrador"
        )

        rutina = Rutina.objects.create(
            nombre="Fuerza Superior",
            descripcion="Ejercicios de fuerza",
            nivel_dificultad="avanzado",
            duracion_minutos=50,
            tipo_ejercicio="fuerza",
            calorias_estimadas=500,
            creador=admin
        )

        # Crear ejercicios con grupos musculares
        pecho = Ejercicio.objects.create(nombre="Press banca", grupo_muscular="Pecho")
        hombros = Ejercicio.objects.create(nombre="Press militar", grupo_muscular="Hombros")
        pecho2 = Ejercicio.objects.create(nombre="Aperturas", grupo_muscular="Pecho")

        # Crear RutinaEjercicio con todos los campos obligatorios
        RutinaEjercicio.objects.create(
            rutina=rutina,
            ejercicio=pecho,
            orden=1,
            series=3,
            repeticiones="10-12",
            descanso_segundos=60
        )
        RutinaEjercicio.objects.create(
            rutina=rutina,
            ejercicio=hombros,
            orden=2,
            series=3,
            repeticiones="10-12",
            descanso_segundos=60
        )
        RutinaEjercicio.objects.create(
            rutina=rutina,
            ejercicio=pecho2,
            orden=3,
            series=3,
            repeticiones="10-12",
            descanso_segundos=60
        )

        grupos = rutina.grupos_musculares

        assert len(grupos) == 2
        assert "Pecho" in grupos
        assert "Hombros" in grupos
