
# Integración 1: Usuario ↔ PerfilSalud

from django.test import TestCase
from core.models import Usuario, PerfilSalud

class UsuarioPerfilSaludIntegrationTest(TestCase):

    def setUp(self):
        # Crear un usuario
        self.usuario = Usuario.objects.create_user(
            email="juan@example.com",
            nombre_usuario="juan123",
            password="Test12345"
        )
        # Crear un perfil de salud asociado
        self.perfil = PerfilSalud.objects.create(
            usuario=self.usuario,
            altura_cm=175,
            peso_kg=70,
            nivel_actividad='moderado'
        )

    def test_usuario_perfil_imc(self):
        # Recuperar el perfil desde el usuario
        perfil_usuario = self.usuario.perfil_salud
        self.assertEqual(perfil_usuario, self.perfil)
        
        # Verificar cálculo de IMC
        imc_esperado = round(70 / (1.75 ** 2), 2)
        self.assertEqual(perfil_usuario.imc, imc_esperado)
        
        # Verificar clasificación del IMC
        self.assertEqual(perfil_usuario.clasificacion_imc, "Peso normal")


# Integración 2: Usuario ↔ ModeloIA ↔ DeteccionPostura

from django.test import TestCase
from core.models import Usuario, ModeloIA, Ejercicio, DeteccionPostura

class DeteccionPosturaIntegrationTest(TestCase):

    def setUp(self):
        # Usuario
        self.usuario = Usuario.objects.create_user(
            email="maria@example.com",
            nombre_usuario="maria123",
            password="Test12345"
        )
        # Modelo de IA activo
        self.modelo = ModeloIA.objects.create(
            nombre_modelo="IA_Sentadillas",
            tipo_ejercicio="sentadilla",
            version="1.0",
            puntos_referencia={"cadera": 0, "rodilla": 0},
            angulos_ideales={"cadera": 90, "rodilla": 90},
            umbral_precision=0.8,
            accuracy_entrenamiento=0.85
        )
        # Ejercicio
        self.ejercicio = Ejercicio.objects.create(
            nombre="Sentadilla Básica",
            tipo="fuerza",
            duracion_estimada_minutos=5,
            calorias_estimadas_por_minuto=5
        )

    def test_deteccion_postura_y_recompensa(self):
        # Crear detección con precisión suficiente
        deteccion = DeteccionPostura.objects.create(
            ejercicio=self.ejercicio,
            usuario=self.usuario,
            modelo_ia=self.modelo,
            puntos_corporales_detectados={"cadera": 90, "rodilla": 90},
            precision_deteccion=0.82,
            puntuacion_tecnica=80
        )
        
        # Procesar recompensas
        puntos, cristales = deteccion.procesar_recompensas()
        
        # Verificar que las recompensas se aplicaron al usuario
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.puntos_experiencia, puntos)
        self.assertEqual(self.usuario.cristales_magicos, cristales)
        
        # Verificar que la detección es confiable
        self.assertTrue(deteccion.es_confiable)

# registro, login, asignación de rutina, progreso en misión, detección de postura, y verificación de estadísticas y dashboard.

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from core.models import Usuario, Rutina, Mision, ProgresoMision
from datetime import date, timedelta

@pytest.mark.django_db
def test_flujo_completo_usuario():
    client = APIClient()

    # ===== Registro de usuario =====
    register_url = reverse('register')
    user_data = {
        'nombre_usuario': 'testuser',
        'email': 'test@example.com',
        'nombre_completo': 'Test User',
        'fecha_nacimiento': '2000-01-01',
        'tipo_usuario': 'usuario_final',
        'password': 'Test1234!',
        'password_confirm': 'Test1234!',
    }
    response = client.post(register_url, user_data, format='json')
    assert response.status_code == 201
    user = Usuario.objects.get(email='test@example.com')  # Obtener instancia del usuario

    # ===== Login =====
    login_url = reverse('login')
    response = client.post(login_url, {'email': 'test@example.com', 'password': 'Test1234!'}, format='json')
    assert response.status_code == 200
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # ===== Crear rutina (simulando admin) =====
    admin = Usuario.objects.create_superuser(
        nombre_usuario='admin',
        email='admin@example.com',
        password='Admin1234!'
    )
    rutina = Rutina.objects.create(
        nombre='Rutina de prueba',
        descripcion='Descripción de la rutina de prueba',
        nivel_dificultad='principiante',  # Valor válido según tu ChoiceField
        duracion_minutos=30,              # Valor numérico válido
        tipo_ejercicio='cardio',          # Valor válido según tu ChoiceField
        calorias_estimadas=250,           # Valor numérico válido
        es_publica=True,
        creador=admin
    )

    # ===== Asignar rutina al usuario =====
    asignar_url = reverse('rutina-asignar-a-mi', args=[rutina.id])
    response = client.post(asignar_url)
    assert response.status_code in [200, 201]
    asignacion_id = response.data['id']

    # ===== Marcar rutina como completada =====
    marcar_completada_url = reverse('asignacionrutina-marcar-completada', args=[asignacion_id])
    response = client.post(marcar_completada_url, {'calificacion_dificultad': 4, 'notas_usuario': 'Buen entrenamiento'})
    assert response.status_code == 200
    assert response.data['completada'] is True

    # ===== Crear misión =====
    mision = Mision.objects.create(
        titulo='Misión Test',
        descripcion='Descripción misión',
        tipo_mision='rutina',             # Valor válido según TIPO_MISION_CHOICES
        objetivo=5,                        # Ejemplo de valor
        unidad_objetivo='rutinas',         # Valor válido según UNIDAD_OBJETIVO_CHOICES      
        recompensa_xp=100,
        recompensa_cristales=10,
        fecha_inicio=date.today() - timedelta(days=1),
        fecha_fin=date.today() + timedelta(days=5),
        frecuencia_recurrencia='diaria',
        esta_activa=True,
        dificultad='medio'
    )

    # ===== Crear progreso de misión para el usuario =====
    progreso = ProgresoMision.objects.create(
        usuario=user,
        mision=mision,
        completada=False
    )

    # ===== Simular actualización del progreso =====
    progreso.actualizar_progreso(incremento=5)  # Completa la misión
    progreso.refresh_from_db()
    user.refresh_from_db()

    # ===== Verificar que la misión se completó y se otorgaron recompensas =====
    assert progreso.completada is True
    assert progreso.progreso_actual == mision.objetivo
    assert user.puntos_experiencia >= mision.recompensa_xp
    assert user.cristales_magicos >= mision.recompensa_cristales

