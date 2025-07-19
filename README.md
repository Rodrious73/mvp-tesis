# Sistema de Gestión de Tesis Digital - UNJFSC

MVP (Producto Mínimo Viable) para digitalizar el ciclo de vida de las tesis en la Universidad Nacional José Faustino Sánchez Carrión.

## Características

- **Autenticación por roles**: Estudiante, Docente, Administrador
- **Gestión de tesis**: Registro, revisión, aprobación/rechazo
- **Panel personalizado** por tipo de usuario
- **Notificaciones** de cambios de estado
- **Gestión de documentos** con subida de archivos

## Tecnologías

- Backend: Flask + SQLAlchemy
- Base de datos: SQLite
- Frontend: HTML + CSS (Bootstrap) + Jinja2
- Autenticación: JWT

## Instalación y Ejecución

1. Clonar el repositorio:
```bash
git clone <repo-url>
cd mvp-tesis
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. Inicializar la base de datos:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Ejecutar la aplicación:
```bash
flask run
```

La aplicación estará disponible en `http://localhost:5000`

## Estructura del Proyecto

```
mvp-tesis/
├── app/
│   ├── __init__.py          # Configuración de la aplicación
│   ├── models/              # Modelos de base de datos
│   ├── routes/              # Rutas y controladores
│   ├── services/            # Lógica de negocio
│   ├── templates/           # Plantillas HTML
│   └── static/              # Archivos estáticos (CSS, JS)
├── migrations/              # Migraciones de base de datos
├── uploads/                 # Archivos subidos
├── config.py               # Configuración
├── run.py                  # Punto de entrada
├── requirements.txt        # Dependencias
└── .env                    # Variables de entorno
```

## Usuarios por defecto

### Administrador
- Email: admin@unjfsc.edu.pe
- Password: admin123

### Docente
- Email: docente@unjfsc.edu.pe
- Password: docente123

### Estudiante
- Email: estudiante@unjfsc.edu.pe
- Password: estudiante123

## Funcionalidades por Rol

### Estudiante
- Registrar propuesta de tesis
- Subir documentos
- Ver estado y observaciones
- Recibir notificaciones

### Docente
- Revisar propuestas asignadas
- Aprobar/rechazar tesis
- Agregar comentarios y observaciones
- Ver historial de revisiones

### Administrador
- Gestionar usuarios
- Asignar asesores y jurados
- Ver estadísticas del sistema
- Gestionar configuraciones

## Contribuir

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT.
