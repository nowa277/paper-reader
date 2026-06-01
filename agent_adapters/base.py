from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class AdapterConfig:
    """适配器配置"""
    name: str                          # 显示名称
    id: str                            # 唯一标识符
    config_file: str                   # 配置文件路径
    skill_format: str                  # 技能格式 (markdown/yaml/json)
    command_prefix: str                # 命令前缀

@dataclass
class GenerationResult:
    """生成结果"""
    success: bool
    output_files: list[str]
    errors: list[str]

class BaseAdapter(ABC):
    """Agent 适配器抽象基类"""

    @abstractmethod
    def get_config(self) -> AdapterConfig:
        """获取适配器配置"""
        pass

    @abstractmethod
    def generate_skill_file(self, skill_source: str) -> str:
        """生成技能文件"""
        pass

    @abstractmethod
    def generate_config_file(self, config: dict) -> str:
        """生成配置文件"""
        pass

    @abstractmethod
    def detect_installation(self) -> bool:
        """检测 Agent 是否已安装"""
        pass

    @abstractmethod
    def get_installation_instructions(self) -> str:
        """获取安装指南"""
        pass
