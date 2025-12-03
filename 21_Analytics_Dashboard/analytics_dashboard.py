"""
Advanced Analytics Dashboard for AI Detection System
Comprehensive analytics including usage statistics, detection metrics, user behavior, and business intelligence
"""

import asyncio
import json
import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from sqlalchemy import create_engine, text
import redis
from collections import defaultdict, Counter
import sqlite3
import streamlit as st
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnalyticsConfig:
    """Configuration for analytics dashboard"""
    database_url: str = "sqlite:///analytics.db"
    redis_url: str = "redis://localhost:6379"
    dashboard_port: int = 8050
    update_interval: int = 30  # seconds
    data_retention_days: int = 90
    cache_ttl: int = 300  # seconds
    
    # Dashboard settings
    theme: str = "bootstrap"
    auto_refresh: bool = True
    export_formats: List[str] = field(default_factory=lambda: ["pdf", "png", "html"])
    
    # Metrics settings
    accuracy_threshold: float = 0.95
    response_time_threshold: float = 2.0  # seconds
    error_rate_threshold: float = 0.01  # 1%

@dataclass
class MetricData:
    """Data structure for metrics"""
    timestamp: datetime
    metric_name: str
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class DataCollector:
    """Data collection and aggregation system"""
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.engine = create_engine(config.database_url)
        self.redis_client = redis.from_url(config.redis_url) if config.redis_url else None
        self.setup_database()
    
    def setup_database(self):
        """Setup database tables"""
        with self.engine.connect() as conn:
            # Usage statistics table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    endpoint TEXT,
                    method TEXT,
                    response_time REAL,
                    status_code INTEGER,
                    user_agent TEXT,
                    ip_address TEXT,
                    request_size INTEGER,
                    response_size INTEGER
                )
            """))
            
            # Detection metrics table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS detection_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    model_name TEXT,
                    confidence_score REAL,
                    detection_count INTEGER,
                    processing_time REAL,
                    image_size INTEGER,
                    accuracy REAL,
                    false_positives INTEGER,
                    false_negatives INTEGER
                )
            """))
            
            # User behavior table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_behavior (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    session_id TEXT,
                    action TEXT,
                    page_url TEXT,
                    duration REAL,
                    device_type TEXT,
                    browser TEXT,
                    location TEXT
                )
            """))
            
            # Business metrics table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS business_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_type TEXT,
                    value REAL,
                    currency TEXT,
                    category TEXT,
                    subcategory TEXT
                )
            """))
            
            conn.commit()
    
    def collect_usage_stats(self, data: Dict[str, Any]):
        """Collect usage statistics"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO usage_stats 
                (user_id, endpoint, method, response_time, status_code, 
                 user_agent, ip_address, request_size, response_size)
                VALUES (:user_id, :endpoint, :method, :response_time, :status_code,
                        :user_agent, :ip_address, :request_size, :response_size)
            """), data)
            conn.commit()
    
    def collect_detection_metrics(self, data: Dict[str, Any]):
        """Collect detection metrics"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO detection_metrics 
                (model_name, confidence_score, detection_count, processing_time,
                 image_size, accuracy, false_positives, false_negatives)
                VALUES (:model_name, :confidence_score, :detection_count, :processing_time,
                        :image_size, :accuracy, :false_positives, :false_negatives)
            """), data)
            conn.commit()
    
    def collect_user_behavior(self, data: Dict[str, Any]):
        """Collect user behavior data"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO user_behavior 
                (user_id, session_id, action, page_url, duration,
                 device_type, browser, location)
                VALUES (:user_id, :session_id, :action, :page_url, :duration,
                        :device_type, :browser, :location)
            """), data)
            conn.commit()
    
    def collect_business_metrics(self, data: Dict[str, Any]):
        """Collect business metrics"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO business_metrics 
                (metric_type, value, currency, category, subcategory)
                VALUES (:metric_type, :value, :currency, :category, :subcategory)
            """), data)
            conn.commit()

