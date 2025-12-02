from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre_usuario, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        if not nombre_usuario:
            raise ValueError("El nombre de usuario es obligatorio")
        
        email = self.normalize_email(email)
        user = self.model(email=email, nombre_usuario=nombre_usuario, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre_usuario, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo_usuario', 'administrador')
        
        return self.create_user(email, nombre_usuario, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    TIPO_USUARIO_CHOICES = [
        ('administrador', 'Administrador'),
        ('usuario_final', 'Usuario Final'),
    ]
    
    NIVEL_FISICO_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
        ('experto', 'Experto'),
    ]

    # Campos básicos de autenticación
    email = models.EmailField(unique=True, max_length=255)
    nombre_usuario = models.CharField(max_length=100, unique=True)
    nombre_completo = models.CharField(max_length=200, blank=True, null=True)
    
    # Tipo de usuario
    tipo_usuario = models.CharField(
        max_length=20, 
        choices=TIPO_USUARIO_CHOICES, 
        default='usuario_final'
    )
    
    # Campos específicos del fitness gamificado
    fecha_nacimiento = models.DateField(blank=True, null=True)
    nivel_fisico_actual = models.CharField(
        max_length=50, 
        choices=NIVEL_FISICO_CHOICES, 
        default='principiante'
    )
    puntos_experiencia = models.IntegerField(default=0)
    cristales_magicos = models.IntegerField(default=0)

    rango_actual = models.ForeignKey(
        'Rango', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='usuarios'
    )
    
    # Campos de control
    fecha_registro = models.DateTimeField(default=timezone.now)
    ultimo_acceso = models.DateTimeField(default=timezone.now)
    esta_activo = models.BooleanField(default=True)
    
    # Campos para Django admin
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre_usuario']

    objects = UsuarioManager()

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.nombre_usuario} ({self.email})"
    
    def save(self, *args, **kwargs):
        # Actualizar último acceso al guardar
        if self.pk:
            self.ultimo_acceso = timezone.now()
        super().save(*args, **kwargs)
    
    def actualizar_rango(self):
        """Actualiza el rango del usuario basado en sus puntos de experiencia"""
        nuevo_rango = Rango.obtener_rango_por_puntos(self.puntos_experiencia)
        if nuevo_rango and nuevo_rango != self.rango_actual:
            rango_anterior = self.rango_actual
            self.rango_actual = nuevo_rango
            self.save()
            
            # Registrar cambio de rango en logs
            if rango_anterior:
                LogActividad.registrar_actividad(
                    usuario=self,
                    tipo_actividad='nivel_subido',
                    descripcion=f"Subió de rango: {rango_anterior.nombre_completo} → {nuevo_rango.nombre_completo}",
                    puntos=100,  # Bonus por subir de rango
                    cristales=50
                )
    
    @property
    def nivel_actual(self):
        """Retorna el nivel físico actual formateado"""
        return self.nivel_fisico_actual.title()
    
    @property
    def es_administrador(self):
        """Verifica si el usuario es administrador"""
        return self.tipo_usuario == 'administrador'
    
    @property
    def es_usuario_final(self):
        """Verifica si el usuario es usuario final"""
        return self.tipo_usuario == 'usuario_final'

class PerfilSalud(models.Model):
    NIVEL_ACTIVIDAD_CHOICES = [
        ('sedentario', 'Sedentario'),
        ('ligero', 'Ligero (ejercicio 1-3 días/semana)'),
        ('moderado', 'Moderado (ejercicio 3-5 días/semana)'),
        ('activo', 'Activo (ejercicio 6-7 días/semana)'),
        ('muy_activo', 'Muy Activo (atleta)'),
    ]

    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='perfil_salud'
    )
    altura_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name='Altura (cm)'
    )
    peso_kg = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name='Peso (kg)'
    )
    condiciones_medicas = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Condiciones médicas'
    )
    restricciones_ejercicio = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Restricciones de ejercicio'
    )
    nivel_actividad = models.CharField(
        max_length=50,
        choices=NIVEL_ACTIVIDAD_CHOICES,
        blank=True, 
        null=True,
        verbose_name='Nivel de actividad'
    )
    objetivos_fitness = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Objetivos de fitness'
    )
    fecha_actualizacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'perfiles_salud'
        verbose_name = 'Perfil de Salud'
        verbose_name_plural = 'Perfiles de Salud'

    def __str__(self):
        return f"Perfil de Salud - {self.usuario.nombre_usuario}"
    
    @property
    def imc(self):
        """Calcula el Índice de Masa Corporal"""
        if self.altura_cm and self.peso_kg:
            altura_m = float(self.altura_cm) / 100
            return round(float(self.peso_kg) / (altura_m ** 2), 2)
        return None
    
    @property
    def clasificacion_imc(self):
        """Clasificación del IMC según OMS"""
        imc_valor = self.imc
        if not imc_valor:
            return "No disponible"
        
        if imc_valor < 18.5:
            return "Bajo peso"
        elif 18.5 <= imc_valor < 25:
            return "Peso normal"
        elif 25 <= imc_valor < 30:
            return "Sobrepeso"
        elif 30 <= imc_valor < 35:
            return "Obesidad grado I"
        elif 35 <= imc_valor < 40:
            return "Obesidad grado II"
        else:
            return "Obesidad grado III"
    
    def save(self, *args, **kwargs):
        # Actualizar fecha de actualización al guardar
        self.fecha_actualizacion = timezone.now()
        super().save(*args, **kwargs)

