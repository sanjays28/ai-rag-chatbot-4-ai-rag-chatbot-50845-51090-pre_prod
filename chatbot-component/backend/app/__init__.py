from flask import Flask, jsonify
from .monitoring import init_monitoring, get_monitoring_stats

def create_app():
    app = Flask(__name__)
    
    # Initialize monitoring
    init_monitoring(app)

    @app.route('/')
    def hello():
        return {'message': 'Hello from Chatbot API!'}

    @app.route('/monitoring/stats')
    def monitoring_stats():
        """Get current monitoring statistics."""
        return jsonify(get_monitoring_stats())

    return app