class MetricsCalculator:
    """Calculate various metrics and KPIs"""
    
    def __init__(self, data_collector: DataCollector):
        self.data_collector = data_collector
        self.engine = data_collector.engine
    
    def calculate_usage_metrics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Calculate usage metrics"""
        time_filter = self._get_time_filter(time_range)
        
        with self.engine.connect() as conn:
            # Total requests
            total_requests = conn.execute(text(f"""
                SELECT COUNT(*) FROM usage_stats WHERE timestamp >= {time_filter}
            """)).scalar()
            
            # Unique users
            unique_users = conn.execute(text(f"""
                SELECT COUNT(DISTINCT user_id) FROM usage_stats WHERE timestamp >= {time_filter}
            """)).scalar()
            
            # Average response time
            avg_response_time = conn.execute(text(f"""
                SELECT AVG(response_time) FROM usage_stats WHERE timestamp >= {time_filter}
            """)).scalar() or 0
            
            # Error rate
            error_count = conn.execute(text(f"""
                SELECT COUNT(*) FROM usage_stats 
                WHERE timestamp >= {time_filter} AND status_code >= 400
            """)).scalar()
            
            error_rate = (error_count / total_requests) if total_requests > 0 else 0
            
            # Top endpoints
            top_endpoints = conn.execute(text(f"""
                SELECT endpoint, COUNT(*) as count 
                FROM usage_stats 
                WHERE timestamp >= {time_filter}
                GROUP BY endpoint 
                ORDER BY count DESC 
                LIMIT 10
            """)).fetchall()
            
            return {
                "total_requests": total_requests,
                "unique_users": unique_users,
                "avg_response_time": avg_response_time,
                "error_rate": error_rate,
                "top_endpoints": [{"endpoint": row[0], "count": row[1]} for row in top_endpoints]
            }
    
    def calculate_detection_metrics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Calculate detection accuracy metrics"""
        time_filter = self._get_time_filter(time_range)
        
        with self.engine.connect() as conn:
            # Overall accuracy
            avg_accuracy = conn.execute(text(f"""
                SELECT AVG(accuracy) FROM detection_metrics WHERE timestamp >= {time_filter}
            """)).scalar() or 0
            
            # Total detections
            total_detections = conn.execute(text(f"""
                SELECT SUM(detection_count) FROM detection_metrics WHERE timestamp >= {time_filter}
            """)).scalar() or 0
            
            # Average confidence
            avg_confidence = conn.execute(text(f"""
                SELECT AVG(confidence_score) FROM detection_metrics WHERE timestamp >= {time_filter}
            """)).scalar() or 0
            
            # Average processing time
            avg_processing_time = conn.execute(text(f"""
                SELECT AVG(processing_time) FROM detection_metrics WHERE timestamp >= {time_filter}
            """)).scalar() or 0
            
            # Model performance
            model_performance = conn.execute(text(f"""
                SELECT model_name, AVG(accuracy) as avg_accuracy, COUNT(*) as count
                FROM detection_metrics 
                WHERE timestamp >= {time_filter}
                GROUP BY model_name
                ORDER BY avg_accuracy DESC
            """)).fetchall()
            
            # False positive/negative rates
            total_fp = conn.execute(text(f"""
                SELECT SUM(false_positives) FROM detection_metrics WHERE timestamp >= {time_filter}
            """)).scalar() or 0
            
            total_fn = conn.execute(text(f"""
                SELECT SUM(false_negatives) FROM detection_metrics WHERE timestamp >= {time_filter}
            """)).scalar() or 0
            
            return {
                "avg_accuracy": avg_accuracy,
                "total_detections": total_detections,
                "avg_confidence": avg_confidence,
                "avg_processing_time": avg_processing_time,
                "model_performance": [
                    {"model": row[0], "accuracy": row[1], "count": row[2]} 
                    for row in model_performance
                ],
                "false_positive_rate": total_fp / total_detections if total_detections > 0 else 0,
                "false_negative_rate": total_fn / total_detections if total_detections > 0 else 0
            }
    
    def calculate_user_behavior_metrics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Calculate user behavior metrics"""
        time_filter = self._get_time_filter(time_range)
        
        with self.engine.connect() as conn:
            # Session metrics
            avg_session_duration = conn.execute(text(f"""
                SELECT AVG(duration) FROM user_behavior 
                WHERE timestamp >= {time_filter} AND action = 'session_end'
            """)).scalar() or 0
            
            # Page views
            page_views = conn.execute(text(f"""
                SELECT page_url, COUNT(*) as views
                FROM user_behavior 
                WHERE timestamp >= {time_filter} AND action = 'page_view'
                GROUP BY page_url
                ORDER BY views DESC
                LIMIT 10
            """)).fetchall()
            
            # Device types
            device_distribution = conn.execute(text(f"""
                SELECT device_type, COUNT(*) as count
                FROM user_behavior 
                WHERE timestamp >= {time_filter}
                GROUP BY device_type
            """)).fetchall()
            
            # Browser distribution
            browser_distribution = conn.execute(text(f"""
                SELECT browser, COUNT(*) as count
                FROM user_behavior 
                WHERE timestamp >= {time_filter}
                GROUP BY browser
                ORDER BY count DESC
                LIMIT 5
            """)).fetchall()
            
            # User actions
            action_distribution = conn.execute(text(f"""
                SELECT action, COUNT(*) as count
                FROM user_behavior 
                WHERE timestamp >= {time_filter}
                GROUP BY action
                ORDER BY count DESC
            """)).fetchall()
            
            return {
                "avg_session_duration": avg_session_duration,
                "page_views": [{"page": row[0], "views": row[1]} for row in page_views],
                "device_distribution": [{"device": row[0], "count": row[1]} for row in device_distribution],
                "browser_distribution": [{"browser": row[0], "count": row[1]} for row in browser_distribution],
                "action_distribution": [{"action": row[0], "count": row[1]} for row in action_distribution]
            }
    
    def calculate_business_metrics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Calculate business intelligence metrics"""
        time_filter = self._get_time_filter(time_range)
        
        with self.engine.connect() as conn:
            # Revenue metrics
            total_revenue = conn.execute(text(f"""
                SELECT SUM(value) FROM business_metrics 
                WHERE timestamp >= {time_filter} AND metric_type = 'revenue'
            """)).scalar() or 0
            
            # Cost metrics
            total_costs = conn.execute(text(f"""
                SELECT SUM(value) FROM business_metrics 
                WHERE timestamp >= {time_filter} AND metric_type = 'cost'
            """)).scalar() or 0
            
            # API usage costs
            api_costs = conn.execute(text(f"""
                SELECT category, SUM(value) as cost
                FROM business_metrics 
                WHERE timestamp >= {time_filter} AND metric_type = 'cost'
                GROUP BY category
                ORDER BY cost DESC
            """)).fetchall()
            
            # ROI calculation
            roi = ((total_revenue - total_costs) / total_costs * 100) if total_costs > 0 else 0
            
            return {
                "total_revenue": total_revenue,
                "total_costs": total_costs,
                "profit": total_revenue - total_costs,
                "roi_percentage": roi,
                "cost_breakdown": [{"category": row[0], "cost": row[1]} for row in api_costs]
            }
    
    def _get_time_filter(self, time_range: str) -> str:
        """Get SQL time filter based on range"""
        if time_range == "1h":
            return "datetime('now', '-1 hour')"
        elif time_range == "24h":
            return "datetime('now', '-1 day')"
        elif time_range == "7d":
            return "datetime('now', '-7 days')"
        elif time_range == "30d":
            return "datetime('now', '-30 days')"
        else:
            return "datetime('now', '-1 day')"

