import requests
from io import BytesIO
from pathlib import Path
from typing import List, Tuple, Optional
from .utils import setup_logger, extract_domain
from .config import Config

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

try:
    from pyvis.network import Network
    import networkx as nx
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False

logger = setup_logger(__name__)


class VisionSystem:
    """Handles face recognition and network graph visualization"""

    def __init__(self, known_image_path: Optional[Path] = None):
        self.known_encoding = None
        self.face_available = FACE_RECOGNITION_AVAILABLE

        if not self.face_available:
            logger.warning("face_recognition not available. Face verification disabled.")
            return

        if known_image_path and known_image_path.exists():
            logger.info(f"Loading target face from {known_image_path}")
            try:
                image = face_recognition.load_image_file(str(known_image_path))
                encodings = face_recognition.face_encodings(image)

                if encodings:
                    self.known_encoding = encodings[0]
                    logger.info("Target face loaded successfully")
                else:
                    logger.warning("No face detected in target image")
            except Exception as e:
                logger.error(f"Error loading target face: {str(e)}")

    def verify_face(self, image_url: str, tolerance: float = 0.6) -> bool:
        """
        Download image from URL and verify if it matches target face

        Args:
            image_url: URL of image to check
            tolerance: Lower = stricter matching (default 0.6)

        Returns:
            True if faces match, False otherwise
        """
        if not self.face_available or self.known_encoding is None:
            return True  # Skip verification if not configured

        try:
            logger.debug(f"Verifying face from {image_url}")
            response = requests.get(image_url, timeout=10)

            if response.status_code != 200:
                logger.debug(f"Failed to download image: {response.status_code}")
                return False

            # Load image from response content
            unknown_image = face_recognition.load_image_file(BytesIO(response.content))
            unknown_encodings = face_recognition.face_encodings(unknown_image)

            if not unknown_encodings:
                logger.debug("No face found in downloaded image")
                return False

            # Compare faces
            matches = face_recognition.compare_faces(
                [self.known_encoding],
                unknown_encodings[0],
                tolerance=tolerance
            )

            result = matches[0] if matches else False
            logger.debug(f"Face match result: {result}")
            return result

        except Exception as e:
            logger.debug(f"Face verification error: {str(e)}")
            return False

    def generate_graph(
        self,
        target_name: str,
        connections: List[Tuple[str, str]],
        output_path: Path
    ) -> bool:
        """
        Create interactive network graph visualization

        Args:
            target_name: Central node (the target)
            connections: List of (source, destination) tuples
            output_path: Where to save HTML file

        Returns:
            True if successful
        """
        if not GRAPH_AVAILABLE:
            logger.error("pyvis/networkx not available. Cannot generate graph.")
            return False

        try:
            logger.info(f"Generating network graph for {target_name}")

            # Create network
            net = Network(
                height="750px",
                width="100%",
                bgcolor="#1a1a1a",
                font_color="#ffffff",
                directed=False
            )

            # Configure physics for better visualization
            net.set_options("""
            {
              "nodes": {
                "font": {"size": 16}
              },
              "edges": {
                "color": {"inherit": true},
                "smooth": {"type": "continuous"}
              },
              "physics": {
                "enabled": true,
                "stabilization": {"iterations": 200}
              }
            }
            """)

            # Add central target node
            net.add_node(
                target_name,
                label=target_name,
                color="#ff4444",
                size=40,
                title=f"Target: {target_name}"
            )

            # Add connection nodes and edges
            for source, destination in connections:
                # Add source node
                net.add_node(
                    source,
                    label=source,
                    color="#44ff44",
                    size=25,
                    title=f"Platform: {source}"
                )

                # Add edge
                net.add_edge(target_name, source, color="#888888")

                # If destination is different, add it too
                if destination != source:
                    net.add_node(
                        destination,
                        label=destination,
                        color="#4444ff",
                        size=20,
                        title=f"Related: {destination}"
                    )
                    net.add_edge(source, destination, color="#666666")

            # Save graph
            output_path.parent.mkdir(parents=True, exist_ok=True)
            net.save_graph(str(output_path))

            logger.info(f"Graph saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Graph generation error: {str(e)}")
            return False
