# run.py
from app import create_app
from config import DevelopmentConfig, ProductionConfig
import os

# Choose config based on an environment variable, e.g., FLASK_ENV
if os.environ.get('FLASK_ENV') == 'production':
    app_config = ProductionConfig()
else:
    app_config = DevelopmentConfig()

app = create_app(app_config)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050) # Debug is controlled by app_config.DEBUG