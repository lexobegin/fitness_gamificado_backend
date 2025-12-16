from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import *

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Agregar claims personalizados al token
        token['tipo_usuario'] = user.tipo_usuario
        token['nombre_usuario'] = user.nombre_usuario
        token['email'] = user.email
        token['rango_actual'] = user.rango_actual.nombre_completo if user.rango_actual else None

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar datos adicionales a la respuesta
        refresh = self.get_token(self.user)
        
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['user'] = UsuarioSerializer(self.user).data
        data['frontend_destino'] = 'angular' if self.user.tipo_usuario == 'administrador' else 'flutter'
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# ========== SERIALIZERS DE AUTENTICACIÓN Y USUARIOS ==========

class UsuarioRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Usuario
        fields = [
            'email', 'nombre_usuario', 'nombre_completo', 'password', 
            'password_confirm', 'fecha_nacimiento', 'tipo_usuario'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = Usuario.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UsuarioLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Credenciales inválidas')
            if not user.is_active:
                raise serializers.ValidationError('Cuenta desactivada')
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError('Email y contraseña requeridos')


class UsuarioSerializer(serializers.ModelSerializer):
    rango_actual_nombre = serializers.CharField(source='rango_actual.nombre_completo', read_only=True)
    nivel_fisico_display = serializers.CharField(source='get_nivel_fisico_actual_display', read_only=True)
    tipo_usuario_display = serializers.CharField(source='get_tipo_usuario_display', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'nombre_usuario', 'nombre_completo', 'tipo_usuario', 'tipo_usuario_display',
            'fecha_nacimiento', 'nivel_fisico_actual', 'nivel_fisico_display',
            'puntos_experiencia', 'cristales_magicos', 'rango_actual', 'rango_actual_nombre',
            'fecha_registro', 'ultimo_acceso', 'esta_activo'
        ]
        read_only_fields = ['id', 'fecha_registro', 'ultimo_acceso', 'puntos_experiencia', 'cristales_magicos']


class UsuarioPerfilSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    imc = serializers.FloatField(read_only=True)
    clasificacion_imc = serializers.CharField(read_only=True)

    class Meta:
        model = PerfilSalud
        fields = [
            'id', 'usuario', 'altura_cm', 'peso_kg', 'imc', 'clasificacion_imc',
            'condiciones_medicas', 'restricciones_ejercicio', 'nivel_actividad',
            'objetivos_fitness', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'usuario', 'fecha_actualizacion']


class PerfilSaludSerializer(serializers.ModelSerializer):
    imc = serializers.FloatField(read_only=True)
    clasificacion_imc = serializers.CharField(read_only=True)
    nivel_actividad_display = serializers.CharField(source='get_nivel_actividad_display', read_only=True)

    class Meta:
        model = PerfilSalud
        fields = [
            'id', 'altura_cm', 'peso_kg', 'imc', 'clasificacion_imc',
            'condiciones_medicas', 'restricciones_ejercicio', 'nivel_actividad', 'nivel_actividad_display',
            'objetivos_fitness', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_actualizacion']


class DispositivoSerializer(serializers.ModelSerializer):
    sistema_operativo_display = serializers.CharField(source='get_sistema_operativo_display', read_only=True)

    class Meta:
        model = Dispositivo
        fields = [
            'id', 'dispositivo_id', 'modelo_dispositivo', 'sistema_operativo', 'sistema_operativo_display',
            'version_sistema', 'token_notificaciones', 'ultima_conexion', 'esta_activo'
        ]
        read_only_fields = ['id', 'ultima_conexion']


class LogActividadSerializer(serializers.ModelSerializer):
    tipo_actividad_display = serializers.CharField(source='get_tipo_actividad_display', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.nombre_usuario', read_only=True)

    class Meta:
        model = LogActividad
        fields = [
            'id', 'usuario', 'usuario_nombre', 'tipo_actividad', 'tipo_actividad_display',
            'descripcion', 'puntos_ganados', 'cristales_ganados', 'fecha_actividad'
        ]
        read_only_fields = ['id', 'fecha_actividad']


# ========== SERIALIZERS DE ENTRENAMIENTO Y EJERCICIOS ==========

class EjercicioSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    grupo_muscular_display = serializers.CharField(source='get_grupo_muscular_display', read_only=True)
    dificultad_estimada = serializers.IntegerField(read_only=True)

    class Meta:
        model = Ejercicio
        fields = [
            'id', 'nombre', 'descripcion', 'tipo', 'tipo_display', 'grupo_muscular', 'grupo_muscular_display',
            'instrucciones', 'video_url', 'imagen_url', 'duracion_estimada_minutos',
            'calorias_estimadas_por_minuto', 'dificultad_estimada'
        ]


class RutinaEjercicioSerializer(serializers.ModelSerializer):
    ejercicio_nombre = serializers.CharField(source='ejercicio.nombre', read_only=True)
    ejercicio_tipo = serializers.CharField(source='ejercicio.tipo', read_only=True)
    ejercicio_imagen = serializers.CharField(source='ejercicio.imagen_url', read_only=True)
    duracion_estimada_minutos = serializers.FloatField(read_only=True)

    class Meta:
        model = RutinaEjercicio
        fields = [
            'id', 'ejercicio', 'ejercicio_nombre', 'ejercicio_tipo', 'ejercicio_imagen',
            'orden', 'series', 'repeticiones', 'descanso_segundos', 'peso_sugerido', 'notas',
            'duracion_estimada_minutos'
        ]


class RutinaSerializer(serializers.ModelSerializer):
    nivel_dificultad_display = serializers.CharField(source='get_nivel_dificultad_display', read_only=True)
    tipo_ejercicio_display = serializers.CharField(source='get_tipo_ejercicio_display', read_only=True)
    creador_nombre = serializers.CharField(source='creador.nombre_usuario', read_only=True)
    total_ejercicios = serializers.IntegerField(read_only=True)
    grupos_musculares = serializers.ListField(read_only=True)
    ejercicios = RutinaEjercicioSerializer(source='rutina_ejercicios', many=True, read_only=True)

    class Meta:
        model = Rutina
        fields = [
            'id', 'nombre', 'descripcion', 'nivel_dificultad', 'nivel_dificultad_display',
            'duracion_minutos', 'tipo_ejercicio', 'tipo_ejercicio_display', 'calorias_estimadas',
            'es_publica', 'creador', 'creador_nombre', 'fecha_creacion', 'esta_activa',
            'total_ejercicios', 'grupos_musculares', 'ejercicios'
        ]
        read_only_fields = ['fecha_creacion']


class AsignacionRutinaSerializer(serializers.ModelSerializer):
    rutina_nombre = serializers.CharField(source='rutina.nombre', read_only=True)
    rutina_nivel_dificultad = serializers.CharField(source='rutina.nivel_dificultad', read_only=True)
    rutina_duracion = serializers.IntegerField(source='rutina.duracion_minutos', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.nombre_usuario', read_only=True)
    calificacion_dificultad_display = serializers.CharField(source='get_calificacion_dificultad_display', read_only=True)
    esta_vencida = serializers.BooleanField(read_only=True)

    class Meta:
        model = AsignacionRutina
        fields = [
            'id', 'usuario', 'usuario_nombre', 'rutina', 'rutina_nombre', 'rutina_nivel_dificultad', 'rutina_duracion',
            'fecha_asignacion', 'fecha_vencimiento', 'completada', 'fecha_completacion',
            'calificacion_dificultad', 'calificacion_dificultad_display', 'notas_usuario', 'esta_vencida'
        ]
        read_only_fields = ['id', 'fecha_completacion']


# ========== SERIALIZERS DE GAMIFICACIÓN ==========

class RangoSerializer(serializers.ModelSerializer):
    rango_completo = serializers.CharField(read_only=True)

    class Meta:
        model = Rango
        fields = [
            'id', 'nombre', 'subrango', 'nombre_completo', 'rango_completo',
            'puntos_experiencia_minimos', 'puntos_experiencia_maximos',
            'icono_url', 'color_hex', 'descripcion'
        ]


class MisionSerializer(serializers.ModelSerializer):
    tipo_mision_display = serializers.CharField(source='get_tipo_mision_display', read_only=True)
    unidad_objetivo_display = serializers.CharField(source='get_unidad_objetivo_display', read_only=True)
    dificultad_display = serializers.CharField(source='get_dificultad_display', read_only=True)
    descripcion_objetivo = serializers.CharField(read_only=True)
    esta_vigente = serializers.BooleanField(read_only=True)

    class Meta:
        model = Mision
        fields = [
            'id', 'titulo', 'descripcion', 'tipo_mision', 'tipo_mision_display',
            'objetivo', 'unidad_objetivo', 'unidad_objetivo_display', 'descripcion_objetivo',
            'recompensa_xp', 'recompensa_cristales', 'fecha_inicio', 'fecha_fin',
            'es_recurrente', 'frecuencia_recurrencia', 'esta_activa', 'dificultad', 'dificultad_display',
            'esta_vigente'
        ]


class ProgresoMisionSerializer(serializers.ModelSerializer):
    mision_titulo = serializers.CharField(source='mision.titulo', read_only=True)
    mision_tipo = serializers.CharField(source='mision.tipo_mision', read_only=True)
    mision_objetivo = serializers.IntegerField(source='mision.objetivo', read_only=True)
    mision_recompensa_xp = serializers.IntegerField(source='mision.recompensa_xp', read_only=True)
    mision_recompensa_cristales = serializers.IntegerField(source='mision.recompensa_cristales', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.nombre_usuario', read_only=True)
    porcentaje_completado = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProgresoMision
        fields = [
            'id', 'usuario', 'usuario_nombre', 'mision', 'mision_titulo', 'mision_tipo',
            'mision_objetivo', 'mision_recompensa_xp', 'mision_recompensa_cristales',
            'progreso_actual', 'completada', 'fecha_completacion', 'fecha_asignacion',
            'fecha_actualizacion', 'porcentaje_completado'
        ]
        read_only_fields = ['id', 'fecha_completacion', 'fecha_actualizacion']


class RankingSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.nombre_usuario', read_only=True)
    usuario_rango = serializers.CharField(source='usuario.rango_actual.nombre_completo', read_only=True)
    tipo_ranking_display = serializers.CharField(source='get_tipo_ranking_display', read_only=True)

    class Meta:
        model = Ranking
        fields = [
            'id', 'usuario', 'usuario_nombre', 'usuario_rango', 'tipo_ranking', 'tipo_ranking_display',
            'posicion', 'puntuacion', 'periodo', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_actualizacion']


# ========== SERIALIZERS DE RECOMPENSAS Y COLECCIONABLES ==========

class CartaEjercicioSerializer(serializers.ModelSerializer):
    ejercicio_nombre = serializers.CharField(source='ejercicio.nombre', read_only=True)
    ejercicio_tipo = serializers.CharField(source='ejercicio.tipo', read_only=True)
    rareza_display = serializers.CharField(source='get_rareza_display', read_only=True)
    poder_total = serializers.IntegerField(read_only=True)
    color_rareza = serializers.CharField(read_only=True)

    class Meta:
        model = CartaEjercicio
        fields = [
            'id', 'ejercicio', 'ejercicio_nombre', 'ejercicio_tipo', 'nombre', 'descripcion',
            'rareza', 'rareza_display', 'atributo_fuerza', 'atributo_resistencia', 'atributo_flexibilidad',
            'imagen_url', 'precio_cristales', 'poder_total', 'color_rareza', 'esta_activa'
        ]


class ColeccionCartaSerializer(serializers.ModelSerializer):
    carta_nombre = serializers.CharField(source='carta.nombre', read_only=True)
    carta_rareza = serializers.CharField(source='carta.rareza', read_only=True)
    carta_imagen = serializers.CharField(source='carta.imagen_url', read_only=True)
    carta_poder_total = serializers.IntegerField(source='carta.poder_total', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.nombre_usuario', read_only=True)

    class Meta:
        model = ColeccionCarta
        fields = [
            'id', 'usuario', 'usuario_nombre', 'carta', 'carta_nombre', 'carta_rareza',
            'carta_imagen', 'carta_poder_total', 'cantidad', 'fecha_obtencion',
            'fecha_ultima_actualizacion', 'es_favorita'
        ]
        read_only_fields = ['id', 'fecha_obtencion', 'fecha_ultima_actualizacion']


class ItemColeccionableSerializer(serializers.ModelSerializer):
    tipo_item_display = serializers.CharField(source='get_tipo_item_display', read_only=True)
    rareza_display = serializers.CharField(source='get_rareza_display', read_only=True)
    es_permanente = serializers.BooleanField(read_only=True)
    puede_comprar = serializers.BooleanField(read_only=True)

    class Meta:
        model = ItemColeccionable
        fields = [
            'id', 'nombre', 'descripcion', 'tipo_item', 'tipo_item_display',
            'rareza', 'rareza_display', 'precio_cristales', 'icono_url', 'imagen_url',
            'es_exclusivo', 'esta_activo', 'fecha_creacion', 'duracion_dias',
            'es_permanente', 'puede_comprar'
        ]
        read_only_fields = ['fecha_creacion']


class InventarioUsuarioSerializer(serializers.ModelSerializer):
    item_nombre = serializers.CharField(source='item.nombre', read_only=True)
    item_tipo = serializers.CharField(source='item.tipo_item', read_only=True)
    item_imagen = serializers.CharField(source='item.imagen_url', read_only=True)
    item_rareza = serializers.CharField(source='item.rareza', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.nombre_usuario', read_only=True)
    ha_expirado = serializers.BooleanField(read_only=True)
    es_usable = serializers.BooleanField(read_only=True)

    class Meta:
        model = InventarioUsuario
        fields = [
            'id', 'usuario', 'usuario_nombre', 'item', 'item_nombre', 'item_tipo',
            'item_imagen', 'item_rareza', 'fecha_obtencion', 'fecha_expiracion',
            'esta_equipado', 'usos_restantes', 'esta_activo', 'ha_expirado', 'es_usable'
        ]
        read_only_fields = ['id', 'fecha_obtencion']


# ========== SERIALIZERS DE IA Y DETECCIÓN DE POSTURAS ==========

class ModeloIASerializer(serializers.ModelSerializer):
    tipo_ejercicio_display = serializers.CharField(source='get_tipo_ejercicio_display', read_only=True)
    esta_disponible = serializers.BooleanField(read_only=True)

    class Meta:
        model = ModeloIA
        fields = [
            'id', 'nombre_modelo', 'tipo_ejercicio', 'tipo_ejercicio_display', 'version',
            'puntos_referencia', 'angulos_ideales', 'umbral_precision', 'esta_activo',
            'fecha_creacion', 'descripcion', 'accuracy_entrenamiento', 'esta_disponible'
        ]
        read_only_fields = ['fecha_creacion']


class DeteccionPosturaSerializer(serializers.ModelSerializer):
    ejercicio_nombre = serializers.CharField(source='ejercicio.nombre', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.nombre_usuario', read_only=True)
    modelo_nombre = serializers.CharField(source='modelo_ia.nombre_modelo', read_only=True)
    es_confiable = serializers.BooleanField(read_only=True)
    nivel_calificacion = serializers.CharField(read_only=True)
    recompensa_puntos = serializers.IntegerField(read_only=True)

    class Meta:
        model = DeteccionPostura
        fields = [
            'id', 'ejercicio', 'ejercicio_nombre', 'usuario_nombre',
            'modelo_ia', 'modelo_nombre', 'fecha_deteccion', 'puntos_corporales_detectados',
            'precision_deteccion', 'puntuacion_tecnica', 'imagen_analizada_url', 'video_analizado_url',
            'duracion_analisis_segundos', 'metadata_analisis', 'es_confiable', 'nivel_calificacion',
            'recompensa_puntos'
        ]
        read_only_fields = ['id', 'fecha_deteccion']


class RetroalimentacionEjecucionSerializer(serializers.ModelSerializer):
    deteccion_info = serializers.CharField(source='deteccion.__str__', read_only=True)
    tipo_correccion_display = serializers.CharField(source='get_tipo_correccion_display', read_only=True)
    nivel_gravedad_display = serializers.CharField(source='get_nivel_gravedad_display', read_only=True)
    icono_gravedad = serializers.CharField(read_only=True)
    es_urgente = serializers.BooleanField(read_only=True)
    ejercicios_complementarios_nombres = serializers.SerializerMethodField()

    class Meta:
        model = RetroalimentacionEjecucion
        fields = [
            'id', 'deteccion', 'deteccion_info', 'tipo_correccion', 'tipo_correccion_display',
            'mensaje_usuario', 'descripcion_tecnica', 'nivel_gravedad', 'nivel_gravedad_display',
            'fue_corregido', 'fecha_correccion', 'sugerencias_mejora', 'ejercicios_complementarios',
            'ejercicios_complementarios_nombres', 'icono_gravedad', 'es_urgente'
        ]
        read_only_fields = ['id', 'fecha_correccion']

    def get_ejercicios_complementarios_nombres(self, obj):
        return [ej.nombre for ej in obj.ejercicios_complementarios.all()]


# ========== SERIALIZERS PARA ESTADÍSTICAS Y DASHBOARD ==========

class EstadisticasUsuarioSerializer(serializers.Serializer):
    total_puntos_experiencia = serializers.IntegerField()
    total_cristales = serializers.IntegerField()
    rutinas_completadas = serializers.IntegerField()
    misiones_completadas = serializers.IntegerField()
    ejercicios_realizados = serializers.IntegerField()
    tiempo_total_entrenamiento = serializers.IntegerField(help_text="En minutos")
    promedio_puntuacion_tecnica = serializers.FloatField()
    cartas_coleccionadas = serializers.IntegerField()
    items_obtenidos = serializers.IntegerField()
    posicion_ranking_global = serializers.IntegerField(allow_null=True)


class ProgresoMensualSerializer(serializers.Serializer):
    mes = serializers.CharField()
    año = serializers.IntegerField()
    rutinas_completadas = serializers.IntegerField()
    puntos_ganados = serializers.IntegerField()
    cristales_ganados = serializers.IntegerField()
    tiempo_entrenamiento = serializers.IntegerField(help_text="En minutos")