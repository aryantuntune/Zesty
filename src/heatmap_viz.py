"""
Activity Heatmap Visualization: Visual heatmaps using matplotlib/seaborn
Shows activity patterns by hour, day, platform, etc.
"""

from datetime import datetime
from typing import List, Dict
from pathlib import Path
import numpy as np
from .utils import setup_logger
from .config import Config

logger = setup_logger(__name__)

# Try to import matplotlib and seaborn
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
    logger.info("Matplotlib available for heatmap visualization")
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not installed. Install with: pip install matplotlib")

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
    logger.info("Seaborn available for enhanced heatmaps")
except ImportError:
    SEABORN_AVAILABLE = False
    logger.warning("Seaborn not installed. Install with: pip install seaborn")


class HeatmapVisualizer:
    """
    Create activity heatmaps

    Features:
    - Hour x Day of week activity heatmap
    - Platform activity heatmap
    - Posting frequency heatmap
    - Multi-account comparison heatmaps
    """

    def __init__(self):
        self.use_matplotlib = MATPLOTLIB_AVAILABLE
        self.use_seaborn = SEABORN_AVAILABLE

        if self.use_seaborn:
            sns.set_theme(style="whitegrid")

    def create_activity_heatmap(
        self,
        timestamps: List[datetime],
        output_path: Path = None,
        title: str = "Activity Heatmap"
    ) -> str:
        """
        Create hour x day of week activity heatmap

        Args:
            timestamps: List of datetime objects
            output_path: Where to save the image
            title: Chart title

        Returns:
            Path to saved file
        """
        if not self.use_matplotlib:
            logger.error("Matplotlib not available")
            return None

        if not timestamps:
            logger.warning("No timestamps to visualize")
            return None

        # Create 7x24 matrix (days x hours)
        activity_matrix = np.zeros((7, 24))

        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Populate matrix
        for ts in timestamps:
            if ts:
                day_idx = ts.weekday()  # 0 = Monday, 6 = Sunday
                hour_idx = ts.hour
                activity_matrix[day_idx][hour_idx] += 1

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 6))

        if self.use_seaborn:
            # Seaborn heatmap
            sns.heatmap(
                activity_matrix,
                cmap='YlOrRd',
                cbar_kws={'label': 'Activity Count'},
                xticklabels=[f'{h:02d}:00' for h in range(24)],
                yticklabels=days_of_week,
                ax=ax,
                annot=False,
                fmt='g'
            )
        else:
            # Matplotlib heatmap
            im = ax.imshow(activity_matrix, cmap='YlOrRd', aspect='auto')

            # Set ticks
            ax.set_xticks(range(24))
            ax.set_xticklabels([f'{h:02d}:00' for h in range(24)], rotation=45)
            ax.set_yticks(range(7))
            ax.set_yticklabels(days_of_week)

            # Colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Activity Count', rotation=270, labelpad=20)

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Day of Week')

        plt.tight_layout()

        # Save
        if output_path is None:
            output_path = Config.REPORTS_DIR / f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Heatmap saved to {output_path}")

        return str(output_path)

    def create_platform_activity_heatmap(
        self,
        activity_data: List[Dict],
        output_path: Path = None
    ) -> str:
        """
        Create platform x time activity heatmap

        Args:
            activity_data: List of {timestamp, platform}
            output_path: Where to save the image

        Returns:
            Path to saved file
        """
        if not self.use_matplotlib:
            logger.error("Matplotlib not available")
            return None

        if not activity_data:
            logger.warning("No activity data to visualize")
            return None

        # Get unique platforms
        platforms = list(set(item.get('platform', 'unknown') for item in activity_data))
        platforms.sort()

        if not platforms:
            logger.warning("No platforms found")
            return None

        # Create matrix: platforms x hours
        platform_matrix = np.zeros((len(platforms), 24))

        for item in activity_data:
            platform = item.get('platform', 'unknown')
            timestamp = item.get('timestamp')

            if platform in platforms and timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        continue

                platform_idx = platforms.index(platform)
                hour_idx = timestamp.hour
                platform_matrix[platform_idx][hour_idx] += 1

        # Create figure
        fig, ax = plt.subplots(figsize=(14, max(6, len(platforms) * 0.5)))

        if self.use_seaborn:
            sns.heatmap(
                platform_matrix,
                cmap='viridis',
                cbar_kws={'label': 'Activity Count'},
                xticklabels=[f'{h:02d}:00' for h in range(24)],
                yticklabels=[p.upper() for p in platforms],
                ax=ax,
                annot=False
            )
        else:
            im = ax.imshow(platform_matrix, cmap='viridis', aspect='auto')

            ax.set_xticks(range(24))
            ax.set_xticklabels([f'{h:02d}:00' for h in range(24)], rotation=45)
            ax.set_yticks(range(len(platforms)))
            ax.set_yticklabels([p.upper() for p in platforms])

            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Activity Count', rotation=270, labelpad=20)

        ax.set_title('Platform Activity Heatmap', fontsize=14, fontweight='bold')
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Platform')

        plt.tight_layout()

        # Save
        if output_path is None:
            output_path = Config.REPORTS_DIR / f"platform_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Platform heatmap saved to {output_path}")

        return str(output_path)

    def create_frequency_heatmap(
        self,
        timestamps: List[datetime],
        output_path: Path = None,
        bin_size: str = 'day'
    ) -> str:
        """
        Create posting frequency heatmap over time

        Args:
            timestamps: List of datetime objects
            output_path: Where to save the image
            bin_size: 'hour', 'day', 'week'

        Returns:
            Path to saved file
        """
        if not self.use_matplotlib:
            logger.error("Matplotlib not available")
            return None

        if not timestamps:
            logger.warning("No timestamps to visualize")
            return None

        # Sort timestamps
        sorted_ts = sorted([ts for ts in timestamps if ts])

        if not sorted_ts:
            return None

        # Create bins
        start_date = sorted_ts[0]
        end_date = sorted_ts[-1]

        if bin_size == 'hour':
            # Hourly bins
            bins = []
            current = start_date.replace(minute=0, second=0, microsecond=0)
            while current <= end_date:
                bins.append(current)
                current = current.replace(hour=current.hour + 1)
        elif bin_size == 'day':
            # Daily bins
            bins = []
            current = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            while current <= end_date:
                bins.append(current)
                current = current.replace(day=current.day + 1)
        else:
            logger.warning(f"Unknown bin_size: {bin_size}")
            return None

        # Count posts per bin
        counts = [0] * len(bins)

        for ts in sorted_ts:
            for i, bin_start in enumerate(bins):
                if i < len(bins) - 1:
                    bin_end = bins[i + 1]
                    if bin_start <= ts < bin_end:
                        counts[i] += 1
                        break
                else:
                    if ts >= bin_start:
                        counts[i] += 1

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 4))

        # Bar chart
        ax.bar(range(len(counts)), counts, color='steelblue', alpha=0.7)

        # Format x-axis
        if bin_size == 'hour':
            labels = [b.strftime('%m/%d %H:00') for b in bins]
        else:
            labels = [b.strftime('%m/%d') for b in bins]

        # Show every Nth label to avoid crowding
        step = max(1, len(labels) // 20)
        ax.set_xticks(range(0, len(labels), step))
        ax.set_xticklabels([labels[i] for i in range(0, len(labels), step)], rotation=45, ha='right')

        ax.set_title(f'Posting Frequency ({bin_size.capitalize()})', fontsize=14, fontweight='bold')
        ax.set_xlabel('Time Period')
        ax.set_ylabel('Post Count')
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        # Save
        if output_path is None:
            output_path = Config.REPORTS_DIR / f"frequency_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Frequency heatmap saved to {output_path}")

        return str(output_path)

    def create_comparison_heatmap(
        self,
        account1_timestamps: List[datetime],
        account2_timestamps: List[datetime],
        account1_name: str = "Account 1",
        account2_name: str = "Account 2",
        output_path: Path = None
    ) -> str:
        """
        Create side-by-side comparison heatmap for two accounts

        Args:
            account1_timestamps: Timestamps for account 1
            account2_timestamps: Timestamps for account 2
            account1_name: Label for account 1
            account2_name: Label for account 2
            output_path: Where to save the image

        Returns:
            Path to saved file
        """
        if not self.use_matplotlib:
            logger.error("Matplotlib not available")
            return None

        # Create matrices
        matrix1 = np.zeros((7, 24))
        matrix2 = np.zeros((7, 24))

        for ts in account1_timestamps:
            if ts:
                matrix1[ts.weekday()][ts.hour] += 1

        for ts in account2_timestamps:
            if ts:
                matrix2[ts.weekday()][ts.hour] += 1

        # Normalize for comparison
        max_val = max(matrix1.max(), matrix2.max())

        if max_val > 0:
            matrix1_norm = matrix1 / max_val
            matrix2_norm = matrix2 / max_val
        else:
            matrix1_norm = matrix1
            matrix2_norm = matrix2

        # Create side-by-side plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 6))

        days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        if self.use_seaborn:
            sns.heatmap(matrix1_norm, cmap='YlOrRd', ax=ax1, cbar_kws={'label': 'Normalized Activity'},
                       xticklabels=[f'{h:02d}' for h in range(24)], yticklabels=days_of_week)
            sns.heatmap(matrix2_norm, cmap='YlOrRd', ax=ax2, cbar_kws={'label': 'Normalized Activity'},
                       xticklabels=[f'{h:02d}' for h in range(24)], yticklabels=days_of_week)
        else:
            im1 = ax1.imshow(matrix1_norm, cmap='YlOrRd', aspect='auto', vmin=0, vmax=1)
            im2 = ax2.imshow(matrix2_norm, cmap='YlOrRd', aspect='auto', vmin=0, vmax=1)

            for ax in [ax1, ax2]:
                ax.set_xticks(range(24))
                ax.set_xticklabels([f'{h:02d}' for h in range(24)], rotation=45)
                ax.set_yticks(range(7))
                ax.set_yticklabels(days_of_week)

            plt.colorbar(im2, ax=[ax1, ax2], label='Normalized Activity')

        ax1.set_title(account1_name, fontsize=12, fontweight='bold')
        ax2.set_title(account2_name, fontsize=12, fontweight='bold')

        ax1.set_xlabel('Hour')
        ax2.set_xlabel('Hour')
        ax1.set_ylabel('Day of Week')

        fig.suptitle('Activity Pattern Comparison', fontsize=14, fontweight='bold', y=1.02)

        plt.tight_layout()

        # Save
        if output_path is None:
            output_path = Config.REPORTS_DIR / f"comparison_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Comparison heatmap saved to {output_path}")

        return str(output_path)


# Convenience function
def get_heatmap_visualizer() -> HeatmapVisualizer:
    """Get heatmap visualizer instance"""
    return HeatmapVisualizer()