class Dispositivo(models.Model):
    SISTEMA_OPERATIVO_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ]

    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='dispositivos'
    )
    dispositivo_id = models.CharField(max_length=255)
    modelo_dispositivo = models.CharField(max_length=200, blank=True, null=True)
    sistema_operativo = models.CharField(
        max_length=100, 
        choices=SISTEMA_OPERATIVO_CHOICES
    )
    version_sistema = models.CharField(max_length=50, blank=True, null=True)
    token_notificaciones = models.CharField(max_length=500, blank=True, null=True)
    ultima_conexion = models.DateTimeField(default=timezone.now)
    esta_activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'dispositivos'
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'
        unique_together = ['usuario', 'dispositivo_id']

    def __str__(self):
        return f"{self.modelo_dispositivo} - {self.usuario.nombre_usuario}"
    
    def save(self, *args, **kwargs):
        # Actualizar última conexión al guardar
        self.ultima_conexion = timezone.now()
        super().save(*args, **kwargs)

class LogActividad(models.Model):
    TIPO_ACTIVIDAD_CHOICES = [
        ('ejercicio', 'Ejercicio'),
        ('mision_completada', 'Misión Completada'),
        ('nivel_subido', 'Nivel Subido'),
        ('cristales_ganados', 'Cristales Ganados'),
        ('login', 'Inicio de Sesión'),
        ('registro', 'Registro'),
        ('otro', 'Otro'),
    ]

    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='logs_actividad'
    )
    tipo_actividad = models.CharField(max_length=100, choices=TIPO_ACTIVIDAD_CHOICES)
    descripcion = models.TextField(blank=True, null=True)
    puntos_ganados = models.IntegerField(default=0)
    cristales_ganados = models.IntegerField(default=0)
    fecha_actividad = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'logs_actividad'
        verbose_name = 'Log de Actividad'
        verbose_name_plural = 'Logs de Actividad'
        ordering = ['-fecha_actividad']

    def __str__(self):
        return f"{self.tipo_actividad} - {self.usuario.nombre_usuario} - {self.fecha_actividad.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def registrar_actividad(cls, usuario, tipo_actividad, descripcion="", puntos=0, cristales=0):
        """Método helper para registrar actividades fácilmente"""
        return cls.objects.create(
            usuario=usuario,
            tipo_actividad=tipo_actividad,
            descripcion=descripcion,
            puntos_ganados=puntos,
            cristales_ganados=cristales
        )

class Ejercicio(models.Model):
    TIPO_EJERCICIO_CHOICES = [
        ('fuerza', 'Fuerza'),
        ('cardio', 'Cardio'),
        ('flexibilidad', 'Flexibilidad'),
        ('equilibrio', 'Equilibrio'),
        ('calentamiento', 'Calentamiento'),
    ]

    GRUPO_MUSCULAR_CHOICES = [
        ('pecho', 'Pecho'),
        ('espalda', 'Espalda'),
        ('hombros', 'Hombros'),
        ('piernas', 'Piernas'),
        ('brazos', 'Brazos'),
        ('abdomen', 'Abdomen'),
        ('gluteos', 'Glúteos'),
        ('full_body', 'Cuerpo Completo'),
        ('cardiovascular', 'Cardiovascular'),
    ]

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=100, choices=TIPO_EJERCICIO_CHOICES)
    grupo_muscular = models.CharField(
        max_length=100, 
        choices=GRUPO_MUSCULAR_CHOICES,
        blank=True, 
        null=True
    )
    instrucciones = models.TextField(blank=True, null=True)
    video_url = models.URLField(max_length=500, blank=True, null=True)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    duracion_estimada_minutos = models.IntegerField(default=10, help_text="Duración estimada en minutos")
    calorias_estimadas_por_minuto = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.0,
        help_text="Calorías estimadas por minuto de ejercicio"
    )

    class Meta:
        db_table = 'ejercicios'
        verbose_name = 'Ejercicio'
        verbose_name_plural = 'Ejercicios'

    def __str__(self):
        return self.nombre
    
    @property
    def dificultad_estimada(self):
        """Calcula una dificultad estimada basada en el tipo y grupo muscular"""
        dificultad_base = {
            'fuerza': 3,
            'cardio': 2,
            'flexibilidad': 1,
            'equilibrio': 2,
            'calentamiento': 1,
        }
        return dificultad_base.get(self.tipo, 2)

