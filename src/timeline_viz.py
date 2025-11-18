"""
Timeline Visualization: Interactive timeline charts using Plotly
Visualizes investigation timeline, account discovery, and activity patterns
"""

from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path
from .utils import setup_logger
from .config import Config

logger = setup_logger(__name__)

# Try to import Plotly
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
    logger.info("Plotly available for timeline visualization")
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not installed. Install with: pip install plotly")


class TimelineVisualizer:
    """
    Create interactive timeline visualizations

    Features:
    - Investigation timeline (account discovery over time)
    - Activity timeline (posting patterns)
    - Change timeline (profile evolution)
    - Event markers (significant discoveries)
    """

    def __init__(self):
        self.use_plotly = PLOTLY_AVAILABLE

    def create_investigation_timeline(
        self,
        accounts: List[Dict],
        output_path: Path = None
    ) -> str:
        """
        Create timeline showing when accounts were discovered

        Args:
            accounts: List of account dicts with 'discovered_at' timestamps
            output_path: Where to save the HTML file

        Returns:
            Path to saved file
        """
        if not self.use_plotly:
            logger.error("Plotly not available")
            return None

        if not accounts:
            logger.warning("No accounts to visualize")
            return None

        # Prepare data
        timeline_data = []

        for account in accounts:
            # Get timestamp
            timestamp = account.get('first_seen') or account.get('discovered_at')

            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        timestamp = datetime.now()

                timeline_data.append({
                    'url': account.get('url', 'Unknown'),
                    'platform': account.get('platform', 'unknown'),
                    'timestamp': timestamp,
                    'discovered_via': account.get('discovered_via', 'unknown'),
                    'similarity': account.get('similarity_score', 0)
                })

        if not timeline_data:
            logger.warning("No valid timestamps found")
            return None

        # Sort by timestamp
        timeline_data.sort(key=lambda x: x['timestamp'])

        # Create figure
        fig = go.Figure()

        # Add scatter trace
        fig.add_trace(go.Scatter(
            x=[d['timestamp'] for d in timeline_data],
            y=[i for i in range(len(timeline_data))],
            mode='markers+text',
            marker=dict(
                size=[max(10, d['similarity']) for d in timeline_data],
                color=[d['similarity'] for d in timeline_data],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Similarity Score")
            ),
            text=[d['platform'].upper() for d in timeline_data],
            textposition="top center",
            hovertemplate='<b>%{text}</b><br>' +
                         'URL: %{customdata[0]}<br>' +
                         'Discovered: %{x}<br>' +
                         'Via: %{customdata[1]}<br>' +
                         'Similarity: %{customdata[2]:.1f}%<br>' +
                         '<extra></extra>',
            customdata=[[d['url'], d['discovered_via'], d['similarity']] for d in timeline_data]
        ))

        # Update layout
        fig.update_layout(
            title='Account Discovery Timeline',
            xaxis_title='Date/Time',
            yaxis_title='Discovery Sequence',
            hovermode='closest',
            height=600,
            showlegend=False
        )

        # Save
        if output_path is None:
            output_path = Config.REPORTS_DIR / f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        fig.write_html(str(output_path))
        logger.info(f"Timeline saved to {output_path}")

        return str(output_path)

    def create_activity_timeline(
        self,
        activity_data: List[Dict],
        output_path: Path = None
    ) -> str:
        """
        Create timeline showing activity patterns over time

        Args:
            activity_data: List of {timestamp, activity_type, platform, content}
            output_path: Where to save the HTML file

        Returns:
            Path to saved file
        """
        if not self.use_plotly:
            logger.error("Plotly not available")
            return None

        if not activity_data:
            logger.warning("No activity data to visualize")
            return None

        # Prepare data
        timestamps = []
        platforms = []
        activities = []

        for item in activity_data:
            timestamp = item.get('timestamp')

            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        continue

                timestamps.append(timestamp)
                platforms.append(item.get('platform', 'unknown'))
                activities.append(item.get('activity_type', 'post'))

        if not timestamps:
            logger.warning("No valid activity timestamps")
            return None

        # Create figure with subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Activity Timeline', 'Activity Frequency'),
            row_heights=[0.7, 0.3],
            vertical_spacing=0.15
        )

        # Timeline scatter
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=[1] * len(timestamps),
                mode='markers',
                marker=dict(
                    size=10,
                    color=[hash(p) % 10 for p in platforms],
                    colorscale='Plotly3',
                    showscale=False
                ),
                text=platforms,
                hovertemplate='<b>%{text}</b><br>%{x}<extra></extra>',
                showlegend=False
            ),
            row=1, col=1
        )

        # Activity frequency histogram
        fig.add_trace(
            go.Histogram(
                x=timestamps,
                nbinsx=20,
                marker_color='indianred',
                showlegend=False
            ),
            row=2, col=1
        )

        # Update layout
        fig.update_layout(
            title='Activity Patterns Over Time',
            height=800,
            hovermode='closest'
        )

        fig.update_xaxes(title_text="Date/Time", row=2, col=1)
        fig.update_yaxes(title_text="Activity", row=1, col=1, showticklabels=False)
        fig.update_yaxes(title_text="Frequency", row=2, col=1)

        # Save
        if output_path is None:
            output_path = Config.REPORTS_DIR / f"activity_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        fig.write_html(str(output_path))
        logger.info(f"Activity timeline saved to {output_path}")

        return str(output_path)

    def create_change_timeline(
        self,
        changes: List[Dict],
        output_path: Path = None
    ) -> str:
        """
        Create timeline showing profile changes over time

        Args:
            changes: List of change events {timestamp, field, old_value, new_value, url}
            output_path: Where to save the HTML file

        Returns:
            Path to saved file
        """
        if not self.use_plotly:
            logger.error("Plotly not available")
            return None

        if not changes:
            logger.warning("No changes to visualize")
            return None

        # Prepare data
        timeline_events = []

        for change in changes:
            timestamp = change.get('detected_at') or change.get('timestamp')

            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        continue

                timeline_events.append({
                    'timestamp': timestamp,
                    'field': change.get('field', 'unknown'),
                    'url': change.get('url', 'unknown'),
                    'old_value': str(change.get('old_value', ''))[:50],
                    'new_value': str(change.get('new_value', ''))[:50]
                })

        if not timeline_events:
            logger.warning("No valid change timestamps")
            return None

        # Sort by timestamp
        timeline_events.sort(key=lambda x: x['timestamp'])

        # Create figure
        fig = go.Figure()

        # Color map for change types
        field_colors = {
            'bio': 'red',
            'name': 'blue',
            'location': 'green',
            'followers': 'orange',
            'following': 'purple'
        }

        for event in timeline_events:
            field = event['field']
            color = field_colors.get(field, 'gray')

            fig.add_trace(go.Scatter(
                x=[event['timestamp']],
                y=[field],
                mode='markers',
                marker=dict(size=15, color=color),
                name=field,
                showlegend=False,
                hovertemplate=f"<b>{field.upper()} changed</b><br>" +
                             f"URL: {event['url']}<br>" +
                             f"Time: %{{x}}<br>" +
                             f"Old: {event['old_value']}<br>" +
                             f"New: {event['new_value']}<br>" +
                             "<extra></extra>"
            ))

        # Update layout
        fig.update_layout(
            title='Profile Change Timeline',
            xaxis_title='Date/Time',
            yaxis_title='Changed Field',
            height=500,
            hovermode='closest'
        )

        # Save
        if output_path is None:
            output_path = Config.REPORTS_DIR / f"changes_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        fig.write_html(str(output_path))
        logger.info(f"Change timeline saved to {output_path}")

        return str(output_path)

    def create_comparison_timeline(
        self,
        investigations: List[Dict],
        target: str,
        output_path: Path = None
    ) -> str:
        """
        Create timeline comparing multiple investigations of the same target

        Args:
            investigations: List of investigation results
            target: Target name
            output_path: Where to save the HTML file

        Returns:
            Path to saved file
        """
        if not self.use_plotly:
            logger.error("Plotly not available")
            return None

        if len(investigations) < 2:
            logger.warning("Need at least 2 investigations to compare")
            return None

        # Prepare data
        timestamps = []
        account_counts = []
        high_confidence_counts = []

        for inv in investigations:
            timestamp = inv.get('timestamp')

            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        continue

                timestamps.append(timestamp)
                account_counts.append(inv.get('num_accounts', 0))
                high_confidence_counts.append(inv.get('high_confidence_matches', 0))

        if not timestamps:
            logger.warning("No valid timestamps in investigations")
            return None

        # Create figure
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=timestamps,
            y=account_counts,
            mode='lines+markers',
            name='Total Accounts',
            line=dict(color='blue', width=2),
            marker=dict(size=10)
        ))

        fig.add_trace(go.Scatter(
            x=timestamps,
            y=high_confidence_counts,
            mode='lines+markers',
            name='High Confidence Matches',
            line=dict(color='green', width=2),
            marker=dict(size=10)
        ))

        # Update layout
        fig.update_layout(
            title=f'Investigation Progress: {target}',
            xaxis_title='Investigation Date',
            yaxis_title='Account Count',
            hovermode='x unified',
            height=500,
            legend=dict(x=0.01, y=0.99)
        )

        # Save
        if output_path is None:
            output_path = Config.REPORTS_DIR / f"comparison_timeline_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        fig.write_html(str(output_path))
        logger.info(f"Comparison timeline saved to {output_path}")

        return str(output_path)


# Convenience function
def get_timeline_visualizer() -> TimelineVisualizer:
    """Get timeline visualizer instance"""
    return TimelineVisualizer()
