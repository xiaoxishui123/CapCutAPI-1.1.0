"""
MCP Bridge 核心数据模型

本模块定义了 MCP Bridge 系统中使用的核心数据模型，包括服务类型、状态、
端点配置以及请求响应模型等。这些模型为整个系统提供了统一的数据结构。
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class ServiceType(str, Enum):
    """
    服务类型枚举
    
    定义了 MCP Bridge 支持的不同服务类型
    """
    MCP = "mcp"  # MCP 协议服务
    HTTP = "http"  # HTTP 桥接服务
    WEBSOCKET = "websocket"  # WebSocket 服务
    GRPC = "grpc"  # gRPC 服务


class ServiceStatus(str, Enum):
    """
    服务状态枚举
    
    定义了服务的各种运行状态
    """
    ACTIVE = "active"  # 服务正常运行
    INACTIVE = "inactive"  # 服务未激活
    ERROR = "error"  # 服务出现错误
    MAINTENANCE = "maintenance"  # 服务维护中
    STARTING = "starting"  # 服务启动中
    STOPPING = "stopping"  # 服务停止中


class ServiceEndpoint(BaseModel):
    """
    服务端点配置模型
    
    定义了服务端点的基本信息和配置参数
    """
    id: str = Field(..., description="端点唯一标识符")
    name: str = Field(..., description="端点名称")
    service_type: ServiceType = Field(..., description="服务类型")
    host: str = Field(default="localhost", description="服务主机地址")
    port: int = Field(..., description="服务端口号")
    path: str = Field(default="/", description="服务路径")
    status: ServiceStatus = Field(default=ServiceStatus.INACTIVE, description="服务状态")
    health_check_url: Optional[str] = Field(None, description="健康检查URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="端点元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    @property
    def url(self) -> str:
        """
        获取完整的服务URL
        
        Returns:
            str: 完整的服务URL
        """
        protocol = "https" if self.metadata.get("ssl", False) else "http"
        return f"{protocol}://{self.host}:{self.port}{self.path}"
    
    def is_healthy(self) -> bool:
        """
        检查服务是否健康
        
        Returns:
            bool: 服务是否健康
        """
        return self.status == ServiceStatus.ACTIVE


class MCPRequest(BaseModel):
    """
    MCP 请求模型
    
    定义了 MCP 协议请求的标准格式
    """
    id: str = Field(..., description="请求唯一标识符")
    method: str = Field(..., description="请求方法名")
    params: Dict[str, Any] = Field(default_factory=dict, description="请求参数")
    jsonrpc: str = Field(default="2.0", description="JSON-RPC 版本")
    timestamp: datetime = Field(default_factory=datetime.now, description="请求时间戳")
    source_endpoint: Optional[str] = Field(None, description="请求来源端点")
    target_endpoint: Optional[str] = Field(None, description="目标端点")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将请求转换为字典格式
        
        Returns:
            Dict[str, Any]: 请求的字典表示
        """
        return {
            "id": self.id,
            "method": self.method,
            "params": self.params,
            "jsonrpc": self.jsonrpc
        }


class MCPResponse(BaseModel):
    """
    MCP 响应模型
    
    定义了 MCP 协议响应的标准格式
    """
    id: str = Field(..., description="响应对应的请求ID")
    result: Optional[Dict[str, Any]] = Field(None, description="响应结果")
    error: Optional[Dict[str, Any]] = Field(None, description="错误信息")
    jsonrpc: str = Field(default="2.0", description="JSON-RPC 版本")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将响应转换为字典格式
        
        Returns:
            Dict[str, Any]: 响应的字典表示
        """
        response = {
            "id": self.id,
            "jsonrpc": self.jsonrpc
        }
        
        if self.result is not None:
            response["result"] = self.result
        
        if self.error is not None:
            response["error"] = self.error
            
        return response
    
    def is_success(self) -> bool:
        """
        检查响应是否成功
        
        Returns:
            bool: 响应是否成功
        """
        return self.error is None


class ServiceMetrics(BaseModel):
    """
    服务指标模型
    
    定义了服务性能和状态指标
    """
    endpoint_id: str = Field(..., description="端点ID")
    request_count: int = Field(default=0, description="请求总数")
    success_count: int = Field(default=0, description="成功请求数")
    error_count: int = Field(default=0, description="错误请求数")
    avg_response_time: float = Field(default=0.0, description="平均响应时间（秒）")
    last_request_time: Optional[datetime] = Field(None, description="最后请求时间")
    uptime: float = Field(default=0.0, description="运行时间（秒）")
    
    @property
    def success_rate(self) -> float:
        """
        计算成功率
        
        Returns:
            float: 成功率（0-1之间）
        """
        if self.request_count == 0:
            return 0.0
        return self.success_count / self.request_count
    
    @property
    def error_rate(self) -> float:
        """
        计算错误率
        
        Returns:
            float: 错误率（0-1之间）
        """
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count


class HealthCheckResult(BaseModel):
    """
    健康检查结果模型
    
    定义了健康检查的结果格式
    """
    endpoint_id: str = Field(..., description="端点ID")
    status: ServiceStatus = Field(..., description="健康状态")
    response_time: float = Field(..., description="响应时间（秒）")
    message: str = Field(default="", description="状态消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    
    def is_healthy(self) -> bool:
        """
        检查是否健康
        
        Returns:
            bool: 是否健康
        """
        return self.status == ServiceStatus.ACTIVE


class WorkflowStep(BaseModel):
    """
    工作流步骤模型
    
    定义了工作流中单个步骤的结构
    """
    id: str = Field(..., description="步骤ID")
    name: str = Field(..., description="步骤名称")
    service_type: ServiceType = Field(..., description="服务类型")
    endpoint_id: str = Field(..., description="目标端点ID")
    method: str = Field(..., description="调用方法")
    params: Dict[str, Any] = Field(default_factory=dict, description="调用参数")
    timeout: int = Field(default=30, description="超时时间（秒）")
    retry_count: int = Field(default=0, description="重试次数")
    depends_on: List[str] = Field(default_factory=list, description="依赖的步骤ID列表")


class WorkflowExecution(BaseModel):
    """
    工作流执行模型
    
    定义了工作流执行的状态和结果
    """
    id: str = Field(..., description="执行ID")
    workflow_id: str = Field(..., description="工作流ID")
    status: str = Field(default="pending", description="执行状态")
    started_at: datetime = Field(default_factory=datetime.now, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    steps_completed: List[str] = Field(default_factory=list, description="已完成的步骤ID列表")
    current_step: Optional[str] = Field(None, description="当前执行的步骤ID")
    results: Dict[str, Any] = Field(default_factory=dict, description="执行结果")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    
    @property
    def duration(self) -> Optional[float]:
        """
        计算执行持续时间
        
        Returns:
            Optional[float]: 执行持续时间（秒），如果未完成则返回None
        """
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()


class ConfigurationItem(BaseModel):
    """
    配置项模型
    
    定义了系统配置项的结构
    """
    key: str = Field(..., description="配置键")
    value: Union[str, int, float, bool, Dict, List] = Field(..., description="配置值")
    description: str = Field(default="", description="配置描述")
    category: str = Field(default="general", description="配置分类")
    is_sensitive: bool = Field(default=False, description="是否为敏感信息")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


# 导出所有模型类
__all__ = [
    "ServiceType",
    "ServiceStatus", 
    "ServiceEndpoint",
    "MCPRequest",
    "MCPResponse",
    "ServiceMetrics",
    "HealthCheckResult",
    "WorkflowStep",
    "WorkflowExecution",
    "ConfigurationItem"
]