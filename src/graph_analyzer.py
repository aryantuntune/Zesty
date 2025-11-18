"""
Social Network Graph Analyzer: Advanced graph theory analysis
Detects communities, central nodes, and relationship patterns
"""

from typing import List, Dict, Set, Tuple
from collections import defaultdict
import statistics
from .utils import setup_logger

logger = setup_logger(__name__)

# Try to import NetworkX
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
    logger.info("NetworkX available for advanced graph analysis")
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not installed. Install with: pip install networkx")
    # We'll implement basic graph analysis without it


class SocialGraphAnalyzer:
    """
    Analyzes social network graphs using graph theory

    Features:
    - Community detection (find clusters of related accounts)
    - Centrality analysis (find most important nodes)
    - Connection strength analysis
    - Anomaly detection (bot networks, fake accounts)
    """

    def __init__(self):
        self.use_networkx = NETWORKX_AVAILABLE

    def build_graph_from_connections(self, connections: List[Tuple]) -> Dict:
        """
        Build graph structure from connection list

        Args:
            connections: List of (source, target) tuples

        Returns:
            Graph data structure
        """
        if self.use_networkx:
            return self._build_networkx_graph(connections)
        else:
            return self._build_simple_graph(connections)

    def _build_networkx_graph(self, connections: List[Tuple]):
        """Build NetworkX graph"""
        G = nx.DiGraph()

        for source, target in connections:
            G.add_edge(source, target)

        logger.info(f"Built NetworkX graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        return G

    def _build_simple_graph(self, connections: List[Tuple]) -> Dict:
        """Build simple adjacency list graph (fallback)"""
        graph = {
            'nodes': set(),
            'edges': defaultdict(set),
            'reverse_edges': defaultdict(set)
        }

        for source, target in connections:
            graph['nodes'].add(source)
            graph['nodes'].add(target)
            graph['edges'][source].add(target)
            graph['reverse_edges'][target].add(source)

        logger.info(f"Built simple graph: {len(graph['nodes'])} nodes, {len(connections)} edges")

        return graph

    def detect_communities(self, graph) -> List[Set]:
        """
        Detect communities (clusters) in the graph

        Returns:
            List of communities (each is a set of nodes)
        """
        if self.use_networkx:
            return self._detect_communities_networkx(graph)
        else:
            return self._detect_communities_simple(graph)

    def _detect_communities_networkx(self, G) -> List[Set]:
        """Community detection using NetworkX algorithms"""
        try:
            # Convert to undirected for community detection
            G_undirected = G.to_undirected()

            # Use greedy modularity communities
            from networkx.algorithms import community
            communities = community.greedy_modularity_communities(G_undirected)

            logger.info(f"Detected {len(communities)} communities using NetworkX")

            return [set(c) for c in communities]

        except Exception as e:
            logger.warning(f"NetworkX community detection failed: {e}")
            return []

    def _detect_communities_simple(self, graph: Dict) -> List[Set]:
        """
        Simple community detection using connected components
        """
        visited = set()
        communities = []

        def dfs(node, community):
            """Depth-first search to find connected component"""
            if node in visited:
                return

            visited.add(node)
            community.add(node)

            # Check outgoing edges
            for neighbor in graph['edges'].get(node, []):
                dfs(neighbor, community)

            # Check incoming edges
            for neighbor in graph['reverse_edges'].get(node, []):
                dfs(neighbor, community)

        # Find all connected components
        for node in graph['nodes']:
            if node not in visited:
                community = set()
                dfs(node, community)
                if community:
                    communities.append(community)

        logger.info(f"Detected {len(communities)} communities using DFS")

        return communities

    def calculate_centrality(self, graph) -> Dict[str, float]:
        """
        Calculate centrality scores (importance) for each node

        Returns:
            {node_name: centrality_score}
        """
        if self.use_networkx:
            return self._calculate_centrality_networkx(graph)
        else:
            return self._calculate_centrality_simple(graph)

    def _calculate_centrality_networkx(self, G) -> Dict[str, float]:
        """Calculate centrality using NetworkX algorithms"""
        try:
            # PageRank centrality
            centrality = nx.pagerank(G)

            logger.info("Calculated PageRank centrality")

            return centrality

        except Exception as e:
            logger.warning(f"NetworkX centrality calculation failed: {e}")
            return {}

    def _calculate_centrality_simple(self, graph: Dict) -> Dict[str, float]:
        """
        Simple degree centrality (number of connections)
        """
        centrality = {}

        for node in graph['nodes']:
            # Count both incoming and outgoing edges
            out_degree = len(graph['edges'].get(node, []))
            in_degree = len(graph['reverse_edges'].get(node, []))

            # Total degree
            degree = out_degree + in_degree

            centrality[node] = degree

        # Normalize to 0-1
        max_degree = max(centrality.values()) if centrality else 1

        for node in centrality:
            centrality[node] = centrality[node] / max_degree

        logger.info("Calculated degree centrality")

        return centrality

    def find_central_nodes(self, graph, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Find most central (important) nodes

        Returns:
            List of (node_name, centrality_score) sorted by importance
        """
        centrality = self.calculate_centrality(graph)

        # Sort by centrality score
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)

        return sorted_nodes[:top_n]

    def analyze_connection_strength(self, graph, node1: str, node2: str) -> Dict:
        """
        Analyze strength of connection between two nodes

        Returns:
            {
                'direct_connection': bool,
                'distance': int,  # Shortest path length
                'common_neighbors': List[str],
                'strength_score': float  # 0-1
            }
        """
        if self.use_networkx:
            return self._analyze_connection_networkx(graph, node1, node2)
        else:
            return self._analyze_connection_simple(graph, node1, node2)

    def _analyze_connection_networkx(self, G, node1: str, node2: str) -> Dict:
        """Connection analysis using NetworkX"""
        try:
            # Check direct connection
            direct = G.has_edge(node1, node2) or G.has_edge(node2, node1)

            # Shortest path
            try:
                distance = nx.shortest_path_length(G.to_undirected(), node1, node2)
            except nx.NetworkXNoPath:
                distance = float('inf')

            # Common neighbors
            neighbors1 = set(G.neighbors(node1))
            neighbors2 = set(G.neighbors(node2))
            common = list(neighbors1.intersection(neighbors2))

            # Strength score
            if direct:
                strength = 1.0
            elif distance == 2:
                strength = 0.7
            elif distance == 3:
                strength = 0.4
            elif distance < float('inf'):
                strength = 1.0 / distance
            else:
                strength = 0.0

            # Boost by common neighbors
            strength += len(common) * 0.1
            strength = min(strength, 1.0)

            return {
                'direct_connection': direct,
                'distance': distance if distance != float('inf') else -1,
                'common_neighbors': common[:10],
                'strength_score': round(strength, 2)
            }

        except Exception as e:
            logger.warning(f"Connection analysis failed: {e}")
            return {
                'direct_connection': False,
                'distance': -1,
                'common_neighbors': [],
                'strength_score': 0.0
            }

    def _analyze_connection_simple(self, graph: Dict, node1: str, node2: str) -> Dict:
        """Simple connection analysis using BFS"""

        # Check direct connection
        direct = node2 in graph['edges'].get(node1, []) or \
                 node1 in graph['edges'].get(node2, [])

        # BFS to find shortest path
        distance = self._bfs_distance(graph, node1, node2)

        # Find common neighbors
        neighbors1 = graph['edges'].get(node1, set()) | graph['reverse_edges'].get(node1, set())
        neighbors2 = graph['edges'].get(node2, set()) | graph['reverse_edges'].get(node2, set())
        common = list(neighbors1.intersection(neighbors2))

        # Strength score
        if direct:
            strength = 1.0
        elif distance == 2:
            strength = 0.7
        elif distance == 3:
            strength = 0.4
        elif distance > 0:
            strength = 1.0 / distance
        else:
            strength = 0.0

        strength += len(common) * 0.1
        strength = min(strength, 1.0)

        return {
            'direct_connection': direct,
            'distance': distance,
            'common_neighbors': common[:10],
            'strength_score': round(strength, 2)
        }

    def _bfs_distance(self, graph: Dict, start: str, end: str, max_depth: int = 5) -> int:
        """BFS to find shortest path distance"""
        if start == end:
            return 0

        visited = {start}
        queue = [(start, 0)]

        while queue:
            node, depth = queue.pop(0)

            if depth >= max_depth:
                break

            # Check neighbors (both directions)
            neighbors = graph['edges'].get(node, set()) | graph['reverse_edges'].get(node, set())

            for neighbor in neighbors:
                if neighbor == end:
                    return depth + 1

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

        return -1  # Not connected

    def detect_anomalies(self, graph, communities: List[Set]) -> Dict:
        """
        Detect anomalous patterns that might indicate:
        - Bot networks
        - Fake accounts
        - Suspicious clustering

        Returns:
            {
                'isolated_nodes': List[str],
                'dense_clusters': List[Set],
                'suspicious_patterns': List[str]
            }
        """
        anomalies = {
            'isolated_nodes': [],
            'dense_clusters': [],
            'suspicious_patterns': []
        }

        centrality = self.calculate_centrality(graph)

        # Find isolated nodes (very low centrality)
        avg_centrality = statistics.mean(centrality.values()) if centrality else 0

        for node, score in centrality.items():
            if score < avg_centrality * 0.1:
                anomalies['isolated_nodes'].append(node)

        # Find very dense clusters (possible bot networks)
        if communities:
            avg_size = statistics.mean([len(c) for c in communities])

            for community in communities:
                if len(community) > avg_size * 3:
                    anomalies['dense_clusters'].append(community)
                    anomalies['suspicious_patterns'].append(
                        f"Unusually large cluster: {len(community)} nodes"
                    )

        # Check for star patterns (one central node, many satellites)
        # This can indicate fake follower networks
        for node, score in centrality.items():
            if score > 0.8:  # Very high centrality
                anomalies['suspicious_patterns'].append(
                    f"Hub detected: {node} has very high centrality"
                )

        logger.info(f"Detected {len(anomalies['isolated_nodes'])} isolated nodes, "
                   f"{len(anomalies['dense_clusters'])} dense clusters")

        return anomalies

    def analyze_full_network(self, connections: List[Tuple]) -> Dict:
        """
        Perform complete network analysis

        Returns:
            Comprehensive analysis report
        """
        # Build graph
        graph = self.build_graph_from_connections(connections)

        # Detect communities
        communities = self.detect_communities(graph)

        # Find central nodes
        central_nodes = self.find_central_nodes(graph, top_n=10)

        # Detect anomalies
        anomalies = self.detect_anomalies(graph, communities)

        # Network statistics
        if self.use_networkx:
            num_nodes = graph.number_of_nodes()
            num_edges = graph.number_of_edges()

            # Graph density
            if num_nodes > 1:
                density = num_edges / (num_nodes * (num_nodes - 1))
            else:
                density = 0
        else:
            num_nodes = len(graph['nodes'])
            num_edges = len(connections)

            if num_nodes > 1:
                density = num_edges / (num_nodes * (num_nodes - 1))
            else:
                density = 0

        analysis = {
            'network_stats': {
                'num_nodes': num_nodes,
                'num_edges': num_edges,
                'density': round(density, 3),
                'avg_degree': round(num_edges / num_nodes, 2) if num_nodes > 0 else 0
            },
            'communities': {
                'count': len(communities),
                'sizes': sorted([len(c) for c in communities], reverse=True),
                'largest_community': max([len(c) for c in communities]) if communities else 0
            },
            'central_nodes': [
                {'node': node, 'score': round(score, 3)}
                for node, score in central_nodes
            ],
            'anomalies': anomalies,
            'analysis_method': 'NetworkX' if self.use_networkx else 'Simple Graph'
        }

        logger.info(f"Complete network analysis: {num_nodes} nodes, "
                   f"{len(communities)} communities")

        return analysis


# Convenience function
def get_graph_analyzer() -> SocialGraphAnalyzer:
    """Get graph analyzer instance"""
    return SocialGraphAnalyzer()
