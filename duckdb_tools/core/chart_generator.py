"""
Plotly Chart Generator for expense analysis
Creates interactive charts from SQL query results
"""

import base64
import io
import logging
from typing import Optional, Dict, Any
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

class PlotlyChartGenerator:
    """
    Generates Plotly charts from DataFrame data
    """
    
    def __init__(self, theme: str = "plotly_white"):
        """
        Initialize chart generator
        
        Args:
            theme: Plotly theme to use
        """
        self.theme = theme
        self.default_colors = px.colors.qualitative.Set3
    
    def create_bar_chart(
        self, 
        df: pd.DataFrame, 
        x_col: str, 
        y_col: str, 
        title: str,
        orientation: str = "v",
        color_col: Optional[str] = None
    ) -> str:
        """
        Create a bar chart from DataFrame
        
        Args:
            df: DataFrame with data
            x_col: Column name for x-axis
            y_col: Column name for y-axis
            title: Chart title
            orientation: 'v' for vertical, 'h' for horizontal
            color_col: Optional column for color coding
            
        Returns:
            str: Base64 encoded PNG image
        """
        try:
            if df.empty:
                logger.warning("Empty DataFrame provided for bar chart")
                return self._create_empty_chart(title)
            
            if orientation == "h":
                fig = px.bar(
                    df, 
                    x=y_col, 
                    y=x_col,
                    title=title,
                    color=color_col,
                    color_discrete_sequence=self.default_colors
                )
            else:
                fig = px.bar(
                    df, 
                    x=x_col, 
                    y=y_col,
                    title=title,
                    color=color_col,
                    color_discrete_sequence=self.default_colors
                )
            
            fig.update_layout(
                template=self.theme,
                title_x=0.5,
                title_font_size=16,
                showlegend=True
            )
            
            return self._chart_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Failed to create bar chart: {e}")
            return self._create_error_chart(title, str(e))
    
    def create_line_chart(
        self, 
        df: pd.DataFrame, 
        x_col: str, 
        y_col: str, 
        title: str,
        color_col: Optional[str] = None
    ) -> str:
        """
        Create a line chart from DataFrame
        
        Args:
            df: DataFrame with data
            x_col: Column name for x-axis
            y_col: Column name for y-axis
            title: Chart title
            color_col: Optional column for color coding
            
        Returns:
            str: Base64 encoded PNG image
        """
        try:
            if df.empty:
                logger.warning("Empty DataFrame provided for line chart")
                return self._create_empty_chart(title)
            
            fig = px.line(
                df, 
                x=x_col, 
                y=y_col,
                title=title,
                color=color_col,
                color_discrete_sequence=self.default_colors
            )
            
            fig.update_layout(
                template=self.theme,
                title_x=0.5,
                title_font_size=16,
                showlegend=True
            )
            
            return self._chart_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Failed to create line chart: {e}")
            return self._create_error_chart(title, str(e))
    
    def create_pie_chart(
        self, 
        df: pd.DataFrame, 
        values_col: str, 
        names_col: str, 
        title: str
    ) -> str:
        """
        Create a pie chart from DataFrame
        
        Args:
            df: DataFrame with data
            values_col: Column name for values
            names_col: Column name for labels
            title: Chart title
            
        Returns:
            str: Base64 encoded PNG image
        """
        try:
            if df.empty:
                logger.warning("Empty DataFrame provided for pie chart")
                return self._create_empty_chart(title)
            
            fig = px.pie(
                df, 
                values=values_col, 
                names=names_col,
                title=title,
                color_discrete_sequence=self.default_colors
            )
            
            fig.update_layout(
                template=self.theme,
                title_x=0.5,
                title_font_size=16
            )
            
            return self._chart_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Failed to create pie chart: {e}")
            return self._create_error_chart(title, str(e))
    
    def create_horizontal_bar_chart(
        self, 
        df: pd.DataFrame, 
        x_col: str, 
        y_col: str, 
        title: str,
        limit: Optional[int] = None
    ) -> str:
        """
        Create a horizontal bar chart (useful for top N lists)
        
        Args:
            df: DataFrame with data
            x_col: Column name for x-axis (values)
            y_col: Column name for y-axis (labels)
            title: Chart title
            limit: Optional limit for number of bars
            
        Returns:
            str: Base64 encoded PNG image
        """
        try:
            if df.empty:
                logger.warning("Empty DataFrame provided for horizontal bar chart")
                return self._create_empty_chart(title)
            
            # Limit results if specified
            if limit and len(df) > limit:
                df = df.head(limit)
            
            fig = px.bar(
                df, 
                x=x_col, 
                y=y_col,
                title=title,
                orientation='h',
                color_discrete_sequence=self.default_colors
            )
            
            fig.update_layout(
                template=self.theme,
                title_x=0.5,
                title_font_size=16,
                yaxis={'categoryorder': 'total ascending'}
            )
            
            return self._chart_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Failed to create horizontal bar chart: {e}")
            return self._create_error_chart(title, str(e))
    
    def _chart_to_base64(self, fig: go.Figure) -> str:
        """
        Convert Plotly figure to base64 string
        
        Args:
            fig: Plotly figure object
            
        Returns:
            str: Base64 encoded PNG image
        """
        try:
            # Convert to PNG bytes
            img_bytes = fig.to_image(format="png", width=800, height=600)
            
            # Encode to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            return img_base64
            
        except Exception as e:
            logger.error(f"Failed to convert chart to base64: {e}")
            return ""
    
    def _create_empty_chart(self, title: str) -> str:
        """Create a chart showing no data message"""
        try:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                title=title,
                template=self.theme,
                title_x=0.5
            )
            return self._chart_to_base64(fig)
        except Exception as e:
            logger.error(f"Failed to create empty chart: {e}")
            return ""
    
    def _create_error_chart(self, title: str, error_msg: str) -> str:
        """Create a chart showing error message"""
        try:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error: {error_msg}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="red")
            )
            fig.update_layout(
                title=title,
                template=self.theme,
                title_x=0.5
            )
            return self._chart_to_base64(fig)
        except Exception as e:
            logger.error(f"Failed to create error chart: {e}")
            return "" 