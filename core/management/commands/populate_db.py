import random
from django.core.management.base import BaseCommand
from faker import Faker
from django.utils import timezone
from datetime import timezone as dt_timezone, datetime, timedelta
from core.models import *

fake = Faker('es_ES')

class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de fitness gamificado'

    def handle(self, *args, **kwargs):
        self.stdout.write("Poblando base de datos de Fitness Gamificado...")

        # Orden de creación (respetando dependencias)
        self.crear_rangos()
        self.crear_administradores()
        self.crear_usuarios_finales()
        self.crear_ejercicios()
        self.crear_rutinas()
        self.crear_misiones()
        self.crear_cartas_ejercicios()
        self.crear_items_coleccionables()
        self.crear_modelos_ia()

        self.stdout.write(self.style.SUCCESS("¡Datos de fitness gamificados generados exitosamente!"))

    def crear_rangos(self):
        rangos = [
            {'nombre': 'B', 'subrango': '1', 'nombre_completo': 'Bronce I', 'puntos_min': 0, 'puntos_max': 100, 'color': '#CD7F32'},
            {'nombre': 'B', 'subrango': '2', 'nombre_completo': 'Bronce II', 'puntos_min': 101, 'puntos_max': 300, 'color': '#CD7F32'},
            {'nombre': 'B', 'subrango': '3', 'nombre_completo': 'Bronce III', 'puntos_min': 301, 'puntos_max': 600, 'color': '#CD7F32'},
            {'nombre': 'P', 'subrango': '1', 'nombre_completo': 'Plata I', 'puntos_min': 601, 'puntos_max': 1000, 'color': '#C0C0C0'},
            {'nombre': 'P', 'subrango': '2', 'nombre_completo': 'Plata II', 'puntos_min': 1001, 'puntos_max': 1500, 'color': '#C0C0C0'},
            {'nombre': 'P', 'subrango': '3', 'nombre_completo': 'Plata III', 'puntos_min': 1501, 'puntos_max': 2100, 'color': '#C0C0C0'},
            {'nombre': 'O', 'subrango': '1', 'nombre_completo': 'Oro I', 'puntos_min': 2101, 'puntos_max': 2800, 'color': '#FFD700'},
            {'nombre': 'O', 'subrango': '2', 'nombre_completo': 'Oro II', 'puntos_min': 2801, 'puntos_max': 3600, 'color': '#FFD700'},
            {'nombre': 'O', 'subrango': '3', 'nombre_completo': 'Oro III', 'puntos_min': 3601, 'puntos_max': 4500, 'color': '#FFD700'},
            {'nombre': 'D', 'subrango': None, 'nombre_completo': 'Diamante', 'puntos_min': 4501, 'puntos_max': None, 'color': '#B9F2FF'},
        ]

        for rango_data in rangos:
            Rango.objects.get_or_create(
                nombre=rango_data['nombre'],
                subrango=rango_data['subrango'],
                defaults={
                    'nombre_completo': rango_data['nombre_completo'],
                    'puntos_experiencia_minimos': rango_data['puntos_min'],
                    'puntos_experiencia_maximos': rango_data['puntos_max'],
                    'color_hex': rango_data['color'],
                    'descripcion': f'Rango {rango_data["nombre_completo"]} del sistema de fitness'
                }
            )
        self.stdout.write(f"Rangos creados: {Rango.objects.count()}")

    def crear_administradores(self):
        # Crear 2 administradores
        administradores_data = [
            {
                'email': 'admin@fitness.com',
                'nombre_usuario': 'admin_fitness',
                'nombre_completo': 'Administrador Principal',
                'password': 'admin123'
            },
            {
                'email': 'soporte@fitness.com',
                'nombre_usuario': 'soporte_tec',
                'nombre_completo': 'Soporte Técnico',
                'password': 'admin123'
            }
        ]

        for admin_data in administradores_data:
            if not Usuario.objects.filter(email=admin_data['email']).exists():
                usuario = Usuario.objects.create_user(
                    email=admin_data['email'],
                    nombre_usuario=admin_data['nombre_usuario'],
                    password=admin_data['password'],
                    nombre_completo=admin_data['nombre_completo'],
                    tipo_usuario='administrador',
                    is_staff=True,
                    is_superuser=True
                )
                
                # Crear perfil de salud para el administrador (opcional)
                PerfilSalud.objects.create(
                    usuario=usuario,
                    altura_cm=175.0,
                    peso_kg=70.0,
                    nivel_actividad='moderado',
                    objetivos_fitness='Mantener forma física y salud'
                )

        self.stdout.write(f"Administradores creados: {Usuario.objects.filter(tipo_usuario='administrador').count()}")

    def crear_usuarios_finales(self):
        # Crear 10 usuarios finales
        nivel_fisico_opciones = ['principiante', 'intermedio', 'avanzado']
        objetivos_fitness = [
            'Perder peso y ganar condición física',
            'Ganar masa muscular',
            'Mejorar resistencia cardiovascular',
            'Aumentar flexibilidad y movilidad',
            'Mantener salud general',
            'Preparación para competencia'
        ]

        for i in range(10):
            email = f'usuario{i+1}@fitness.com'
            nombre_usuario = f'usuario_fitness_{i+1}'
            
            if not Usuario.objects.filter(email=email).exists():
                # Crear usuario
                usuario = Usuario.objects.create_user(
                    email=email,
                    nombre_usuario=nombre_usuario,
                    password='usuario123',
                    nombre_completo=fake.name(),
                    tipo_usuario='usuario_final',
                    fecha_nacimiento=fake.date_of_birth(minimum_age=18, maximum_age=65),
                    nivel_fisico_actual=random.choice(nivel_fisico_opciones),
                    puntos_experiencia=random.randint(0, 2000),
                    cristales_magicos=random.randint(0, 500)
                )

                # Asignar rango basado en puntos de experiencia
                rango_adecuado = Rango.obtener_rango_por_puntos(usuario.puntos_experiencia)
                if rango_adecuado:
                    usuario.rango_actual = rango_adecuado
                    usuario.save()

                # Crear perfil de salud
                altura = random.uniform(150.0, 190.0)
                peso = random.uniform(50.0, 100.0)
                
                PerfilSalud.objects.create(
                    usuario=usuario,
                    altura_cm=round(altura, 2),
                    peso_kg=round(peso, 2),
                    condiciones_medicas=random.choice(['', 'Asma leve', 'Alergias estacionales', '']),
                    restricciones_ejercicio=random.choice(['', 'Evitar impacto alto', 'Limitación hombro derecho', '']),
                    nivel_actividad=random.choice(['sedentario', 'ligero', 'moderado', 'activo']),
                    objetivos_fitness=random.choice(objetivos_fitness)
                )

                # Crear dispositivo móvil simulado
                Dispositivo.objects.create(
                    usuario=usuario,
                    dispositivo_id=f"DEV_{usuario.id}_{fake.uuid4()[:8]}",
                    modelo_dispositivo=random.choice(['iPhone 14', 'Samsung Galaxy S23', 'Google Pixel 7', 'Xiaomi Redmi Note']),
                    sistema_operativo=random.choice(['ios', 'android']),
                    version_sistema=random.choice(['16.0', '15.0', '14.0', '13.0']),
                    token_notificaciones=fake.uuid4()
                )

                # Crear algunos logs de actividad iniciales
                for _ in range(random.randint(5, 15)):
                    LogActividad.objects.create(
                        usuario=usuario,
                        tipo_actividad=random.choice(['ejercicio', 'login', 'mision_completada', 'nivel_subido']),
                        descripcion=fake.sentence(),
                        puntos_ganados=random.randint(5, 50),
                        cristales_ganados=random.randint(1, 10),
                        fecha_actividad=fake.date_time_between(start_date='-30d', end_date='now', tzinfo=dt_timezone.utc)
                    )

        self.stdout.write(f"Usuarios finales creados: {Usuario.objects.filter(tipo_usuario='usuario_final').count()}")

    def crear_ejercicios(self):
        ejercicios_data = [
            # Fuerza
            {'nombre': 'Sentadillas', 'tipo': 'fuerza', 'grupo_muscular': 'piernas', 'duracion': 10, 'calorias': 8},
            {'nombre': 'Flexiones de pecho', 'tipo': 'fuerza', 'grupo_muscular': 'pecho', 'duracion': 10, 'calorias': 7},
            {'nombre': 'Plancha abdominal', 'tipo': 'fuerza', 'grupo_muscular': 'abdomen', 'duracion': 5, 'calorias': 5},
            {'nombre': 'Fondos en silla', 'tipo': 'fuerza', 'grupo_muscular': 'brazos', 'duracion': 8, 'calorias': 6},
            {'nombre': 'Zancadas', 'tipo': 'fuerza', 'grupo_muscular': 'piernas', 'duracion': 12, 'calorias': 9},
            
            # Cardio
            {'nombre': 'Burpees', 'tipo': 'cardio', 'grupo_muscular': 'full_body', 'duracion': 15, 'calorias': 12},
            {'nombre': 'Mountain Climbers', 'tipo': 'cardio', 'grupo_muscular': 'full_body', 'duracion': 10, 'calorias': 10},
            {'nombre': 'Saltos de estrella', 'tipo': 'cardio', 'grupo_muscular': 'full_body', 'duracion': 8, 'calorias': 9},
            {'nombre': 'Correr en el lugar', 'tipo': 'cardio', 'grupo_muscular': 'cardiovascular', 'duracion': 10, 'calorias': 8},
            
            # Flexibilidad
            {'nombre': 'Estiramiento de espalda', 'tipo': 'flexibilidad', 'grupo_muscular': 'espalda', 'duracion': 5, 'calorias': 3},
            {'nombre': 'Estiramiento de piernas', 'tipo': 'flexibilidad', 'grupo_muscular': 'piernas', 'duracion': 5, 'calorias': 3},
            {'nombre': 'Postura del niño', 'tipo': 'flexibilidad', 'grupo_muscular': 'espalda', 'duracion': 3, 'calorias': 2},
            {'nombre': 'Estiramiento de hombros', 'tipo': 'flexibilidad', 'grupo_muscular': 'hombros', 'duracion': 4, 'calorias': 2},
        ]

        for ej_data in ejercicios_data:
            Ejercicio.objects.get_or_create(
                nombre=ej_data['nombre'],
                defaults={
                    'descripcion': f'Ejercicio de {ej_data["tipo"]} para {ej_data["grupo_muscular"]}',
                    'tipo': ej_data['tipo'],
                    'grupo_muscular': ej_data['grupo_muscular'],
                    'instrucciones': f'Realizar el ejercicio {ej_data["nombre"]} con técnica adecuada',
                    'video_url': f'https://ejemplo.com/videos/{ej_data["nombre"].lower().replace(" ", "_")}.mp4',
                    'imagen_url': f'https://ejemplo.com/images/{ej_data["nombre"].lower().replace(" ", "_")}.jpg',
                    'duracion_estimada_minutos': ej_data['duracion'],
                    'calorias_estimadas_por_minuto': ej_data['calorias']
                }
            )
        self.stdout.write(f"Ejercicios creados: {Ejercicio.objects.count()}")

    def crear_rutinas(self):
        administradores = Usuario.objects.filter(tipo_usuario='administrador')
        ejercicios = list(Ejercicio.objects.all())
        
        rutinas_data = [
            {
                'nombre': 'Rutina Principiante Full Body',
                'nivel': 'principiante',
                'tipo': 'completo',
                'duracion': 30,
                'calorias': 180
            },
            {
                'nombre': 'Rutina Intermedia Fuerza',
                'nivel': 'intermedio', 
                'tipo': 'fuerza',
                'duracion': 45,
                'calorias': 250
            },
            {
                'nombre': 'Rutina Avanzada Cardio',
                'nivel': 'avanzado',
                'tipo': 'cardio',
                'duracion': 40,
                'calorias': 320
            },
            {
                'nombre': 'Rutina Flexibilidad Diaria',
                'nivel': 'principiante',
                'tipo': 'flexibilidad',
                'duracion': 20,
                'calorias': 80
            }
        ]

        for rutina_data in rutinas_data:
            rutina, created = Rutina.objects.get_or_create(
                nombre=rutina_data['nombre'],
                defaults={
                    'descripcion': f'Rutina de {rutina_data["tipo"]} para nivel {rutina_data["nivel"]}',
                    'nivel_dificultad': rutina_data['nivel'],
                    'duracion_minutos': rutina_data['duracion'],
                    'tipo_ejercicio': rutina_data['tipo'],
                    'calorias_estimadas': rutina_data['calorias'],
                    'creador': random.choice(administradores),
                    'es_publica': True
                }
            )

            if created:
                # Agregar ejercicios a la rutina
                ejercicios_rutina = random.sample(ejercicios, k=random.randint(4, 8))
                for orden, ejercicio in enumerate(ejercicios_rutina, 1):
                    RutinaEjercicio.objects.create(
                        rutina=rutina,
                        ejercicio=ejercicio,
                        orden=orden,
                        series=random.randint(3, 5),
                        repeticiones=f"{random.randint(8, 15)}-{random.randint(12, 20)}",
                        descanso_segundos=random.choice([30, 45, 60]),
                        peso_sugerido=random.choice([None, 5.0, 10.0, 15.0])
                    )

        self.stdout.write(f"Rutinas creadas: {Rutina.objects.count()}")

    def crear_misiones(self):
        misiones_data = [
            {
                'titulo': 'Primeros Pasos',
                'tipo': 'ejercicio',
                'objetivo': 5,
                'unidad': 'veces',
                'xp': 100,
                'cristales': 20
            },
            {
                'titulo': 'Consistencia Semanal',
                'tipo': 'rutina',
                'objetivo': 3,
                'unidad': 'rutinas',
                'xp': 200,
                'cristales': 50
            },
            {
                'titulo': 'Quema Calórica',
                'tipo': 'ejercicio', 
                'objetivo': 1000,
                'unidad': 'calorias',
                'xp': 150,
                'cristales': 30
            },
            {
                'titulo': 'Reto de Fuerza',
                'tipo': 'ejercicio',
                'objetivo': 50,
                'unidad': 'repeticiones',
                'xp': 180,
                'cristales': 40
            }
        ]

        for mision_data in misiones_data:
            Mision.objects.get_or_create(
                titulo=mision_data['titulo'],
                defaults={
                    'descripcion': f'Completa {mision_data["objetivo"]} {mision_data["unidad"]} de actividad',
                    'tipo_mision': mision_data['tipo'],
                    'objetivo': mision_data['objetivo'],
                    'unidad_objetivo': mision_data['unidad'],
                    'recompensa_xp': mision_data['xp'],
                    'recompensa_cristales': mision_data['cristales'],
                    'fecha_inicio': timezone.now().date(),
                    'fecha_fin': timezone.now().date() + timedelta(days=30),
                    'esta_activa': True,
                    'dificultad': random.choice(['facil', 'medio', 'dificil'])
                }
            )
        self.stdout.write(f"Misiones creadas: {Mision.objects.count()}")

    def crear_cartas_ejercicios(self):
        ejercicios = Ejercicio.objects.all()
        rarezas = ['comun', 'rara', 'epica', 'legendaria']
        
        for ejercicio in ejercicios:
            rareza = random.choice(rarezas)
            precio_base = {'comun': 50, 'rara': 100, 'epica': 200, 'legendaria': 500}
            
            CartaEjercicio.objects.get_or_create(
                ejercicio=ejercicio,
                defaults={
                    'nombre': f"Carta de {ejercicio.nombre}",
                    'descripcion': f"Carta coleccionable del ejercicio {ejercicio.nombre}",
                    'rareza': rareza,
                    'atributo_fuerza': random.randint(1, 10),
                    'atributo_resistencia': random.randint(1, 10),
                    'atributo_flexibilidad': random.randint(1, 10),
                    'precio_cristales': precio_base[rareza],
                    'esta_activa': True
                }
            )
        self.stdout.write(f"Cartas de ejercicio creadas: {CartaEjercicio.objects.count()}")

    def crear_items_coleccionables(self):
        items_data = [
            {'nombre': 'Avatar Básico', 'tipo': 'avatar', 'rareza': 'comun', 'precio': 100},
            {'nombre': 'Marco Dorado', 'tipo': 'marco', 'rareza': 'rara', 'precio': 200},
            {'nombre': 'Fondo Montañas', 'tipo': 'fondo', 'rareza': 'comun', 'precio': 150},
            {'nombre': 'Insignia Principiante', 'tipo': 'badge', 'rareza': 'comun', 'precio': 50},
            {'nombre': 'Efecto Estrellas', 'tipo': 'efecto', 'rareza': 'epica', 'precio': 300},
            {'nombre': 'Tema Oscuro', 'tipo': 'tema', 'rareza': 'rara', 'precio': 250},
        ]

        for item_data in items_data:
            ItemColeccionable.objects.get_or_create(
                nombre=item_data['nombre'],
                defaults={
                    'descripcion': f'Item {item_data["tipo"]} de rareza {item_data["rareza"]}',
                    'tipo_item': item_data['tipo'],
                    'rareza': item_data['rareza'],
                    'precio_cristales': item_data['precio'],
                    'esta_activo': True
                }
            )
        self.stdout.write(f"Items coleccionables creados: {ItemColeccionable.objects.count()}")

    def crear_modelos_ia(self):
        modelos_data = [
            {'nombre': 'pose_sentadilla_v1', 'ejercicio': 'sentadilla', 'version': '1.0'},
            {'nombre': 'pose_flexiones_v1', 'ejercicio': 'flexiones', 'version': '1.0'},
            {'nombre': 'pose_plancha_v1', 'ejercicio': 'plancha', 'version': '1.0'},
        ]

        for modelo_data in modelos_data:
            ModeloIA.objects.get_or_create(
                nombre_modelo=modelo_data['nombre'],
                defaults={
                    'tipo_ejercicio': modelo_data['ejercicio'],
                    'version': modelo_data['version'],
                    'puntos_referencia': {'keypoints': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]},
                    'angulos_ideales': {'angulo_rodilla': 90, 'angulo_cadera': 85},
                    'umbral_precision': 0.75,
                    'esta_activo': True,
                    'accuracy_entrenamiento': round(random.uniform(0.85, 0.95), 2)
                }
            )
        self.stdout.write(f"Modelos IA creados: {ModeloIA.objects.count()}")