class Rutina(models.Model):
    NIVEL_DIFICULTAD_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
        ('experto', 'Experto'),
    ]

    TIPO_EJERCICIO_CHOICES = [
        ('fuerza', 'Fuerza'),
        ('cardio', 'Cardio'),
        ('flexibilidad', 'Flexibilidad'),
        ('mixto', 'Mixto'),
        ('completo', 'Entrenamiento Completo'),
    ]

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    nivel_dificultad = models.CharField(
        max_length=50, 
        choices=NIVEL_DIFICULTAD_CHOICES
    )
    duracion_minutos = models.IntegerField(help_text="Duración total estimada en minutos")
    tipo_ejercicio = models.CharField(
        max_length=100, 
        choices=TIPO_EJERCICIO_CHOICES
    )
    calorias_estimadas = models.IntegerField(help_text="Calorías totales estimadas")
    es_publica = models.BooleanField(default=True)
    creador = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='rutinas_creadas',
        limit_choices_to={'tipo_usuario': 'administrador'}
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    esta_activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'rutinas'
        verbose_name = 'Rutina'
        verbose_name_plural = 'Rutinas'
        ordering = ['nivel_dificultad', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.nivel_dificultad})"
    
    @property
    def total_ejercicios(self):
        """Retorna el número total de ejercicios en la rutina"""
        return self.rutina_ejercicios.count()
    
    @property
    def grupos_musculares(self):
        """Retorna los grupos musculares únicos trabajados en la rutina"""
        ejercicios = self.rutina_ejercicios.select_related('ejercicio').all()
        grupos = set(ej.ejercicio.grupo_muscular for ej in ejercicios if ej.ejercicio.grupo_muscular)
        return list(grupos)

class RutinaEjercicio(models.Model):
    rutina = models.ForeignKey(
        Rutina, 
        on_delete=models.CASCADE, 
        related_name='rutina_ejercicios'
    )
    ejercicio = models.ForeignKey(
        Ejercicio, 
        on_delete=models.CASCADE,
        related_name='en_rutinas'
    )
    orden = models.IntegerField(help_text="Orden de ejecución en la rutina")
    series = models.IntegerField(help_text="Número de series")
    repeticiones = models.CharField(
        max_length=100, 
        help_text="Ej: 10-12, 8-10, o '30 segundos' para cardio"
    )
    descanso_segundos = models.IntegerField(
        default=60,
        help_text="Segundos de descanso entre series"
    )
    peso_sugerido = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Peso sugerido en kg (opcional)"
    )
    notas = models.TextField(blank=True, null=True, help_text="Notas adicionales para este ejercicio")

    class Meta:
        db_table = 'rutina_ejercicios'
        verbose_name = 'Ejercicio en Rutina'
        verbose_name_plural = 'Ejercicios en Rutinas'
        ordering = ['rutina', 'orden']
        unique_together = ['rutina', 'orden']

    def __str__(self):
        return f"{self.rutina.nombre} - {self.ejercicio.nombre} (Orden: {self.orden})"
    
    @property
    def duracion_estimada_minutos(self):
        """Calcula la duración estimada de este ejercicio en la rutina"""
        series_tiempo = self.series * 0.5  # 30 segundos por serie en promedio
        descanso_tiempo = (self.series - 1) * (self.descanso_segundos / 60) if self.series > 1 else 0
        return round(series_tiempo + descanso_tiempo, 1)

