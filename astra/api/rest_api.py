"""REST API server for Astra Headend."""

from flask import Flask, jsonify, request
from flask_cors import CORS
from typing import Dict, Any
import threading
from astra.utils.logger import get_logger

logger = get_logger(__name__)


class AstraAPI:
    """REST API server for Astra Headend."""

    def __init__(self, headend, host: str = '0.0.0.0', port: int = 5000):
        """Initialize API server.
        
        Args:
            headend: AstraHeadend instance
            host: API server host
            port: API server port
        """
        self.headend = headend
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        
        self._register_routes()
        logger.info(f"Astra API initialized: {host}:{port}")

    def _register_routes(self):
        """Register API routes."""
        
        @self.app.route('/api/v1/health', methods=['GET'])
        def health():
            """Health check endpoint."""
            return jsonify({'status': 'ok', 'service': 'astra-headend'})
        
        @self.app.route('/api/v1/status', methods=['GET'])
        def get_status():
            """Get system status."""
            return jsonify(self.headend.get_status())
        
        @self.app.route('/api/v1/config', methods=['GET'])
        def get_config():
            """Get system configuration."""
            return jsonify(self.headend.to_dict())
        
        @self.app.route('/api/v1/channels', methods=['GET'])
        def list_channels():
            """List all channels."""
            channels = self.headend.list_channels()
            return jsonify({
                'channels': [ch.to_dict() for ch in channels]
            })
        
        @self.app.route('/api/v1/channels/<name>', methods=['GET'])
        def get_channel(name):
            """Get channel details."""
            channel = self.headend.get_channel(name)
            if not channel:
                return jsonify({'error': 'Channel not found'}), 404
            return jsonify(channel.to_dict())
        
        @self.app.route('/api/v1/channels', methods=['POST'])
        def create_channel():
            """Create new channel."""
            data = request.get_json()
            
            from astra.core.headend import Channel
            channel = Channel(
                name=data.get('name'),
                service_id=data.get('service_id'),
                video_pid=data.get('video_pid'),
                audio_pids=data.get('audio_pids', []),
            )
            
            if self.headend.add_channel(channel):
                return jsonify(channel.to_dict()), 201
            else:
                return jsonify({'error': 'Channel already exists'}), 409
        
        @self.app.route('/api/v1/channels/<name>', methods=['DELETE'])
        def delete_channel(name):
            """Delete channel."""
            if self.headend.remove_channel(name):
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Channel not found'}), 404
        
        @self.app.route('/api/v1/sources', methods=['GET'])
        def list_sources():
            """List all input sources."""
            sources = self.headend.list_input_sources()
            return jsonify({
                'sources': [src.to_dict() for src in sources]
            })
        
        @self.app.route('/api/v1/sources', methods=['POST'])
        def create_source():
            """Create new input source."""
            data = request.get_json()
            
            from astra.core.headend import InputSource, SourceType
            source = InputSource(
                name=data.get('name'),
                source_type=SourceType(data.get('type')),
                uri=data.get('uri'),
                adapter=data.get('adapter'),
                frequency=data.get('frequency'),
                symbol_rate=data.get('symbol_rate'),
            )
            
            if self.headend.add_input_source(source):
                return jsonify(source.to_dict()), 201
            else:
                return jsonify({'error': 'Source already exists'}), 409
        
        @self.app.route('/api/v1/sources/<name>', methods=['DELETE'])
        def delete_source(name):
            """Delete input source."""
            if self.headend.remove_input_source(name):
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Source not found'}), 404
        
        @self.app.route('/api/v1/outputs', methods=['GET'])
        def list_outputs():
            """List all output targets."""
            outputs = self.headend.list_output_targets()
            return jsonify({
                'outputs': [out.to_dict() for out in outputs]
            })
        
        @self.app.route('/api/v1/outputs', methods=['POST'])
        def create_output():
            """Create new output target."""
            data = request.get_json()
            
            from astra.core.headend import OutputTarget, OutputType
            output = OutputTarget(
                name=data.get('name'),
                output_type=OutputType(data.get('type')),
                uri=data.get('uri'),
                channels=data.get('channels', []),
            )
            
            if self.headend.add_output_target(output):
                return jsonify(output.to_dict()), 201
            else:
                return jsonify({'error': 'Output already exists'}), 409
        
        @self.app.route('/api/v1/outputs/<name>', methods=['DELETE'])
        def delete_output(name):
            """Delete output target."""
            if self.headend.remove_output_target(name):
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Output not found'}), 404
        
        @self.app.route('/api/v1/system/start', methods=['POST'])
        def start_system():
            """Start headend system."""
            self.headend.start()
            return jsonify({'status': 'started'})
        
        @self.app.route('/api/v1/system/stop', methods=['POST'])
        def stop_system():
            """Stop headend system."""
            self.headend.stop()
            return jsonify({'status': 'stopped'})
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"API error: {error}")
            return jsonify({'error': 'Internal server error'}), 500

    def start(self):
        """Start API server."""
        logger.info(f"Starting API server on {self.host}:{self.port}")
        self.api_thread = threading.Thread(
            target=lambda: self.app.run(
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False
            ),
            daemon=True
        )
        self.api_thread.start()

    def stop(self):
        """Stop API server."""
        logger.info("Stopping API server")

    def __repr__(self) -> str:
        return f"AstraAPI({self.host}:{self.port})"
