from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta

from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import CustomTokenObtainPairSerializer

from .models import *
from .serializers import *

# ========== VIEWSETS DE AUTENTICACIÓN Y USUARIOS ==========

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioRegisterSerializer
        return UsuarioSerializer

    def get_queryset(self):
        user = self.request.user
        if user.tipo_usuario == 'administrador':
            return Usuario.objects.all()
        return Usuario.objects.filter(id=user.id)

    @action(detail=False, methods=['get'])
    def perfil(self, request):
        """Obtiene el perfil del usuario autenticado"""
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def actualizar_perfil(self, request):
        """Actualiza el perfil del usuario autenticado"""
        serializer = UsuarioSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtiene estadísticas del usuario"""
        user = request.user
        from django.db.models import Count, Sum, Avg
        
        # Cálculo de estadísticas
        rutinas_completadas = AsignacionRutina.objects.filter(
            usuario=user, completada=True
        ).count()
        
        misiones_completadas = ProgresoMision.objects.filter(
            usuario=user, completada=True
        ).count()
        
        ejercicios_realizados = DeteccionPostura.objects.filter(
            usuario=user
        ).count()
        
        tiempo_entrenamiento = DeteccionPostura.objects.filter(
            usuario=user
        ).aggregate(total=Sum('duracion_analisis_segundos'))['total'] or 0
        
        promedio_puntuacion = DeteccionPostura.objects.filter(
            usuario=user
        ).aggregate(promedio=Avg('puntuacion_tecnica'))['promedio'] or 0
        
        cartas_coleccionadas = ColeccionCarta.objects.filter(
            usuario=user
        ).count()
        
        items_obtenidos = InventarioUsuario.objects.filter(
            usuario=user
        ).count()
        
        # Posición en ranking global (simplificado)
        ranking_global = Ranking.objects.filter(
            usuario=user, tipo_ranking='global'
        ).first()
        posicion_ranking = ranking_global.posicion if ranking_global else None

        data = {
            'total_puntos_experiencia': user.puntos_experiencia,
            'total_cristales': user.cristales_magicos,
            'rutinas_completadas': rutinas_completadas,
            'misiones_completadas': misiones_completadas,
            'ejercicios_realizados': ejercicios_realizados,
            'tiempo_total_entrenamiento': int(tiempo_entrenamiento / 60),  # Convertir a minutos
            'promedio_puntuacion_tecnica': round(promedio_puntuacion, 2),
            'cartas_coleccionadas': cartas_coleccionadas,
            'items_obtenidos': items_obtenidos,
            'posicion_ranking_global': posicion_ranking,
        }
        
        serializer = EstadisticasUsuarioSerializer(data)
        return Response(serializer.data)


class PerfilSaludViewSet(viewsets.ModelViewSet):
    serializer_class = PerfilSaludSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PerfilSalud.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=False, methods=['get'])
    def mi_perfil(self, request):
        """Obtiene el perfil de salud del usuario autenticado"""
        try:
            perfil = PerfilSalud.objects.get(usuario=request.user)
            serializer = PerfilSaludSerializer(perfil)
            return Response(serializer.data)
        except PerfilSalud.DoesNotExist:
            return Response(
                {'detail': 'Perfil de salud no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class DispositivoViewSet(viewsets.ModelViewSet):
    serializer_class = DispositivoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Dispositivo.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class LogActividadViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LogActividadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LogActividad.objects.filter(usuario=self.request.user).order_by('-fecha_actividad')


# ========== VIEWSETS DE ENTRENAMIENTO Y EJERCICIOS ==========

class EjercicioViewSet(viewsets.ModelViewSet):
    queryset = Ejercicio.objects.all()
    serializer_class = EjercicioSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Filtra ejercicios por tipo"""
        tipo = request.query_params.get('tipo')
        if tipo:
            ejercicios = Ejercicio.objects.filter(tipo=tipo)
            serializer = self.get_serializer(ejercicios, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Parámetro tipo requerido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def por_grupo_muscular(self, request):
        """Filtra ejercicios por grupo muscular"""
        grupo = request.query_params.get('grupo')
        if grupo:
            ejercicios = Ejercicio.objects.filter(grupo_muscular=grupo)
            serializer = self.get_serializer(ejercicios, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Parámetro grupo requerido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class RutinaViewSet(viewsets.ModelViewSet):
    serializer_class = RutinaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.tipo_usuario == 'administrador':
            return Rutina.objects.all()
        return Rutina.objects.filter(Q(es_publica=True) | Q(creador=user))

    def perform_create(self, serializer):
        serializer.save(creador=self.request.user)

    @action(detail=True, methods=['post'])
    def asignar_a_mi(self, request, pk=None):
        """Asigna una rutina al usuario autenticado"""
        rutina = self.get_object()
        asignacion, created = AsignacionRutina.objects.get_or_create(
            usuario=request.user,
            rutina=rutina,
            defaults={'fecha_asignacion': timezone.now().date()}
        )
        
        if created:
            serializer = AsignacionRutinaSerializer(asignacion)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'detail': 'Ya tienes esta rutina asignada'}, 
                status=status.HTTP_200_OK
            )