class AsignacionRutina(models.Model):
    CALIFICACION_CHOICES = [
        (1, 'Muy Fácil'),
        (2, 'Fácil'),
        (3, 'Moderado'),
        (4, 'Difícil'),
        (5, 'Muy Difícil'),
    ]

    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='asignaciones_rutina'
    )
    rutina = models.ForeignKey(
        Rutina, 
        on_delete=models.CASCADE,
        related_name='asignaciones'
    )
    fecha_asignacion = models.DateField(default=timezone.now)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    completada = models.BooleanField(default=False)
    fecha_completacion = models.DateTimeField(blank=True, null=True)
    calificacion_dificultad = models.IntegerField(
        choices=CALIFICACION_CHOICES, 
        blank=True, 
        null=True,
        help_text="Calificación de dificultad del 1 al 5"
    )
    notas_usuario = models.TextField(blank=True, null=True, help_text="Notas del usuario sobre la rutina")

    class Meta:
        db_table = 'asignaciones_rutina'
        verbose_name = 'Asignación de Rutina'
        verbose_name_plural = 'Asignaciones de Rutina'
        ordering = ['-fecha_asignacion']

    def __str__(self):
        return f"{self.usuario.nombre_usuario} - {self.rutina.nombre} - {self.fecha_asignacion}"
    
    def marcar_completada(self, calificacion=None, notas=""):
        """Método para marcar la rutina como completada"""
        self.completada = True
        self.fecha_completacion = timezone.now()
        if calificacion:
            self.calificacion_dificultad = calificacion
        if notas:
            self.notas_usuario = notas
        self.save()
        
        # Registrar en logs de actividad
        LogActividad.registrar_actividad(
            usuario=self.usuario,
            tipo_actividad='ejercicio',
            descripcion=f"Completó la rutina: {self.rutina.nombre}",
            puntos=50,  # Puntos base por completar rutina
            cristales=10  # Cristales base por completar rutina
        )
    
    @property
    def esta_vencida(self):
        """Verifica si la asignación está vencida"""
        if self.fecha_vencimiento and timezone.now().date() > self.fecha_vencimiento:
            return not self.completada
        return False

class Rango(models.Model):
    nombre = models.CharField(max_length=10)
    nombre_completo = models.CharField(max_length=50)
    subrango = models.CharField(max_length=10, blank=True, null=True)
    puntos_experiencia_minimos = models.IntegerField()
    puntos_experiencia_maximos = models.IntegerField(blank=True, null=True)
    icono_url = models.URLField(max_length=500, blank=True, null=True)
    color_hex = models.CharField(max_length=7, default='#000000', help_text="Color en formato HEX")
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'rangos'
        verbose_name = 'Rango'
        verbose_name_plural = 'Rangos'
        ordering = ['puntos_experiencia_minimos']
        unique_together = ('nombre', 'subrango')

    def __str__(self):
        if self.subrango:
            return f"{self.nombre} {self.subrango} - {self.nombre_completo}"
        return f"{self.nombre} - {self.nombre_completo}"
    
    @property
    def rango_completo(self):
        """Retorna el nombre completo del rango con subrango"""
        if self.subrango:
            return f"{self.nombre} {self.subrango}"
        return self.nombre
    
    @classmethod
    def obtener_rango_por_puntos(cls, puntos):
        """Obtiene el rango correspondiente a una cantidad de puntos"""
        return cls.objects.filter(
            puntos_experiencia_minimos__lte=puntos
        ).order_by('-puntos_experiencia_minimos').first()

class Mision(models.Model):
    TIPO_MISION_CHOICES = [
        ('ejercicio', 'Ejercicio'),
        ('rutina', 'Rutina'),
        ('consistencia', 'Consistencia'),
        ('logro', 'Logro Especial'),
        ('social', 'Social'),
        ('exploracion', 'Exploración'),
    ]

    UNIDAD_OBJETIVO_CHOICES = [
        ('repeticiones', 'Repeticiones'),
        ('series', 'Series'),
        ('minutos', 'Minutos'),
        ('dias', 'Días'),
        ('rutinas', 'Rutinas'),
        ('ejercicios', 'Ejercicios'),
        ('veces', 'Veces'),
    ]

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    tipo_mision = models.CharField(max_length=100, choices=TIPO_MISION_CHOICES)
    objetivo = models.IntegerField(help_text="Valor objetivo a alcanzar")
    unidad_objetivo = models.CharField(max_length=50, choices=UNIDAD_OBJETIVO_CHOICES)
    recompensa_xp = models.IntegerField(help_text="Experiencia a recompensar")
    recompensa_cristales = models.IntegerField(default=0)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    es_recurrente = models.BooleanField(default=False)
    frecuencia_recurrencia = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        choices=[('diaria', 'Diaria'), ('semanal', 'Semanal'), ('mensual', 'Mensual')]
    )
    esta_activa = models.BooleanField(default=True)
    dificultad = models.CharField(
        max_length=20,
        choices=[('facil', 'Fácil'), ('medio', 'Medio'), ('dificil', 'Difícil')],
        default='medio'
    )

    class Meta:
        db_table = 'misiones'
        verbose_name = 'Misión'
        verbose_name_plural = 'Misiones'
        ordering = ['dificultad', 'recompensa_xp']

    def __str__(self):
        return f"{self.titulo} ({self.tipo_mision})"
    
    @property
    def esta_vigente(self):
        """Verifica si la misión está vigente"""
        ahora = timezone.now().date()
        if self.fecha_inicio and ahora < self.fecha_inicio:
            return False
        if self.fecha_fin and ahora > self.fecha_fin:
            return False
        return self.esta_activa
    
    @property
    def descripcion_objetivo(self):
        """Retorna una descripción completa del objetivo"""
        return f"{self.objetivo} {self.get_unidad_objetivo_display()}"

