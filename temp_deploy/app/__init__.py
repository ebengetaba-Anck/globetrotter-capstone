from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'microservices-secret-key-change-in-prod'
    return app
    
    # Enregistrer les blueprints
    from app.main import main_bp
    app.register_blueprint(main_bp)
    
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from app.recommendations import recommendations_bp
    app.register_blueprint(recommendations_bp)
    
    from app.itineraries import itineraries_bp
    app.register_blueprint(itineraries_bp)
    
    from app.favorites import favorites_bp
    app.register_blueprint(favorites_bp)
    
    from app.reviews import reviews_bp
    app.register_blueprint(reviews_bp)
    
    from app.destinations import destinations_bp
    app.register_blueprint(destinations_bp)
    
    from app.transport import transport_bp
    app.register_blueprint(transport_bp)
    
    from app.activities import activities_bp
    app.register_blueprint(activities_bp)
    
    return app