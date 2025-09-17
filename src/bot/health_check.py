"""
Health check endpoint for monitoring
"""
from flask import Flask, jsonify
from utils.monitoring import get_health_status, monitor
import logging

logger = logging.getLogger(__name__)

def create_health_app() -> Flask:
    """Create Flask app for health checks"""
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        try:
            status = get_health_status()
            return jsonify(status), 200 if status['status'] == 'healthy' else 503
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint"""
        try:
            stats = monitor.get_stats()
            
            # Simple Prometheus format
            metrics = []
            for key, value in stats.items():
                if isinstance(value, (int, float)):
                    metrics.append(f"rasch_bot_{key} {value}")
            
            return '\n'.join(metrics), 200, {'Content-Type': 'text/plain'}
        except Exception as e:
            logger.error(f"Metrics error: {str(e)}")
            return f"# Error: {str(e)}", 500, {'Content-Type': 'text/plain'}
    
    @app.route('/stats')
    def stats():
        """Detailed stats endpoint"""
        try:
            stats = monitor.get_stats()
            return jsonify(stats), 200
        except Exception as e:
            logger.error(f"Stats error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return app