class ProgresoMision(models.Model):
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='progreso_misiones'
    )
    mision = models.ForeignKey(
        Mision, 
        on_delete=models.CASCADE,
        related_name='progresos'
    )
    progreso_actual = models.IntegerField(default=0)
    completada = models.BooleanField(default=False)
    fecha_completacion = models.DateTimeField(blank=True, null=True)
    fecha_asignacion = models.DateField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'progreso_misiones'
        verbose_name = 'Progreso de Misión'
        verbose_name_plural = 'Progresos de Misiones'
        unique_together = ['usuario', 'mision']

    def __str__(self):
        return f"{self.usuario.nombre_usuario} - {self.mision.titulo} ({self.progreso_actual}/{self.mision.objetivo})"
    
    @property
    def porcentaje_completado(self):
        """Calcula el porcentaje de completado de la misión"""
        if self.mision.objetivo == 0:
            return 0
        return min(100, int((self.progreso_actual / self.mision.objetivo) * 100))
    
    def actualizar_progreso(self, incremento=1):
        """Actualiza el progreso de la misión"""
        if not self.completada:
            self.progreso_actual += incremento
            self.fecha_actualizacion = timezone.now()
            
            # Verificar si se completó la misión
            if self.progreso_actual >= self.mision.objetivo:
                self.completada = True
                self.fecha_completacion = timezone.now()
                self.progreso_actual = self.mision.objetivo  # No exceder el objetivo
                
                # Recompensar al usuario
                self.usuario.puntos_experiencia += self.mision.recompensa_xp
                self.usuario.cristales_magicos += self.mision.recompensa_cristales
                self.usuario.save()
                
                # Registrar en logs
                LogActividad.registrar_actividad(
                    usuario=self.usuario,
                    tipo_actividad='mision_completada',
                    descripcion=f"Completó misión: {self.mision.titulo}",
                    puntos=self.mision.recompensa_xp,
                    cristales=self.mision.recompensa_cristales
                )
            
            self.save()

class Ranking(models.Model):
    TIPO_RANKING_CHOICES = [
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('anual', 'Anual'),
        ('global', 'Global'),
    ]

    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='rankings'
    )
    tipo_ranking = models.CharField(max_length=100, choices=TIPO_RANKING_CHOICES)
    posicion = models.IntegerField()
    puntuacion = models.IntegerField(help_text="Puntuación total en el ranking")
    periodo = models.DateField(help_text="Fecha de inicio del período del ranking")
    fecha_actualizacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'rankings'
        verbose_name = 'Ranking'
        verbose_name_plural = 'Rankings'
        unique_together = ['usuario', 'tipo_ranking', 'periodo']
        ordering = ['tipo_ranking', 'periodo', 'posicion']

    def __str__(self):
        return f"{self.usuario.nombre_usuario} - {self.tipo_ranking} - Pos {self.posicion}"

    @classmethod
    def actualizar_ranking(cls, tipo_ranking, periodo):
        """Actualiza las posiciones del ranking para un período específico"""
        # Obtener todos los usuarios con sus puntuaciones
        usuarios = Usuario.objects.filter(tipo_usuario='usuario_final').annotate(
            puntuacion_total=models.Sum('logs_actividad__puntos_ganados')
        ).order_by('-puntuacion_total')
        
        # Actualizar o crear registros de ranking
        for posicion, usuario in enumerate(usuarios, 1):
            if usuario.puntuacion_total:  # Solo usuarios con puntuación
                cls.objects.update_or_create(
                    usuario=usuario,
                    tipo_ranking=tipo_ranking,
                    periodo=periodo,
                    defaults={
                        'posicion': posicion,
                        'puntuacion': usuario.puntuacion_total or 0
                    }
                )

