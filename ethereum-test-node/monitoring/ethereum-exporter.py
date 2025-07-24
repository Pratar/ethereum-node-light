#!/usr/bin/env python3
"""
Простой экспортер метрик для Ethereum node
Преобразует JSON метрики geth в формат Prometheus
"""

import requests
import json
import time
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class MetricsExporter(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            
            try:
                # Получаем метрики от geth
                response = requests.get('http://ethereum-node:6060/debug/metrics', timeout=5)
                if response.status_code == 200:
                    metrics_data = response.json()
                    
                    # Преобразуем в формат Prometheus
                    prometheus_metrics = self.convert_to_prometheus(metrics_data)
                    self.wfile.write(prometheus_metrics.encode())
                else:
                    self.wfile.write(b'# Error: Could not fetch metrics from geth\n')
            except Exception as e:
                self.wfile.write(f'# Error: {str(e)}\n'.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def convert_to_prometheus(self, metrics_data):
        """Преобразует JSON метрики в формат Prometheus"""
        prometheus_lines = []
        
        # Добавляем информацию о метриках
        prometheus_lines.append('# HELP ethereum_node_info Ethereum node information')
        prometheus_lines.append('# TYPE ethereum_node_info gauge')
        prometheus_lines.append('ethereum_node_info{version="geth"} 1')
        
        # Обрабатываем основные метрики
        for key, value in metrics_data.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                # Преобразуем ключ в формат Prometheus
                metric_name = self.sanitize_metric_name(key)
                prometheus_lines.append(f'# HELP {metric_name} {key}')
                prometheus_lines.append(f'# TYPE {metric_name} gauge')
                prometheus_lines.append(f'{metric_name} {value}')
            # Исключаем булевы значения для избежания ошибок парсинга
        
        # Обрабатываем memstats
        if 'memstats' in metrics_data:
            memstats = metrics_data['memstats']
            for key, value in memstats.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    metric_name = f'ethereum_memory_{self.sanitize_metric_name(key)}'
                    prometheus_lines.append(f'# HELP {metric_name} Memory statistic: {key}')
                    prometheus_lines.append(f'# TYPE {metric_name} gauge')
                    prometheus_lines.append(f'{metric_name} {value}')
                # Исключаем булевы значения для избежания ошибок парсинга
        
        return '\n'.join(prometheus_lines) + '\n'
    
    def sanitize_metric_name(self, name):
        """Преобразует имя метрики в формат Prometheus"""
        # Заменяем недопустимые символы
        name = re.sub(r'[^a-zA-Z0-9_:]', '_', name)
        # Убираем множественные подчеркивания
        name = re.sub(r'_+', '_', name)
        # Убираем подчеркивания в начале и конце
        name = name.strip('_')
        return name
    
    def log_message(self, format, *args):
        # Отключаем логирование для чистоты вывода
        pass

def run_exporter(port=9091):
    """Запускает экспортер метрик"""
    server = HTTPServer(('0.0.0.0', port), MetricsExporter)
    print(f'Starting metrics exporter on port {port}')
    server.serve_forever()

if __name__ == '__main__':
    run_exporter() 