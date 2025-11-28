"""Flask application factory."""
import logging
from flask import Flask, jsonify
from app.config import DevelopmentConfig
from app.extensions import db, cors


def create_app(config_class=DevelopmentConfig):
    """
    Create and configure Flask application.

    Args:
        config_class: Configuration class to use

    Returns:
        Configured Flask app
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize extensions
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from app.routes import tasks, progress, leds, projects, sprints, user_stories, gauges, admin, taiga
    app.register_blueprint(tasks.bp)
    app.register_blueprint(progress.bp)
    app.register_blueprint(leds.bp)
    app.register_blueprint(projects.bp)
    app.register_blueprint(sprints.bp)
    app.register_blueprint(user_stories.bp)
    app.register_blueprint(gauges.bp)
    app.register_blueprint(admin.admin_bp)
    app.register_blueprint(taiga.bp)

    # Create database tables (no demo data seeding)
    with app.app_context():
        db.create_all()

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': str(e)}), 400

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Internal server error'}), 500

    # Health check endpoints (both with and without /api prefix)
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'}), 200

    @app.route('/api/health')
    def api_health():
        return jsonify({'status': 'ok'}), 200

    logging.info("Flask app created successfully")
    return app
