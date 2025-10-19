#!/usr/bin/env python3
"""
Система мониторинга серверов и приложений
Создано: Сентябрь 2024
"""

import psutil
import requests
import time
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import sqlite3
import os
from prometheus_client import start_http_server, Gauge, Counter, Histogram

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler()
    ]
)

class SystemMonitor:
    def __init__(self, config_file='monitor_config.json'):
        self.config = self.load_config(config_file)
        self.db_path = 'data/monitoring.db'
        self.init_database()
        
        # Prometheus метрики
        self.cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
        self.memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
        self.disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage')
        self.load_average = Gauge('system_load_average', 'System load average')
        self.web_service_up = Gauge('web_service_up', 'Web service status', ['service_name'])
        self.web_service_response_time = Histogram('web_service_response_time_seconds', 'Web service response time', ['service_name'])
    
    def load_config(self, config_file):
        """Загрузка конфигурации"""
        default_config = {
            'check_interval': 60,  # секунды
            'cpu_threshold': 80,   # %
            'memory_threshold': 85, # %
            'disk_threshold': 90,   # %
            'email_alerts': True,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email_from': 'monitor@example.com',
            'email_to': 'admin@example.com',
            'email_password': '',
            'web_endpoints': [
                {'name': 'Main App', 'url': 'http://localhost:8000/health'},
                {'name': 'API Service', 'url': 'http://localhost:3000/api/health'}
            ]
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL,
                load_average REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS web_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                endpoint_name TEXT,
                url TEXT,
                status_code INTEGER,
                response_time REAL,
                is_up BOOLEAN
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT,
                message TEXT,
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_system_metrics(self):
        """Получение системных метрик"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0
            
            metrics = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'load_average': load_avg,
                'timestamp': datetime.now().isoformat()
            }
            
            # Обновление Prometheus метрик
            self.cpu_usage.set(cpu_percent)
            self.memory_usage.set(memory.percent)
            self.disk_usage.set(disk.percent)
            self.load_average.set(load_avg)
            
            # Сохранение в базу данных
            self.save_system_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logging.error(f"Ошибка при получении системных метрик: {e}")
            return None
    
    def save_system_metrics(self, metrics):
        """Сохранение системных метрик в БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_metrics 
            (cpu_percent, memory_percent, disk_percent, load_average)
            VALUES (?, ?, ?, ?)
        ''', (
            metrics['cpu_percent'],
            metrics['memory_percent'],
            metrics['disk_percent'],
            metrics['load_average']
        ))
        
        conn.commit()
        conn.close()
    
    def check_web_endpoints(self):
        """Проверка веб-эндпоинтов"""
        results = []
        
        for endpoint in self.config['web_endpoints']:
            try:
                start_time = time.time()
                response = requests.get(endpoint['url'], timeout=10)
                response_time = time.time() - start_time
                
                is_up = response.status_code == 200
                
                result = {
                    'name': endpoint['name'],
                    'url': endpoint['url'],
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'is_up': is_up,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Обновление Prometheus метрик
                self.web_service_up.labels(service_name=endpoint['name']).set(1 if is_up else 0)
                self.web_service_response_time.labels(service_name=endpoint['name']).observe(response_time)
                
                # Сохранение в БД
                self.save_web_check(result)
                
                results.append(result)
                
                if not is_up:
                    self.send_alert('web_down', f"Сервис {endpoint['name']} недоступен")
                
            except Exception as e:
                result = {
                    'name': endpoint['name'],
                    'url': endpoint['url'],
                    'status_code': 0,
                    'response_time': 0,
                    'is_up': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Обновление Prometheus метрик для ошибок
                self.web_service_up.labels(service_name=endpoint['name']).set(0)
                self.web_service_response_time.labels(service_name=endpoint['name']).observe(0)
                
                self.save_web_check(result)
                results.append(result)
                
                self.send_alert('web_error', f"Ошибка проверки {endpoint['name']}: {e}")
        
        return results
    
    def save_web_check(self, result):
        """Сохранение результата проверки веб-эндпоинта"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO web_checks 
            (endpoint_name, url, status_code, response_time, is_up)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            result['name'],
            result['url'],
            result['status_code'],
            result['response_time'],
            result['is_up']
        ))
        
        conn.commit()
        conn.close()
    
    def check_thresholds(self, metrics):
        """Проверка превышения пороговых значений"""
        alerts = []
        
        if metrics['cpu_percent'] > self.config['cpu_threshold']:
            alerts.append({
                'type': 'high_cpu',
                'message': f"Высокая загрузка CPU: {metrics['cpu_percent']:.1f}%"
            })
        
        if metrics['memory_percent'] > self.config['memory_threshold']:
            alerts.append({
                'type': 'high_memory',
                'message': f"Высокое использование памяти: {metrics['memory_percent']:.1f}%"
            })
        
        if metrics['disk_percent'] > self.config['disk_threshold']:
            alerts.append({
                'type': 'high_disk',
                'message': f"Мало места на диске: {metrics['disk_percent']:.1f}%"
            })
        
        for alert in alerts:
            self.send_alert(alert['type'], alert['message'])
        
        return alerts
    
    def send_alert(self, alert_type, message):
        """Отправка уведомления"""
        if not self.config['email_alerts']:
            return
        
        try:
            # Сохранение в БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts (alert_type, message)
                VALUES (?, ?)
            ''', (alert_type, message))
            
            conn.commit()
            conn.close()
            
            # Отправка email
            self.send_email(alert_type, message)
            
            logging.warning(f"ALERT: {message}")
            
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления: {e}")
    
    def send_email(self, alert_type, message):
        """Отправка email уведомления"""
        if not self.config.get('email_password'):
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email_from']
            msg['To'] = self.config['email_to']
            msg['Subject'] = f"Мониторинг: {alert_type.upper()}"
            
            body = f"""
            Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Тип: {alert_type}
            Сообщение: {message}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['email_from'], self.config['email_password'])
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logging.error(f"Ошибка при отправке email: {e}")
    
    def generate_report(self, hours=24):
        """Генерация отчета за указанный период"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Системные метрики
        cursor.execute('''
            SELECT AVG(cpu_percent), AVG(memory_percent), AVG(disk_percent)
            FROM system_metrics 
            WHERE timestamp > datetime('now', '-{} hours')
        '''.format(hours))
        
        avg_metrics = cursor.fetchone()
        
        # Веб-проверки
        cursor.execute('''
            SELECT endpoint_name, 
                   COUNT(*) as total_checks,
                   SUM(CASE WHEN is_up = 1 THEN 1 ELSE 0 END) as successful_checks,
                   AVG(response_time) as avg_response_time
            FROM web_checks 
            WHERE timestamp > datetime('now', '-{} hours')
            GROUP BY endpoint_name
        '''.format(hours))
        
        web_stats = cursor.fetchall()
        
        # Активные алерты
        cursor.execute('''
            SELECT COUNT(*) FROM alerts 
            WHERE resolved = 0 AND timestamp > datetime('now', '-{} hours')
        '''.format(hours))
        
        active_alerts = cursor.fetchone()[0]
        
        conn.close()
        
        report = {
            'period_hours': hours,
            'avg_cpu': avg_metrics[0] if avg_metrics[0] else 0,
            'avg_memory': avg_metrics[1] if avg_metrics[1] else 0,
            'avg_disk': avg_metrics[2] if avg_metrics[2] else 0,
            'web_endpoints': [
                {
                    'name': stat[0],
                    'total_checks': stat[1],
                    'successful_checks': stat[2],
                    'uptime_percent': (stat[2] / stat[1] * 100) if stat[1] > 0 else 0,
                    'avg_response_time': stat[3] if stat[3] else 0
                }
                for stat in web_stats
            ],
            'active_alerts': active_alerts,
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def run_monitoring_cycle(self):
        """Выполнение одного цикла мониторинга"""
        logging.info("Начало цикла мониторинга")
        
        # Системные метрики
        metrics = self.get_system_metrics()
        if metrics:
            self.check_thresholds(metrics)
        
        # Проверка веб-эндпоинтов
        web_results = self.check_web_endpoints()
        
        logging.info("Цикл мониторинга завершен")
        return metrics, web_results
    
    def start_monitoring(self):
        """Запуск непрерывного мониторинга"""
        logging.info("Запуск системы мониторинга")
        
        try:
            while True:
                self.run_monitoring_cycle()
                time.sleep(self.config['check_interval'])
                
        except KeyboardInterrupt:
            logging.info("Остановка системы мониторинга")
        except Exception as e:
            logging.error(f"Критическая ошибка в системе мониторинга: {e}")

def main():
    """Основная функция"""
    monitor = SystemMonitor()
    
    # Запуск Prometheus HTTP сервера на порту 8000
    start_http_server(8000)
    logging.info("Prometheus metrics server started on port 8000")
    
    # Генерация отчета за последние 24 часа
    report = monitor.generate_report(24)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # Запуск мониторинга
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