class ChartGenerator:
    """Generate interactive charts and visualizations"""
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
    
    def create_usage_chart(self, metrics: Dict[str, Any]) -> go.Figure:
        """Create usage statistics chart"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Requests Over Time', 'Response Time', 'Error Rate', 'Top Endpoints'),
            specs=[[{"secondary_y": True}, {"type": "indicator"}],
                   [{"type": "indicator"}, {"type": "bar"}]]
        )
        
        # Requests over time (placeholder data)
        hours = list(range(24))
        requests = np.random.poisson(100, 24)
        
        fig.add_trace(
            go.Scatter(x=hours, y=requests, name="Requests", line=dict(color="blue")),
            row=1, col=1
        )
        
        # Response time indicator
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=metrics.get("avg_response_time", 0) * 1000,  # Convert to ms
                title={"text": "Avg Response Time (ms)"},
                gauge={"axis": {"range": [None, 5000]},
                       "bar": {"color": "darkblue"},
                       "steps": [{"range": [0, 1000], "color": "lightgray"},
                                {"range": [1000, 3000], "color": "yellow"},
                                {"range": [3000, 5000], "color": "red"}]}
            ),
            row=1, col=2
        )
        
        # Error rate indicator
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=metrics.get("error_rate", 0) * 100,  # Convert to percentage
                title={"text": "Error Rate (%)"},
                gauge={"axis": {"range": [None, 10]},
                       "bar": {"color": "red"},
                       "steps": [{"range": [0, 1], "color": "lightgray"},
                                {"range": [1, 5], "color": "yellow"},
                                {"range": [5, 10], "color": "red"}]}
            ),
            row=2, col=1
        )
        
        # Top endpoints
        endpoints = [ep["endpoint"] for ep in metrics.get("top_endpoints", [])]
        counts = [ep["count"] for ep in metrics.get("top_endpoints", [])]
        
        fig.add_trace(
            go.Bar(x=endpoints, y=counts, name="Requests", marker_color="lightblue"),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False, title_text="Usage Statistics Dashboard")
        return fig
    
    def create_detection_chart(self, metrics: Dict[str, Any]) -> go.Figure:
        """Create detection metrics chart"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Model Accuracy', 'Detection Volume', 'Confidence Distribution', 'Processing Time'),
            specs=[[{"type": "bar"}, {"type": "indicator"}],
                   [{"type": "histogram"}, {"type": "indicator"}]]
        )
        
        # Model accuracy
        models = [m["model"] for m in metrics.get("model_performance", [])]
        accuracies = [m["accuracy"] for m in metrics.get("model_performance", [])]
        
        fig.add_trace(
            go.Bar(x=models, y=accuracies, name="Accuracy", marker_color="green"),
            row=1, col=1
        )
        
        # Detection volume indicator
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=metrics.get("total_detections", 0),
                title={"text": "Total Detections"},
                number={"font": {"size": 40}}
            ),
            row=1, col=2
        )
        
        # Confidence distribution (placeholder data)
        confidence_scores = np.random.beta(8, 2, 1000)  # Simulated confidence scores
        fig.add_trace(
            go.Histogram(x=confidence_scores, name="Confidence", marker_color="orange"),
            row=2, col=1
        )
        
        # Processing time indicator
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=metrics.get("avg_processing_time", 0) * 1000,  # Convert to ms
                title={"text": "Avg Processing Time (ms)"},
                gauge={"axis": {"range": [None, 1000]},
                       "bar": {"color": "purple"},
                       "steps": [{"range": [0, 100], "color": "lightgray"},
                                {"range": [100, 500], "color": "yellow"},
                                {"range": [500, 1000], "color": "red"}]}
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False, title_text="Detection Metrics Dashboard")
        return fig
    
    def create_user_behavior_chart(self, metrics: Dict[str, Any]) -> go.Figure:
        """Create user behavior chart"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Device Distribution', 'Browser Distribution', 'Page Views', 'User Actions'),
            specs=[[{"type": "pie"}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Device distribution
        devices = [d["device"] for d in metrics.get("device_distribution", [])]
        device_counts = [d["count"] for d in metrics.get("device_distribution", [])]
        
        fig.add_trace(
            go.Pie(labels=devices, values=device_counts, name="Devices"),
            row=1, col=1
        )
        
        # Browser distribution
        browsers = [b["browser"] for b in metrics.get("browser_distribution", [])]
        browser_counts = [b["count"] for b in metrics.get("browser_distribution", [])]
        
        fig.add_trace(
            go.Pie(labels=browsers, values=browser_counts, name="Browsers"),
            row=1, col=2
        )
        
        # Page views
        pages = [p["page"] for p in metrics.get("page_views", [])]
        views = [p["views"] for p in metrics.get("page_views", [])]
        
        fig.add_trace(
            go.Bar(x=pages, y=views, name="Views", marker_color="lightcoral"),
            row=2, col=1
        )
        
        # User actions
        actions = [a["action"] for a in metrics.get("action_distribution", [])]
        action_counts = [a["count"] for a in metrics.get("action_distribution", [])]
        
        fig.add_trace(
            go.Bar(x=actions, y=action_counts, name="Actions", marker_color="lightseagreen"),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False, title_text="User Behavior Analytics")
        return fig
    
    def create_business_chart(self, metrics: Dict[str, Any]) -> go.Figure:
        """Create business intelligence chart"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Revenue vs Costs', 'ROI', 'Cost Breakdown', 'Profit Trend'),
            specs=[[{"type": "bar"}, {"type": "indicator"}],
                   [{"type": "pie"}, {"type": "scatter"}]]
        )
        
        # Revenue vs Costs
        fig.add_trace(
            go.Bar(x=["Revenue", "Costs", "Profit"], 
                   y=[metrics.get("total_revenue", 0), 
                      metrics.get("total_costs", 0),
                      metrics.get("profit", 0)],
                   marker_color=["green", "red", "blue"]),
            row=1, col=1
        )
        
        # ROI indicator
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=metrics.get("roi_percentage", 0),
                title={"text": "ROI (%)"},
                gauge={"axis": {"range": [-100, 200]},
                       "bar": {"color": "gold"},
                       "steps": [{"range": [-100, 0], "color": "red"},
                                {"range": [0, 50], "color": "yellow"},
                                {"range": [50, 200], "color": "green"}]}
            ),
            row=1, col=2
        )
        
        # Cost breakdown
        categories = [c["category"] for c in metrics.get("cost_breakdown", [])]
        costs = [c["cost"] for c in metrics.get("cost_breakdown", [])]
        
        fig.add_trace(
            go.Pie(labels=categories, values=costs, name="Costs"),
            row=2, col=1
        )
        
        # Profit trend (placeholder data)
        days = list(range(30))
        profits = np.cumsum(np.random.normal(100, 50, 30))
        
        fig.add_trace(
            go.Scatter(x=days, y=profits, name="Profit", line=dict(color="green")),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False, title_text="Business Intelligence Dashboard")
        return fig

