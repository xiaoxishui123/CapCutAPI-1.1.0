"""
MCP Bridge 监控系统
提供性能监控、健康检查、指标收集和告警功能
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import json
from datetime import datetime, timedelta

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import aiohttp


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """健康检查配置"""
    name: str
    check_func: Callable
    interval: int = 30          # 检查间隔（秒）
    timeout: int = 10           # 超时时间（秒）
    retries: int = 3            # 重试次数
    enabled: bool = True
    critical: bool = False      # 是否为关键检查


@dataclass
class MetricConfig:
    """指标配置"""
    name: str
    metric_type: str           # counter, histogram, gauge
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # 用于histogram


@dataclass
class Alert:
    """告警信息"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class SystemMetrics:
    """系统指标"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]
    timestamp: datetime


@dataclass
class ServiceMetrics:
    """服务指标"""
    request_count: int
    error_count: int
    response_time_avg: float
    response_time_p95: float
    response_time_p99: float
    active_connections: int
    cache_hit_rate: float
    timestamp: datetime


class MonitoringSystem:
    """监控系统 - 提供全面的性能监控和健康检查"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化监控系统
        
        Args:
            config: 监控配置
        """
        self.config = config
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_status: Dict[str, HealthStatus] = {}
        self.alerts: List[Alert] = []
        self.metrics_history: List[Dict[str, Any]] = []
        
        # Prometheus指标
        self.registry = CollectorRegistry()
        self._setup_prometheus_metrics()
        
        # 监控任务
        self._monitoring_tasks: List[asyncio.Task] = []
        self._running = False
        
        logger.info("监控系统初始化完成")
    
    def _setup_prometheus_metrics(self) -> None:
        """设置Prometheus指标"""
        # 请求指标
        self.request_counter = Counter(
            'mcp_bridge_requests_total',
            'Total number of requests',
            ['method', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'mcp_bridge_request_duration_seconds',
            'Request duration in seconds',
            ['method'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=self.registry
        )
        
        # 系统指标
        self.cpu_usage = Gauge(
            'mcp_bridge_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'mcp_bridge_memory_usage_percent',
            'Memory usage percentage',
            registry=self.registry
        )
        
        self.active_connections = Gauge(
            'mcp_bridge_active_connections',
            'Number of active connections',
            registry=self.registry
        )
        
        # 缓存指标
        self.cache_hits = Counter(
            'mcp_bridge_cache_hits_total',
            'Total cache hits',
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'mcp_bridge_cache_misses_total',
            'Total cache misses',
            registry=self.registry
        )
        
        # 健康检查指标
        self.health_check_status = Gauge(
            'mcp_bridge_health_check_status',
            'Health check status (1=healthy, 0=unhealthy)',
            ['check_name'],
            registry=self.registry
        )
    
    async def start(self) -> None:
        """启动监控系统"""
        if self._running:
            return
        
        self._running = True
        
        # 启动健康检查任务
        for check_name, health_check in self.health_checks.items():
            if health_check.enabled:
                task = asyncio.create_task(
                    self._run_health_check(check_name, health_check)
                )
                self._monitoring_tasks.append(task)
        
        # 启动系统指标收集任务
        metrics_task = asyncio.create_task(self._collect_system_metrics())
        self._monitoring_tasks.append(metrics_task)
        
        # 启动告警检查任务
        alert_task = asyncio.create_task(self._check_alerts())
        self._monitoring_tasks.append(alert_task)
        
        logger.info("监控系统已启动")
    
    async def stop(self) -> None:
        """停止监控系统"""
        self._running = False
        
        # 取消所有监控任务
        for task in self._monitoring_tasks:
            task.cancel()
        
        # 等待任务完成
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks, return_exceptions=True)
        
        self._monitoring_tasks.clear()
        logger.info("监控系统已停止")
    
    def register_health_check(self, health_check: HealthCheck) -> None:
        """
        注册健康检查
        
        Args:
            health_check: 健康检查配置
        """
        self.health_checks[health_check.name] = health_check
        self.health_status[health_check.name] = HealthStatus.UNKNOWN
        
        logger.info(f"注册健康检查: {health_check.name}")
    
    async def _run_health_check(self, check_name: str, health_check: HealthCheck) -> None:
        """运行健康检查"""
        while self._running:
            try:
                start_time = time.time()
                
                # 执行健康检查
                for attempt in range(health_check.retries + 1):
                    try:
                        result = await asyncio.wait_for(
                            health_check.check_func(),
                            timeout=health_check.timeout
                        )
                        
                        if result:
                            self.health_status[check_name] = HealthStatus.HEALTHY
                            self.health_check_status.labels(check_name=check_name).set(1)
                            break
                        else:
                            if attempt == health_check.retries:
                                self.health_status[check_name] = HealthStatus.UNHEALTHY
                                self.health_check_status.labels(check_name=check_name).set(0)
                                
                                # 生成告警
                                await self._create_alert(
                                    AlertLevel.ERROR if health_check.critical else AlertLevel.WARNING,
                                    f"健康检查失败: {check_name}",
                                    f"健康检查 {check_name} 连续 {health_check.retries + 1} 次失败",
                                    f"health_check_{check_name}"
                                )
                    
                    except asyncio.TimeoutError:
                        if attempt == health_check.retries:
                            self.health_status[check_name] = HealthStatus.UNHEALTHY
                            self.health_check_status.labels(check_name=check_name).set(0)
                            
                            await self._create_alert(
                                AlertLevel.ERROR,
                                f"健康检查超时: {check_name}",
                                f"健康检查 {check_name} 超时 ({health_check.timeout}s)",
                                f"health_check_{check_name}_timeout"
                            )
                    
                    except Exception as e:
                        if attempt == health_check.retries:
                            self.health_status[check_name] = HealthStatus.UNHEALTHY
                            self.health_check_status.labels(check_name=check_name).set(0)
                            
                            await self._create_alert(
                                AlertLevel.ERROR,
                                f"健康检查异常: {check_name}",
                                f"健康检查 {check_name} 发生异常: {str(e)}",
                                f"health_check_{check_name}_error"
                            )
                        
                        logger.error(f"健康检查 {check_name} 异常: {str(e)}")
                
                # 等待下次检查
                await asyncio.sleep(health_check.interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查任务 {check_name} 异常: {str(e)}")
                await asyncio.sleep(health_check.interval)
    
    async def _collect_system_metrics(self) -> None:
        """收集系统指标"""
        while self._running:
            try:
                # 收集系统指标
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                load_avg = psutil.getloadavg()
                
                # 更新Prometheus指标
                self.cpu_usage.set(cpu_percent)
                self.memory_usage.set(memory.percent)
                
                # 创建系统指标对象
                system_metrics = SystemMetrics(
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    disk_percent=disk.percent,
                    network_io={
                        'bytes_sent': network.bytes_sent,
                        'bytes_recv': network.bytes_recv,
                        'packets_sent': network.packets_sent,
                        'packets_recv': network.packets_recv
                    },
                    process_count=len(psutil.pids()),
                    load_average=list(load_avg),
                    timestamp=datetime.now()
                )
                
                # 保存到历史记录
                self.metrics_history.append({
                    'type': 'system',
                    'data': system_metrics.__dict__,
                    'timestamp': system_metrics.timestamp.isoformat()
                })
                
                # 限制历史记录大小
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-500:]
                
                # 检查阈值告警
                await self._check_system_thresholds(system_metrics)
                
                await asyncio.sleep(30)  # 每30秒收集一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"系统指标收集异常: {str(e)}")
                await asyncio.sleep(30)
    
    async def _check_system_thresholds(self, metrics: SystemMetrics) -> None:
        """检查系统阈值告警"""
        thresholds = self.config.get('thresholds', {})
        
        # CPU使用率告警
        cpu_threshold = thresholds.get('cpu_percent', 80)
        if metrics.cpu_percent > cpu_threshold:
            await self._create_alert(
                AlertLevel.WARNING,
                "CPU使用率过高",
                f"CPU使用率 {metrics.cpu_percent:.1f}% 超过阈值 {cpu_threshold}%",
                "system_cpu_high"
            )
        
        # 内存使用率告警
        memory_threshold = thresholds.get('memory_percent', 85)
        if metrics.memory_percent > memory_threshold:
            await self._create_alert(
                AlertLevel.WARNING,
                "内存使用率过高",
                f"内存使用率 {metrics.memory_percent:.1f}% 超过阈值 {memory_threshold}%",
                "system_memory_high"
            )
        
        # 磁盘使用率告警
        disk_threshold = thresholds.get('disk_percent', 90)
        if metrics.disk_percent > disk_threshold:
            await self._create_alert(
                AlertLevel.ERROR,
                "磁盘使用率过高",
                f"磁盘使用率 {metrics.disk_percent:.1f}% 超过阈值 {disk_threshold}%",
                "system_disk_high"
            )
    
    async def _check_alerts(self) -> None:
        """检查和处理告警"""
        while self._running:
            try:
                # 检查告警自动恢复
                current_time = datetime.now()
                for alert in self.alerts:
                    if not alert.resolved:
                        # 检查是否可以自动恢复
                        if await self._should_resolve_alert(alert):
                            alert.resolved = True
                            alert.resolved_at = current_time
                            logger.info(f"告警自动恢复: {alert.title}")
                
                # 清理过期的已恢复告警
                retention_hours = self.config.get('alert_retention_hours', 24)
                cutoff_time = current_time - timedelta(hours=retention_hours)
                self.alerts = [
                    alert for alert in self.alerts
                    if not alert.resolved or 
                    (alert.resolved_at and alert.resolved_at > cutoff_time)
                ]
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"告警检查异常: {str(e)}")
                await asyncio.sleep(60)
    
    async def _should_resolve_alert(self, alert: Alert) -> bool:
        """检查告警是否应该自动恢复"""
        # 根据告警源判断恢复条件
        if alert.source.startswith("health_check_"):
            check_name = alert.source.replace("health_check_", "").replace("_timeout", "").replace("_error", "")
            return self.health_status.get(check_name) == HealthStatus.HEALTHY
        
        elif alert.source == "system_cpu_high":
            # 检查最近的CPU使用率
            recent_metrics = [
                m for m in self.metrics_history[-5:]
                if m['type'] == 'system'
            ]
            if recent_metrics:
                avg_cpu = sum(m['data']['cpu_percent'] for m in recent_metrics) / len(recent_metrics)
                return avg_cpu < self.config.get('thresholds', {}).get('cpu_percent', 80)
        
        # 其他告警类型的恢复逻辑...
        
        return False
    
    async def _create_alert(self, level: AlertLevel, title: str, message: str, source: str) -> None:
        """创建告警"""
        # 检查是否已存在相同的未恢复告警
        existing_alert = next(
            (alert for alert in self.alerts 
             if alert.source == source and not alert.resolved),
            None
        )
        
        if existing_alert:
            return  # 避免重复告警
        
        alert = Alert(
            id=f"{source}_{int(time.time())}",
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source=source
        )
        
        self.alerts.append(alert)
        logger.warning(f"新告警: [{level.value.upper()}] {title} - {message}")
        
        # 发送告警通知
        await self._send_alert_notification(alert)
    
    async def _send_alert_notification(self, alert: Alert) -> None:
        """发送告警通知"""
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            return
        
        try:
            payload = {
                'alert_id': alert.id,
                'level': alert.level.value,
                'title': alert.title,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'source': alert.source
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"告警通知发送成功: {alert.id}")
                    else:
                        logger.error(f"告警通知发送失败: {response.status}")
        
        except Exception as e:
            logger.error(f"发送告警通知异常: {str(e)}")
    
    @asynccontextmanager
    async def request_context(self, method: str):
        """请求监控上下文管理器"""
        start_time = time.time()
        
        try:
            yield
            
            # 记录成功请求
            duration = time.time() - start_time
            self.request_counter.labels(method=method, status='success').inc()
            self.request_duration.labels(method=method).observe(duration)
            
        except Exception as e:
            # 记录失败请求
            duration = time.time() - start_time
            self.request_counter.labels(method=method, status='error').inc()
            self.request_duration.labels(method=method).observe(duration)
            
            # 创建错误告警
            await self._create_alert(
                AlertLevel.ERROR,
                f"请求失败: {method}",
                f"方法 {method} 执行失败: {str(e)}",
                f"request_error_{method}"
            )
            
            raise
    
    def record_cache_hit(self) -> None:
        """记录缓存命中"""
        self.cache_hits.inc()
    
    def record_cache_miss(self) -> None:
        """记录缓存未命中"""
        self.cache_misses.inc()
    
    def update_active_connections(self, count: int) -> None:
        """更新活跃连接数"""
        self.active_connections.set(count)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取整体健康状态"""
        overall_status = HealthStatus.HEALTHY
        
        # 检查关键健康检查
        for check_name, health_check in self.health_checks.items():
            if health_check.critical and health_check.enabled:
                status = self.health_status.get(check_name, HealthStatus.UNKNOWN)
                if status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                    break
                elif status == HealthStatus.DEGRADED:
                    overall_status = HealthStatus.DEGRADED
        
        # 统计告警
        active_alerts = [alert for alert in self.alerts if not alert.resolved]
        critical_alerts = [alert for alert in active_alerts if alert.level == AlertLevel.CRITICAL]
        
        if critical_alerts:
            overall_status = HealthStatus.UNHEALTHY
        elif active_alerts:
            if overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'checks': {
                name: status.value 
                for name, status in self.health_status.items()
            },
            'alerts': {
                'total': len(active_alerts),
                'critical': len(critical_alerts),
                'error': len([a for a in active_alerts if a.level == AlertLevel.ERROR]),
                'warning': len([a for a in active_alerts if a.level == AlertLevel.WARNING])
            }
        }
    
    async def get_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        return generate_latest(self.registry).decode('utf-8')
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        if not self.metrics_history:
            return {}
        
        # 获取最新的系统指标
        latest_system_metrics = None
        for metric in reversed(self.metrics_history):
            if metric['type'] == 'system':
                latest_system_metrics = metric['data']
                break
        
        return latest_system_metrics or {}
    
    async def get_alerts(self, resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        获取告警列表
        
        Args:
            resolved: 是否已解决，None表示获取所有告警
            
        Returns:
            告警列表
        """
        alerts = self.alerts
        
        if resolved is not None:
            alerts = [alert for alert in alerts if alert.resolved == resolved]
        
        return [
            {
                'id': alert.id,
                'level': alert.level.value,
                'title': alert.title,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'source': alert.source,
                'resolved': alert.resolved,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
            }
            for alert in alerts
        ]
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """
        手动解决告警
        
        Args:
            alert_id: 告警ID
            
        Returns:
            是否成功解决
        """
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"手动解决告警: {alert.title}")
                return True
        
        return False


# 预定义的健康检查函数
async def check_redis_health(redis_client) -> bool:
    """检查Redis健康状态"""
    try:
        if redis_client:
            await redis_client.ping()
            return True
        return False
    except Exception:
        return False


async def check_http_endpoint_health(url: str, timeout: int = 5) -> bool:
    """检查HTTP端点健康状态"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                return response.status == 200
    except Exception:
        return False


async def check_disk_space_health(path: str = '/', threshold: float = 90.0) -> bool:
    """检查磁盘空间健康状态"""
    try:
        disk_usage = psutil.disk_usage(path)
        usage_percent = (disk_usage.used / disk_usage.total) * 100
        return usage_percent < threshold
    except Exception:
        return False