class AsignacionRutinaViewSet(viewsets.ModelViewSet):
    serializer_class = AsignacionRutinaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AsignacionRutina.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=['post'])
    def marcar_completada(self, request, pk=None):
        """Marca una asignación de rutina como completada"""
        asignacion = self.get_object()
        calificacion = request.data.get('calificacion_dificultad')
        notas = request.data.get('notas_usuario', '')
        
        asignacion.marcar_completada(calificacion, notas)
        serializer = self.get_serializer(asignacion)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Obtiene las rutinas asignadas pendientes"""
        pendientes = self.get_queryset().filter(completada=False)
        serializer = self.get_serializer(pendientes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def completadas(self, request):
        """Obtiene las rutinas asignadas completadas"""
        completadas = self.get_queryset().filter(completada=True)
        serializer = self.get_serializer(completadas, many=True)
        return Response(serializer.data)


# ========== VIEWSETS DE GAMIFICACIÓN ==========

class RangoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Rango.objects.all()
    serializer_class = RangoSerializer
    permission_classes = [permissions.IsAuthenticated]


class MisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Mision.objects.filter(esta_activa=True)
    serializer_class = MisionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """Obtiene misiones disponibles para el usuario"""
        user = request.user
        misiones_completadas = ProgresoMision.objects.filter(
            usuario=user, completada=True
        ).values_list('mision_id', flat=True)
        
        # Misiones activas y vigentes que el usuario no ha completado
        misiones_disponibles = Mision.objects.filter(
            esta_activa=True,
            fecha_inicio__lte=timezone.now().date()
        ).exclude(
            Q(fecha_fin__lt=timezone.now().date()) | 
            Q(id__in=misiones_completadas)
        )
        
        serializer = self.get_serializer(misiones_disponibles, many=True)
        return Response(serializer.data)


class ProgresoMisionViewSet(viewsets.ModelViewSet):
    serializer_class = ProgresoMisionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProgresoMision.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=['post'])
    def actualizar_progreso(self, request, pk=None):
        """Actualiza el progreso de una misión"""
        progreso = self.get_object()
        incremento = request.data.get('incremento', 1)
        
        progreso.actualizar_progreso(incremento)
        serializer = self.get_serializer(progreso)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def activas(self, request):
        """Obtiene misiones en progreso (no completadas)"""
        activas = self.get_queryset().filter(completada=False)
        serializer = self.get_serializer(activas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def completadas(self, request):
        """Obtiene misiones completadas"""
        completadas = self.get_queryset().filter(completada=True)
        serializer = self.get_serializer(completadas, many=True)
        return Response(serializer.data)


class RankingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RankingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ranking.objects.filter(usuario=self.request.user)

    @action(detail=False, methods=['get'])
    def global_top(self, request):
        """Obtiene el top del ranking global"""
        top_global = Ranking.objects.filter(
            tipo_ranking='global'
        ).order_by('posicion')[:20]
        serializer = self.get_serializer(top_global, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def semanal_top(self, request):
        """Obtiene el top del ranking semanal"""
        inicio_semana = timezone.now().date() - timedelta(days=timezone.now().weekday())
        top_semanal = Ranking.objects.filter(
            tipo_ranking='semanal',
            periodo=inicio_semana
        ).order_by('posicion')[:20]
        serializer = self.get_serializer(top_semanal, many=True)
        return Response(serializer.data)


# ========== VIEWSETS DE RECOMPENSAS Y COLECCIONABLES ==========

class CartaEjercicioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CartaEjercicio.objects.filter(esta_activa=True)
    serializer_class = CartaEjercicioSerializer
    permission_classes = [permissions.IsAuthenticated]


class ColeccionCartaViewSet(viewsets.ModelViewSet):
    serializer_class = ColeccionCartaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ColeccionCarta.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=['post'])
    def marcar_favorita(self, request, pk=None):
        """Marca/desmarca una carta como favorita"""
        coleccion = self.get_object()
        coleccion.es_favorita = not coleccion.es_favorita
        coleccion.save()
        serializer = self.get_serializer(coleccion)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def favoritas(self, request):
        """Obtiene las cartas favoritas del usuario"""
        favoritas = self.get_queryset().filter(es_favorita=True)
        serializer = self.get_serializer(favoritas, many=True)
        return Response(serializer.data)


class ItemColeccionableViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ItemColeccionable.objects.filter(esta_activo=True)
    serializer_class = ItemColeccionableSerializer
    permission_classes = [permissions.IsAuthenticated]


class InventarioUsuarioViewSet(viewsets.ModelViewSet):
    serializer_class = InventarioUsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InventarioUsuario.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=['post'])
    def equipar(self, request, pk=None):
        """Equipa un item del inventario"""
        inventario = self.get_object()
        inventario.equipar()
        serializer = self.get_serializer(inventario)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def desequipar(self, request, pk=None):
        """Desequipa un item del inventario"""
        inventario = self.get_object()
        inventario.desequipar()
        serializer = self.get_serializer(inventario)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def usar(self, request, pk=None):
        """Usa un item consumible"""
        inventario = self.get_object()
        if inventario.usar():
            serializer = self.get_serializer(inventario)
            return Response(serializer.data)
        return Response(
            {'detail': 'No se puede usar este item'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def equipados(self, request):
        """Obtiene los items actualmente equipados"""
        equipados = InventarioUsuario.obtener_items_equipados(request.user)
        serializer = self.get_serializer(equipados, many=True)
        return Response(serializer.data)


# ========== VIEWSETS DE IA Y DETECCIÓN DE POSTURAS ==========

class ModeloIAViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ModeloIA.objects.filter(esta_activo=True)
    serializer_class = ModeloIASerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def por_ejercicio(self, request):
        """Obtiene modelos por tipo de ejercicio"""
        tipo_ejercicio = request.query_params.get('tipo_ejercicio')
        if tipo_ejercicio:
            modelos = ModeloIA.objects.filter(
                tipo_ejercicio=tipo_ejercicio, 
                esta_activo=True
            )
            serializer = self.get_serializer(modelos, many=True)
            return Response(serializer.data)
        return Response(
            {'detail': 'Parámetro tipo_ejercicio requerido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class DeteccionPosturaViewSet(viewsets.ModelViewSet):
    serializer_class = DeteccionPosturaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DeteccionPostura.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        deteccion = serializer.save(usuario=self.request.user)
        # Procesar recompensas automáticamente
        deteccion.procesar_recompensas()

    @action(detail=False, methods=['get'])
    def recientes(self, request):
        """Obtiene las detecciones más recientes"""
        recientes = self.get_queryset().order_by('-fecha_deteccion')[:10]
        serializer = self.get_serializer(recientes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def retroalimentacion(self, request, pk=None):
        """Obtiene la retroalimentación de una detección"""
        deteccion = self.get_object()
        retroalimentaciones = deteccion.retroalimentaciones.all()
        serializer = RetroalimentacionEjecucionSerializer(
            retroalimentaciones, many=True
        )
        return Response(serializer.data)


class RetroalimentacionEjecucionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RetroalimentacionEjecucionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RetroalimentacionEjecucion.objects.filter(
            deteccion__usuario=self.request.user
        )

    @action(detail=True, methods=['post'])
    def marcar_corregido(self, request, pk=None):
        """Marca una corrección como corregida"""
        retroalimentacion = self.get_object()
        retroalimentacion.marcar_corregido()
        serializer = self.get_serializer(retroalimentacion)
        return Response(serializer.data)


# ========== VISTAS DE AUTENTICACIÓN ==========

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.user
            user_data = UsuarioSerializer(user).data
            
            # Generar tokens manualmente para tener control total
            refresh = RefreshToken.for_user(user)
            
            # Agregar claims personalizados
            refresh['tipo_usuario'] = user.tipo_usuario
            refresh['nombre_usuario'] = user.nombre_usuario
            
            return Response({
                'user': user_data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'frontend_destino': 'angular' if user.tipo_usuario == 'administrador' else 'flutter',
                'message': 'Login exitoso'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UsuarioRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generar tokens automáticamente después del registro
            refresh = RefreshToken.for_user(user)
            refresh['tipo_usuario'] = user.tipo_usuario
            refresh['nombre_usuario'] = user.nombre_usuario
            
            user_data = UsuarioSerializer(user).data
            
            return Response({
                'user': user_data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'frontend_destino': 'angular' if user.tipo_usuario == 'administrador' else 'flutter',
                'message': 'Usuario registrado exitosamente'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Logout exitoso'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token requerido'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)
            
            return Response({
                'access': access_token
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Token inválido o expirado'
            }, status=status.HTTP_400_BAD_REQUEST)


# ========== VISTAS DE DASHBOARD Y REPORTES ==========

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Datos básicos del usuario
        user_data = UsuarioSerializer(user).data
        
        # Rutinas asignadas recientes
        rutinas_recientes = AsignacionRutina.objects.filter(
            usuario=user
        ).order_by('-fecha_asignacion')[:5]
        rutinas_serializer = AsignacionRutinaSerializer(
            rutinas_recientes, many=True
        )
        
        # Misiones activas
        misiones_activas = ProgresoMision.objects.filter(
            usuario=user, completada=False
        )[:5]
        misiones_serializer = ProgresoMisionSerializer(
            misiones_activas, many=True
        )
        
        # Logs de actividad recientes
        logs_recientes = LogActividad.objects.filter(
            usuario=user
        ).order_by('-fecha_actividad')[:10]
        logs_serializer = LogActividadSerializer(logs_recientes, many=True)
        
        return Response({
            'usuario': user_data,
            'rutinas_recientes': rutinas_serializer.data,
            'misiones_activas': misiones_serializer.data,
            'actividad_reciente': logs_serializer.data,
        })