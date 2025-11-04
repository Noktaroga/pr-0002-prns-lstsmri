"""
Flask Sitemap Integration
========================

Integrates sitemap generation with Flask backend.
Provides dynamic sitemap endpoints and automatic regeneration.
"""

from flask import Flask, Response, request, jsonify
from generate_sitemap import SitemapGenerator
import os
from datetime import datetime, timedelta
from pathlib import Path


class FlaskSitemapIntegration:
    """Flask integration for dynamic sitemap generation."""
    
    def __init__(self, app: Flask, config_path: str = None):
        self.app = app
        self.generator = SitemapGenerator(config_path)
        self.cache = {}
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
        
        self._register_routes()
    
    def _register_routes(self):
        """Register sitemap routes with Flask."""
        
        @self.app.route('/sitemap.xml')
        def main_sitemap():
            """Serve main sitemap index."""
            return self._serve_sitemap('main', self.generator.generate_main_sitemap)
        
        @self.app.route('/sitemap-main.xml')
        def main_pages_sitemap():
            """Serve main pages sitemap."""
            return self._serve_sitemap('main-pages', self.generator.generate_main_pages_sitemap)
        
        @self.app.route('/sitemap-videos.xml')
        def videos_sitemap():
            """Serve videos sitemap."""
            limit = request.args.get('limit', type=int)
            return self._serve_sitemap('videos', lambda: self.generator.generate_videos_sitemap(limit))
        
        @self.app.route('/sitemap-categories.xml')
        def categories_sitemap():
            """Serve categories sitemap."""
            return self._serve_sitemap('categories', self.generator.generate_categories_sitemap)
        
        @self.app.route('/sitemap-performers.xml')
        def performers_sitemap():
            """Serve performers sitemap."""
            return self._serve_sitemap('performers', self.generator.generate_performers_sitemap)
        
        @self.app.route('/api/sitemaps/generate', methods=['POST'])
        def regenerate_sitemaps():
            """API endpoint to regenerate all sitemaps."""
            try:
                # Clear cache
                self.cache.clear()
                
                # Generate new sitemaps
                output_dir = request.json.get('output_dir', 'sitemaps')
                results = self.generator.generate_all_sitemaps(output_dir)
                
                return jsonify({
                    'success': True,
                    'message': f'Generated {len(results)} sitemaps',
                    'files': results,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/sitemaps/status')
        def sitemap_status():
            """Get sitemap generation status and cache info."""
            cache_info = {}
            for key, (content, timestamp) in self.cache.items():
                age = datetime.now() - timestamp
                cache_info[key] = {
                    'cached': True,
                    'age_seconds': age.total_seconds(),
                    'expires_in': (self.cache_duration - age).total_seconds(),
                    'size_bytes': len(content)
                }
            
            return jsonify({
                'domain': self.generator.domain,
                'cache_duration_hours': self.cache_duration.total_seconds() / 3600,
                'cached_sitemaps': cache_info
            })
    
    def _serve_sitemap(self, cache_key: str, generator_func):
        """Serve sitemap with caching."""
        now = datetime.now()
        
        # Check cache
        if cache_key in self.cache:
            content, timestamp = self.cache[cache_key]
            if now - timestamp < self.cache_duration:
                return Response(content, mimetype='application/xml')
        
        # Generate new content
        try:
            content = generator_func()
            self.cache[cache_key] = (content, now)
            
            return Response(content, mimetype='application/xml')
        except Exception as e:
            return Response(f"Error generating sitemap: {e}", status=500)


# Example usage in app.py
def setup_sitemaps(app: Flask):
    """Setup sitemap integration with Flask app."""
    config_path = os.path.join(os.path.dirname(__file__), 'sitemap.config.json')
    sitemap_integration = FlaskSitemapIntegration(app, config_path)
    return sitemap_integration


# Example standalone app for testing
if __name__ == "__main__":
    app = Flask(__name__)
    
    # Setup sitemaps
    setup_sitemaps(app)
    
    @app.route('/')
    def index():
        return '''
        <h1>Sitemap Testing</h1>
        <ul>
            <li><a href="/sitemap.xml">Main Sitemap</a></li>
            <li><a href="/sitemap-videos.xml">Videos Sitemap</a></li>
            <li><a href="/sitemap-categories.xml">Categories Sitemap</a></li>
            <li><a href="/api/sitemaps/status">Sitemap Status API</a></li>
        </ul>
        '''
    
    app.run(debug=True, port=3001)