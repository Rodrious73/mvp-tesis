#!/usr/bin/env python3
"""
Sistema de Gestión de Tesis Digital - UNJFSC
Punto de entrada de la aplicación Flask
"""

import os
from app import create_app

# Crear la aplicación Flask
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # Crear directorio de uploads si no existe
    upload_dir = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # Ejecutar la aplicación
    app.run(debug=True, host='0.0.0.0', port=5000)
