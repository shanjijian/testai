import os
import yaml
from functools import lru_cache
from pathlib import Path
from typing import Optional, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from pydantic import BaseModel, Field, AliasChoices, ConfigDict, model_validator

class LLMSettings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    api_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("llm_api_key", "LLM_API_KEY"))
    base_url: Optional[str] = Field(default=None, validation_alias=AliasChoices("llm_base_url", "LLM_BASE_URL"))
    model: Optional[str] = Field(default=None, validation_alias=AliasChoices("llm_model", "LLM_MODEL"))
    temperature: float = Field(default=0.7, validation_alias=AliasChoices("llm_temperature", "LLM_TEMPERATURE"))
    timeout: int = Field(default=300, validation_alias=AliasChoices("llm_timeout", "LLM_TIMEOUT"))

class StorageSettings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    cos_secret_id: Optional[str] = Field(default=None, validation_alias=AliasChoices("cos_secret_id", "COS_SECRET_ID"))
    cos_secret_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("cos_secret_key", "COS_SECRET_KEY"))
    region: str = Field(default="ap-beijing", validation_alias=AliasChoices("cos_region", "COS_REGION"))
    bucket: Optional[str] = Field(default=None, validation_alias=AliasChoices("cos_bucket", "COS_BUCKET"))

class DatabaseSettings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/testai_agent",
        validation_alias=AliasChoices("postgres_url", "POSTGRES_URL", "database_url")
    )

class SandboxSettings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    url: str = Field(default="http://localhost:8090", validation_alias=AliasChoices("opensandbox_url", "OPENSANDBOX_URL"))
    api_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("opensandbox_api_key", "OPENSANDBOX_API_KEY"))

class SkillSettings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    main_dir: Path = Field(default=Path("skills"), validation_alias=AliasChoices("main_skills_dir", "MAIN_SKILLS_DIR"))
    sub1_dir: Path = Field(default=Path("skills"), validation_alias=AliasChoices("sub1_skills_dir", "SUB1_SKILLS_DIR"))
    sub2_dir: Path = Path("skills")

class LangfuseSettings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    public_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("langfuse_public_key", "LANGFUSE_PUBLIC_KEY"))
    secret_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("langfuse_secret_key", "LANGFUSE_SECRET_KEY"))
    base_url: str = Field(default="https://cloud.langfuse.com", validation_alias=AliasChoices("langfuse_base_url", "LANGFUSE_BASE_URL"))

class JDCloudSettings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    ak: Optional[str] = Field(default=None, validation_alias=AliasChoices("jdcloud_ak", "JDCLOUD_AK"))
    sk: Optional[str] = Field(default=None, validation_alias=AliasChoices("jdcloud_sk", "JDCLOUD_SK"))
    region: str = Field(default="cn-north-1", validation_alias=AliasChoices("default_region", "DEFAULT_REGION"))

class Settings(BaseSettings):
    """带验证的应用程序设置 (嵌套模型)。"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",  # 支持 LLM__API_KEY 等标准嵌套写法
    )
    
    llm: LLMSettings = Field(default_factory=LLMSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings, validation_alias=AliasChoices("storage", "cos"))
    database: DatabaseSettings = Field(default_factory=DatabaseSettings, validation_alias=AliasChoices("database", "postgres"))
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings, validation_alias=AliasChoices("sandbox", "opensandbox"))
    skills: SkillSettings = Field(default_factory=SkillSettings)
    langfuse: LangfuseSettings = Field(default_factory=LangfuseSettings)
    jdcloud: JDCloudSettings = Field(default_factory=JDCloudSettings)
    recursion_limit: int = Field(default=100, validation_alias=AliasChoices("recursion_limit", "RECURSION_LIMIT"))

    @model_validator(mode="before")
    @classmethod
    def pull_flat_env_vars(cls, data: Any) -> Any:
        """自动将 .env 中的扁平化环境变量 (如 LLM_API_KEY) 映射到嵌套结构。"""
        if not isinstance(data, dict):
            data = {}
        
        # 定义环境变量前缀到配置分类的映射
        mappings = {
            "LLM_": "llm",
            "COS_": "storage",
            "POSTGRES_": "database",
            "OPENSANDBOX_": "sandbox",
            "LANGFUSE_": "langfuse",
            "JDCLOUD_": "jdcloud",
        }
        
        # 遍历所有环境变量并按前缀归类
        for env_key, value in os.environ.items():
            for prefix, target_field in mappings.items():
                if env_key.startswith(prefix):
                    sub_key = env_key[len(prefix):].lower()
                    if target_field not in data:
                        data[target_field] = {}
                    # 只有当 YAML 中没有设置该字段时，才使用环境变量补充
                    if isinstance(data[target_field], dict) and sub_key not in data[target_field]:
                        data[target_field][sub_key] = value
        
        # 处理不带标准前缀的特殊映射
        if os.getenv("DEFAULT_REGION"):
            if "jdcloud" not in data: data["jdcloud"] = {}
            if "region" not in data["jdcloud"]: data["jdcloud"]["region"] = os.getenv("DEFAULT_REGION")
            
        if os.getenv("TAVILY_API_KEY"):
            # 如果有特殊变量，也可以合并到对应的分类或保留在顶级 (如果 model 支持)
            pass

        return data

@lru_cache()
def get_settings() -> Settings:
    """获取单例 Settings 实例 (优先自 configs/config.yaml)。"""
    # 先从 YAML 加载，如果失败，从环境变量加载
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    CONFIG_DIR = PROJECT_ROOT / "configs"
    config_path = CONFIG_DIR / "config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f) or {}
            return Settings(**yaml_data)
    return Settings()