class CartaEjercicio(models.Model):
    RAREZA_CHOICES = [
        ('comun', 'Común'),
        ('rara', 'Rara'),
        ('epica', 'Épica'),
        ('legendaria', 'Legendaria'),
        ('mitica', 'Mítica'),
    ]

    ejercicio = models.ForeignKey(
        Ejercicio, 
        on_delete=models.CASCADE,
        related_name='cartas'
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    rareza = models.CharField(max_length=50, choices=RAREZA_CHOICES)
    atributo_fuerza = models.IntegerField(default=1)
    atributo_resistencia = models.IntegerField(default=1)
    atributo_flexibilidad = models.IntegerField(default=1)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    precio_cristales = models.IntegerField(help_text="Precio en cristales mágicos")
    esta_activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'cartas_ejercicio'
        verbose_name = 'Carta de Ejercicio'
        verbose_name_plural = 'Cartas de Ejercicio'

    def __str__(self):
        return f"{self.nombre} ({self.get_rareza_display()})"
    
    @property
    def poder_total(self):
        """Calcula el poder total de la carta"""
        return self.atributo_fuerza + self.atributo_resistencia + self.atributo_flexibilidad
    
    @property
    def color_rareza(self):
        """Retorna el color asociado a la rareza"""
        colores = {
            'comun': '#969696',
            'rara': '#2E86C1',
            'epica': '#8E44AD',
            'legendaria': '#F39C12',
            'mitica': '#E74C3C'
        }
        return colores.get(self.rareza, '#969696')

class ColeccionCarta(models.Model):
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='coleccion_cartas'
    )
    carta = models.ForeignKey(
        CartaEjercicio, 
        on_delete=models.CASCADE,
        related_name='en_colecciones'
    )
    cantidad = models.IntegerField(default=1)
    fecha_obtencion = models.DateTimeField(default=timezone.now)
    fecha_ultima_actualizacion = models.DateTimeField(auto_now=True)
    es_favorita = models.BooleanField(default=False)

    class Meta:
        db_table = 'coleccion_cartas'
        verbose_name = 'Colección de Carta'
        verbose_name_plural = 'Colección de Cartas'
        unique_together = ['usuario', 'carta']

    def __str__(self):
        return f"{self.usuario.nombre_usuario} - {self.carta.nombre} x{self.cantidad}"
    
    def incrementar_cantidad(self, cantidad=1):
        """Incrementa la cantidad de esta carta en la colección"""
        self.cantidad += cantidad
        self.save()
    
    @classmethod
    def obtener_cartas_usuario(cls, usuario):
        """Obtiene todas las cartas de un usuario con información de la carta"""
        return cls.objects.filter(usuario=usuario).select_related('carta', 'carta__ejercicio')

class ItemColeccionable(models.Model):
    TIPO_ITEM_CHOICES = [
        ('avatar', 'Avatar'),
        ('marco', 'Marco de Perfil'),
        ('fondo', 'Fondo de Perfil'),
        ('badge', 'Insignia'),
        ('efecto', 'Efecto Especial'),
        ('tema', 'Tema de UI'),
        ('consumible', 'Consumible'),
    ]

    RAREZA_CHOICES = [
        ('comun', 'Común'),
        ('rara', 'Rara'),
        ('epica', 'Épica'),
        ('legendaria', 'Legendaria'),
        ('mitica', 'Mítica'),
    ]

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    tipo_item = models.CharField(max_length=100, choices=TIPO_ITEM_CHOICES)
    rareza = models.CharField(max_length=50, choices=RAREZA_CHOICES)
    precio_cristales = models.IntegerField(help_text="Precio en cristales mágicos")
    icono_url = models.URLField(max_length=500, blank=True, null=True)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    es_exclusivo = models.BooleanField(default=False)
    esta_activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    duracion_dias = models.IntegerField(
        blank=True, 
        null=True,
        help_text="Duración en días (null = permanente)"
    )

    class Meta:
        db_table = 'items_coleccionables'
        verbose_name = 'Item Coleccionable'
        verbose_name_plural = 'Items Coleccionables'
        ordering = ['tipo_item', 'rareza', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_item_display()})"
    
    @property
    def es_permanente(self):
        """Verifica si el item es permanente"""
        return self.duracion_dias is None
    
    @property
    def puede_comprar(self):
        """Verifica si el item está disponible para compra"""
        return self.esta_activo and self.precio_cristales > 0

class InventarioUsuario(models.Model):
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='inventario'
    )
    item = models.ForeignKey(
        ItemColeccionable, 
        on_delete=models.CASCADE,
        related_name='en_inventarios'
    )
    fecha_obtencion = models.DateTimeField(default=timezone.now)
    fecha_expiracion = models.DateTimeField(blank=True, null=True)
    esta_equipado = models.BooleanField(default=False)
    usos_restantes = models.IntegerField(
        default=1,
        help_text="Usos restantes para items consumibles"
    )
    esta_activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'inventario_usuarios'
        verbose_name = 'Inventario de Usuario'
        verbose_name_plural = "Inventarios de Usuario"
        unique_together = ['usuario', 'item']

    def __str__(self):
        return f"{self.usuario.nombre_usuario} - {self.item.nombre}"
    
    @property
    def ha_expirado(self):
        """Verifica si el item ha expirado"""
        if self.fecha_expiracion:
            return timezone.now() > self.fecha_expiracion
        return False
    
    @property
    def es_usable(self):
        """Verifica si el item puede ser usado"""
        return self.esta_activo and not self.ha_expirado and self.usos_restantes > 0
    
    def equipar(self):
        """Equipa el item para el usuario"""
        # Desequipar otros items del mismo tipo
        items_mismo_tipo = InventarioUsuario.objects.filter(
            usuario=self.usuario,
            item__tipo_item=self.item.tipo_item,
            esta_equipado=True
        ).exclude(id=self.id)
        
        items_mismo_tipo.update(esta_equipado=False)
        
        # Equipar este item
        self.esta_equipado = True
        self.save()
    
    def desequipar(self):
        """Desequipa el item"""
        self.esta_equipado = False
        self.save()
    
    def usar(self):
        """Usa el item (para consumibles)"""
        if self.es_usable and self.item.tipo_item == 'consumible':
            self.usos_restantes -= 1
            if self.usos_restantes <= 0:
                self.esta_activo = False
            self.save()
            return True
        return False
    
    @classmethod
    def obtener_items_equipados(cls, usuario):
        """Obtiene todos los items equipados por un usuario"""
        return cls.objects.filter(
            usuario=usuario, 
            esta_equipado=True,
            esta_activo=True
        ).select_related('item')