class DashboardApp:
    """Main dashboard application using Dash"""
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.data_collector = DataCollector(config)
        self.metrics_calculator = MetricsCalculator(self.data_collector)
        self.chart_generator = ChartGenerator()
        
        # Initialize Dash app
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Setup dashboard layout"""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("AI Detection Analytics Dashboard", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),
            
            # Control panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Controls", className="card-title"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Time Range:"),
                                    dcc.Dropdown(
                                        id="time-range-dropdown",
                                        options=[
                                            {"label": "Last Hour", "value": "1h"},
                                            {"label": "Last 24 Hours", "value": "24h"},
                                            {"label": "Last 7 Days", "value": "7d"},
                                            {"label": "Last 30 Days", "value": "30d"}
                                        ],
                                        value="24h"
                                    )
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Auto Refresh:"),
                                    dbc.Switch(
                                        id="auto-refresh-switch",
                                        value=True,
                                        className="mb-2"
                                    )
                                ], width=6)
                            ])
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Metrics cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id="total-requests", className="text-primary"),
                            html.P("Total Requests", className="card-text")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id="unique-users", className="text-success"),
                            html.P("Unique Users", className="card-text")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id="avg-accuracy", className="text-info"),
                            html.P("Average Accuracy", className="card-text")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id="total-detections", className="text-warning"),
                            html.P("Total Detections", className="card-text")
                        ])
                    ])
                ], width=3)
            ], className="mb-4"),
            
            # Charts
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="usage-chart")
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="detection-chart")
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="behavior-chart")
                ], width=6),
                dbc.Col([
                    dcc.Graph(id="business-chart")
                ], width=6)
            ]),
            
            # Auto-refresh interval
            dcc.Interval(
                id="interval-component",
                interval=self.config.update_interval * 1000,  # in milliseconds
                n_intervals=0
            )
        ], fluid=True)
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [Output("total-requests", "children"),
             Output("unique-users", "children"),
             Output("avg-accuracy", "children"),
             Output("total-detections", "children"),
             Output("usage-chart", "figure"),
             Output("detection-chart", "figure"),
             Output("behavior-chart", "figure"),
             Output("business-chart", "figure")],
            [Input("time-range-dropdown", "value"),
             Input("interval-component", "n_intervals"),
             Input("auto-refresh-switch", "value")]
        )
        def update_dashboard(time_range, n_intervals, auto_refresh):
            # Calculate metrics
            usage_metrics = self.metrics_calculator.calculate_usage_metrics(time_range)
            detection_metrics = self.metrics_calculator.calculate_detection_metrics(time_range)
            behavior_metrics = self.metrics_calculator.calculate_user_behavior_metrics(time_range)
            business_metrics = self.metrics_calculator.calculate_business_metrics(time_range)
            
            # Update metric cards
            total_requests = f"{usage_metrics.get('total_requests', 0):,}"
            unique_users = f"{usage_metrics.get('unique_users', 0):,}"
            avg_accuracy = f"{detection_metrics.get('avg_accuracy', 0):.2%}"
            total_detections = f"{detection_metrics.get('total_detections', 0):,}"
            
            # Generate charts
            usage_chart = self.chart_generator.create_usage_chart(usage_metrics)
            detection_chart = self.chart_generator.create_detection_chart(detection_metrics)
            behavior_chart = self.chart_generator.create_user_behavior_chart(behavior_metrics)
            business_chart = self.chart_generator.create_business_chart(business_metrics)
            
            return (total_requests, unique_users, avg_accuracy, total_detections,
                    usage_chart, detection_chart, behavior_chart, business_chart)
    
    def run(self, debug: bool = False):
        """Run the dashboard application"""
        logger.info(f"Starting analytics dashboard on port {self.config.dashboard_port}")
        self.app.run_server(
            debug=debug,
            host="0.0.0.0",
            port=self.config.dashboard_port
        )

class StreamlitDashboard:
    """Alternative Streamlit-based dashboard"""
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.data_collector = DataCollector(config)
        self.metrics_calculator = MetricsCalculator(self.data_collector)
        self.chart_generator = ChartGenerator()
    
    def run(self):
        """Run Streamlit dashboard"""
        st.set_page_config(
            page_title="AI Detection Analytics",
            page_icon="📊",
            layout="wide"
        )
        
        st.title("🤖 AI Detection Analytics Dashboard")
        st.markdown("---")
        
        # Sidebar controls
        st.sidebar.header("Controls")
        time_range = st.sidebar.selectbox(
            "Time Range",
            ["1h", "24h", "7d", "30d"],
            index=1
        )
        
        auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
        
        if st.sidebar.button("Refresh Data") or auto_refresh:
            # Calculate metrics
            usage_metrics = self.metrics_calculator.calculate_usage_metrics(time_range)
            detection_metrics = self.metrics_calculator.calculate_detection_metrics(time_range)
            behavior_metrics = self.metrics_calculator.calculate_user_behavior_metrics(time_range)
            business_metrics = self.metrics_calculator.calculate_business_metrics(time_range)
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Requests", f"{usage_metrics.get('total_requests', 0):,}")
            
            with col2:
                st.metric("Unique Users", f"{usage_metrics.get('unique_users', 0):,}")
            
            with col3:
                st.metric("Average Accuracy", f"{detection_metrics.get('avg_accuracy', 0):.2%}")
            
            with col4:
                st.metric("Total Detections", f"{detection_metrics.get('total_detections', 0):,}")
            
            # Display charts
            st.subheader("📈 Usage Statistics")
            usage_chart = self.chart_generator.create_usage_chart(usage_metrics)
            st.plotly_chart(usage_chart, use_container_width=True)
            
            st.subheader("🎯 Detection Metrics")
            detection_chart = self.chart_generator.create_detection_chart(detection_metrics)
            st.plotly_chart(detection_chart, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("👥 User Behavior")
                behavior_chart = self.chart_generator.create_user_behavior_chart(behavior_metrics)
                st.plotly_chart(behavior_chart, use_container_width=True)
            
            with col2:
                st.subheader("💰 Business Intelligence")
                business_chart = self.chart_generator.create_business_chart(business_metrics)
                st.plotly_chart(business_chart, use_container_width=True)

def generate_sample_data(data_collector: DataCollector):
    """Generate sample data for testing"""
    import random
    from datetime import datetime, timedelta
    
    # Generate sample usage data
    for i in range(1000):
        timestamp = datetime.now() - timedelta(hours=random.randint(0, 24))
        data_collector.collect_usage_stats({
            "user_id": f"user_{random.randint(1, 100)}",
            "endpoint": random.choice(["/detect", "/health", "/upload", "/results"]),
            "method": random.choice(["GET", "POST"]),
            "response_time": random.uniform(0.1, 3.0),
            "status_code": random.choice([200, 200, 200, 400, 404, 500]),
            "user_agent": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
            "ip_address": f"192.168.1.{random.randint(1, 255)}",
            "request_size": random.randint(1000, 10000),
            "response_size": random.randint(500, 5000)
        })
    
    # Generate sample detection data
    for i in range(500):
        timestamp = datetime.now() - timedelta(hours=random.randint(0, 24))
        data_collector.collect_detection_metrics({
            "model_name": random.choice(["yolo_v5", "rcnn", "ssd"]),
            "confidence_score": random.uniform(0.5, 1.0),
            "detection_count": random.randint(0, 10),
            "processing_time": random.uniform(0.05, 0.5),
            "image_size": random.randint(100000, 1000000),
            "accuracy": random.uniform(0.8, 0.99),
            "false_positives": random.randint(0, 3),
            "false_negatives": random.randint(0, 2)
        })
    
    # Generate sample user behavior data
    for i in range(2000):
        timestamp = datetime.now() - timedelta(hours=random.randint(0, 24))
        data_collector.collect_user_behavior({
            "user_id": f"user_{random.randint(1, 100)}",
            "session_id": f"session_{random.randint(1, 200)}",
            "action": random.choice(["page_view", "click", "upload", "download", "session_end"]),
            "page_url": random.choice(["/", "/upload", "/results", "/settings", "/help"]),
            "duration": random.uniform(1, 300),
            "device_type": random.choice(["desktop", "mobile", "tablet"]),
            "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
            "location": random.choice(["US", "UK", "DE", "FR", "JP"])
        })
    
    # Generate sample business data
    for i in range(100):
        timestamp = datetime.now() - timedelta(days=random.randint(0, 30))
        data_collector.collect_business_metrics({
            "metric_type": random.choice(["revenue", "cost"]),
            "value": random.uniform(10, 1000),
            "currency": "USD",
            "category": random.choice(["api_usage", "storage", "compute", "subscription"]),
            "subcategory": random.choice(["aws", "gcp", "azure", "premium"])
        })

def main():
    """Main function for analytics dashboard"""
    # Create configuration
    config = AnalyticsConfig(
        dashboard_port=8050,
        update_interval=30
    )
    
    # Initialize data collector
    data_collector = DataCollector(config)
    
    # Generate sample data for testing
    print("Generating sample data...")
    generate_sample_data(data_collector)
    print("Sample data generated!")
    
    # Choose dashboard type
    dashboard_type = input("Choose dashboard type (dash/streamlit): ").lower()
    
    if dashboard_type == "streamlit":
        # Run Streamlit dashboard
        dashboard = StreamlitDashboard(config)
        print("Starting Streamlit dashboard...")
        print("Run: streamlit run analytics_dashboard.py")
    else:
        # Run Dash dashboard
        dashboard = DashboardApp(config)
        print(f"Starting Dash dashboard on http://localhost:{config.dashboard_port}")
        dashboard.run(debug=True)

if __name__ == "__main__":
    main()