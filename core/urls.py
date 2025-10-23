from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()

# Autenticación y usuarios
router.register(r'usuarios', views.UsuarioViewSet, basename='usuario')
router.register(r'perfiles-salud', views.PerfilSaludViewSet, basename='perfilsalud')
router.register(r'dispositivos', views.DispositivoViewSet, basename='dispositivo')
router.register(r'logs-actividad', views.LogActividadViewSet, basename='logactividad')

# Entrenamiento y ejercicios
router.register(r'ejercicios', views.EjercicioViewSet, basename='ejercicio')
router.register(r'rutinas', views.RutinaViewSet, basename='rutina')
router.register(r'asignaciones-rutina', views.AsignacionRutinaViewSet, basename='asignacionrutina')

# Gamificación
router.register(r'rangos', views.RangoViewSet, basename='rango')
router.register(r'misiones', views.MisionViewSet, basename='mision')
router.register(r'progreso-misiones', views.ProgresoMisionViewSet, basename='progresomision')
router.register(r'rankings', views.RankingViewSet, basename='ranking')

# Recompensas y coleccionables
router.register(r'cartas', views.CartaEjercicioViewSet, basename='carta')
router.register(r'coleccion-cartas', views.ColeccionCartaViewSet, basename='coleccioncarta')
router.register(r'items', views.ItemColeccionableViewSet, basename='item')
router.register(r'inventario', views.InventarioUsuarioViewSet, basename='inventario')

# IA y detección de posturas
router.register(r'modelos-ia', views.ModeloIAViewSet, basename='modeloia')
router.register(r'detecciones-postura', views.DeteccionPosturaViewSet, basename='deteccionpostura')
router.register(r'retroalimentacion', views.RetroalimentacionEjecucionViewSet, basename='retroalimentacion')

urlpatterns = [
    path('', include(router.urls)),
    
    # Autenticación
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/refresh/', views.RefreshTokenView.as_view(), name='token_refresh'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh_default'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
]