class ModeloIA(models.Model):
    TIPO_EJERCICIO_CHOICES = [
        ('sentadilla', 'Sentadilla'),
        ('flexiones', 'Flexiones'),
        ('plancha', 'Plancha'),
        ('estocadas', 'Estocadas'),
        ('fondos', 'Fondos'),
        ('abdominales', 'Abdominales'),
        ('levantamiento_pesas', 'Levantamiento de Pesas'),
        ('yoga', 'Posturas de Yoga'),
        ('general', 'Ejercicio General'),
    ]

    nombre_modelo = models.CharField(max_length=200)
    tipo_ejercicio = models.CharField(max_length=100, choices=TIPO_EJERCICIO_CHOICES)
    version = models.CharField(max_length=50)
    puntos_referencia = models.JSONField(help_text="Puntos corporales de referencia en formato JSON")
    angulos_ideales = models.JSONField(help_text="Ángulos ideales para la postura en formato JSON")
    umbral_precision = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.8,
        help_text="Umbral mínimo de precisión (0.0 - 1.0)"
    )
    esta_activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    descripcion = models.TextField(blank=True, null=True)
    accuracy_entrenamiento = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Precisión del modelo en entrenamiento"
    )

    class Meta:
        db_table = 'modelos_ia'
        verbose_name = 'Modelo de IA'
        verbose_name_plural = 'Modelos de IA'
        unique_together = ['nombre_modelo', 'version']
        ordering = ['tipo_ejercicio', '-version']

    def __str__(self):
        return f"{self.nombre_modelo} v{self.version} - {self.get_tipo_ejercicio_display()}"
    
    @property
    def esta_disponible(self):
        """Verifica si el modelo está disponible para uso"""
        return self.esta_activo and self.accuracy_entrenamiento and self.accuracy_entrenamiento >= 0.7
    
    @classmethod
    def obtener_modelo_activo(cls, tipo_ejercicio):
        """Obtiene el modelo activo más reciente para un tipo de ejercicio"""
        return cls.objects.filter(
            tipo_ejercicio=tipo_ejercicio,
            esta_activo=True
        ).order_by('-version').first()

