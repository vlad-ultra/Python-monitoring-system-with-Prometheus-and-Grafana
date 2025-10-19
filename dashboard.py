#!/usr/bin/env python3
"""
Веб-дашборд для системы мониторинга
Создано: Октябрь 2024
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)

class MonitoringDashboard:
    def __init__(self, db_path='data/monitoring.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создание таблицы system_metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL,
                load_average REAL,
                timestamp TEXT
            )
        ''')
        
        # Создание таблицы web_checks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS web_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                url TEXT,
                status_code INTEGER,
                response_time REAL,
                is_up BOOLEAN,
                error TEXT,
                timestamp TEXT
            )
        ''')
        
        # Создание таблицы alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT,
                message TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_latest_metrics(self):
        """Получение последних метрик"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cpu_percent, memory_percent, disk_percent, load_average, timestamp
            FROM system_metrics 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'cpu_percent': result[0],
                'memory_percent': result[1],
                'disk_percent': result[2],
                'load_average': result[3],
                'timestamp': result[4]
            }
        return None
    
    def get_metrics_history(self, hours=24):
        """Получение истории метрик"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cpu_percent, memory_percent, disk_percent, timestamp
            FROM system_metrics 
            WHERE timestamp > datetime('now', '-{} hours')
            ORDER BY timestamp ASC
        '''.format(hours))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'cpu_percent': row[0],
                'memory_percent': row[1],
                'disk_percent': row[2],
                'timestamp': row[3]
            }
            for row in results
        ]
    
    def get_web_status(self):
        """Получение статуса веб-сервисов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT endpoint_name, url, status_code, response_time, is_up, timestamp
            FROM web_checks 
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY timestamp DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        # Группируем по эндпоинтам и берем последний статус
        endpoints = {}
        for row in results:
            name = row[0]
            if name not in endpoints:
                endpoints[name] = {
                    'name': name,
                    'url': row[1],
                    'status_code': row[2],
                    'response_time': row[3],
                    'is_up': bool(row[4]),
                    'timestamp': row[5]
                }
        
        return list(endpoints.values())
    
    def get_alerts(self, limit=10):
        """Получение последних алертов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT alert_type, message, timestamp, resolved
            FROM alerts 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'type': row[0],
                'message': row[1],
                'timestamp': row[2],
                'resolved': bool(row[3])
            }
            for row in results
        ]
    
    def get_uptime_stats(self, hours=24):
        """Получение статистики uptime"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT endpoint_name,
                   COUNT(*) as total_checks,
                   SUM(CASE WHEN is_up = 1 THEN 1 ELSE 0 END) as successful_checks,
                   AVG(response_time) as avg_response_time
            FROM web_checks 
            WHERE timestamp > datetime('now', '-{} hours')
            GROUP BY endpoint_name
        '''.format(hours))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'name': row[0],
                'total_checks': row[1],
                'successful_checks': row[2],
                'uptime_percent': (row[2] / row[1] * 100) if row[1] > 0 else 0,
                'avg_response_time': row[3] if row[3] else 0
            }
            for row in results
        ]

dashboard = MonitoringDashboard()

@app.route('/')
def index():
    """Главная страница дашборда"""
    return render_template('dashboard.html')

@app.route('/api/metrics/current')
def api_current_metrics():
    """API для получения текущих метрик"""
    metrics = dashboard.get_latest_metrics()
    return jsonify(metrics)

@app.route('/api/metrics/history')
def api_metrics_history():
    """API для получения истории метрик"""
    hours = request.args.get('hours', 24, type=int)
    history = dashboard.get_metrics_history(hours)
    return jsonify(history)

@app.route('/api/web/status')
def api_web_status():
    """API для получения статуса веб-сервисов"""
    status = dashboard.get_web_status()
    return jsonify(status)

@app.route('/api/alerts')
def api_alerts():
    """API для получения алертов"""
    limit = request.args.get('limit', 10, type=int)
    alerts = dashboard.get_alerts(limit)
    return jsonify(alerts)

@app.route('/api/uptime')
def api_uptime():
    """API для получения статистики uptime"""
    hours = request.args.get('hours', 24, type=int)
    stats = dashboard.get_uptime_stats(hours)
    return jsonify(stats)

if __name__ == '__main__':
    # Создаем директорию для шаблонов
    os.makedirs('templates', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