class DeteccionPostura(models.Model):
    ejercicio = models.ForeignKey(
        'Ejercicio',
        on_delete=models.CASCADE,
        related_name='detecciones_postura'
    )
    usuario = models.ForeignKey(
        'Usuario',
        on_delete=models.CASCADE,
        related_name='detecciones_postura'
    )
    modelo_ia = models.ForeignKey(
        'ModeloIA',
        on_delete=models.CASCADE,
        related_name='detecciones'
    )
    fecha_deteccion = models.DateTimeField(default=timezone.now)
    puntos_corporales_detectados = models.JSONField(help_text="Puntos corporales detectados en formato JSON")
    precision_deteccion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Precisión de la detección (0.0 - 1.0)"
    )
    puntuacion_tecnica = models.IntegerField(
        help_text="Puntuación de técnica (0-100)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    imagen_analizada_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL de la imagen analizada"
    )
    video_analizado_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL del video analizado"
    )
    duracion_analisis_segundos = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Duración del análisis en segundos"
    )
    metadata_analisis = models.JSONField(
        blank=True,
        null=True,
        help_text="Metadatos adicionales del análisis"
    )

    class Meta:
        db_table = 'detecciones_postura'
        verbose_name = 'Detección de Postura'
        verbose_name_plural = 'Detecciones de Postura'
        ordering = ['-fecha_deteccion']

    def __str__(self):
        return f"{self.usuario.nombre_usuario} - {self.ejercicio.nombre} - {self.fecha_deteccion.strftime('%Y-%m-%d %H:%M')}"

    @property
    def es_confiable(self):
        """Verifica si la detección es confiable"""
        return Decimal(self.precision_deteccion) >= Decimal(self.modelo_ia.umbral_precision)

    @property
    def nivel_calificacion(self):
        """Retorna el nivel de calificación basado en la puntuación"""
        if self.puntuacion_tecnica >= 90:
            return 'excelente'
        elif self.puntuacion_tecnica >= 75:
            return 'bueno'
        elif self.puntuacion_tecnica >= 60:
            return 'regular'
        else:
            return 'necesita_mejora'

    @property
    def recompensa_puntos(self):
        """Calcula la recompensa de puntos basada en la puntuación"""
        if self.puntuacion_tecnica >= 90:
            return 30
        elif self.puntuacion_tecnica >= 75:
            return 20
        elif self.puntuacion_tecnica >= 60:
            return 10
        else:
            return 5  # Recompensa mínima por intento

    def procesar_recompensas(self):
        """Procesa las recompensas por la detección exitosa"""
        if self.es_confiable:
            puntos = self.recompensa_puntos
            cristales = max(1, self.puntuacion_tecnica // 20)  # 1-5 cristales

            # Actualizar usuario
            self.usuario.puntos_experiencia += puntos
            self.usuario.cristales_magicos += cristales
            self.usuario.save()

            # Registrar en logs
            from core.models import LogActividad  # Importación local para evitar import circular
            LogActividad.registrar_actividad(
                usuario=self.usuario,
                tipo_actividad='ejercicio',
                descripcion=f"Ejercicio con IA: {self.ejercicio.nombre} - Puntuación: {self.puntuacion_tecnica}",
                puntos=puntos,
                cristales=cristales
            )

            return puntos, cristales
        return 0, 0

class RetroalimentacionEjecucion(models.Model):
    TIPO_CORRECCION_CHOICES = [
        ('postura', 'Postura Corporal'),
        ('alineacion', 'Alineación'),
        ('rango_movimiento', 'Rango de Movimiento'),
        ('velocidad', 'Velocidad de Ejecución'),
        ('respiración', 'Patrón de Respiración'),
        ('estabilidad', 'Estabilidad'),
        ('fuerza', 'Aplicación de Fuerza'),
    ]

    NIVEL_GRAVEDAD_CHOICES = [
        ('leve', 'Leve'),
        ('moderado', 'Moderado'),
        ('grave', 'Grave'),
        ('critico', 'Crítico'),
    ]

    deteccion = models.ForeignKey(
        DeteccionPostura, 
        on_delete=models.CASCADE, 
        related_name='retroalimentaciones'
    )
    tipo_correccion = models.CharField(max_length=100, choices=TIPO_CORRECCION_CHOICES)
    mensaje_usuario = models.TextField(help_text="Mensaje amigable para el usuario")
    descripcion_tecnica = models.TextField(
        blank=True, 
        null=True,
        help_text="Descripción técnica de la corrección"
    )
    nivel_gravedad = models.CharField(max_length=50, choices=NIVEL_GRAVEDAD_CHOICES)
    fue_corregido = models.BooleanField(default=False)
    fecha_correccion = models.DateTimeField(blank=True, null=True)
    sugerencias_mejora = models.TextField(
        blank=True, 
        null=True,
        help_text="Sugerencias específicas para mejorar"
    )
    ejercicios_complementarios = models.ManyToManyField(
        Ejercicio,
        blank=True,
        help_text="Ejercicios recomendados para mejorar esta área",
        related_name='retroalimentaciones_complementarias'
    )

    class Meta:
        db_table = 'retroalimentacion_ejecucion'
        verbose_name = 'Retroalimentación de Ejecución'
        verbose_name_plural = 'Retroalimentaciones de Ejecución'
        ordering = ['nivel_gravedad', 'tipo_correccion']

    def __str__(self):
        return f"{self.deteccion.usuario.nombre_usuario} - {self.tipo_correccion} - {self.nivel_gravedad}"
    
    @property
    def es_urgente(self):
        """Verifica si la corrección es urgente"""
        return self.nivel_gravedad in ['grave', 'critico']
    
    @property
    def icono_gravedad(self):
        """Retorna un icono basado en el nivel de gravedad"""
        iconos = {
            'leve': '✅',
            'moderado': '⚠️',
            'grave': '❌',
            'critico': '🚨'
        }
        return iconos.get(self.nivel_gravedad, '⚪')
    
    def marcar_corregido(self):
        """Marca la corrección como corregida"""
        self.fue_corregido = True
        self.fecha_correccion = timezone.now()
        self.save()
        
        # Recompensa por corregir errores graves
        if self.nivel_gravedad in ['grave', 'critico']:
            LogActividad.registrar_actividad(
                usuario=self.deteccion.usuario,
                tipo_actividad='correccion_postura',
                descripcion=f"Corrigió: {self.tipo_correccion}",
                puntos=15,
                cristales=5
            )