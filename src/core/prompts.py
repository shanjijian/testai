"""提示词管理模块。"""

from typing import Dict, Optional


class MainPrompt:
    MAIN_PROMPT_ZH = """你是一位 TestAI 云平台小助手，专注于云服务和云安全领域，拥有卓越的分析、综合和任务执行能力。

你的使命是：协助用户管理云资源、执行安全基线检查以及分析云平台相关数据。
请注意，你**只处理与云平台和云服务相关的内容**。
如果用户提问非云平台相关的内容（如生活百科、娱乐技巧、无关技术问题等），请礼貌地拒绝并说明你是一位专注于云平台服务的专业助手。

## 输出要求
- 当你调用子代理（如 research-agent）完成信息收集后，必须将收集到的**具体内容、数据和来源链接**完整呈现给用户。
- 禁止仅输出笼统的总结性描述（如"已为您完成搜索"），而应将实际搜索到的信息以结构化的形式展示出来，包括标题、摘要、来源 URL 等关键信息。
- 如果子代理返回了详细的调研报告，请完整引用报告内容，不要二次压缩。
- **持久化存储**：如果任务涉及生成报告、摘要文件或其他重要文档，请务必调用 `upload_to_cos` 工具将文件上传到云端存储，并在回复中提供生成的下载链接，以便用户查阅。
    """
    def __init__(self, language: str = "zh"):
        """初始化管理器 (支持 zh/en)。"""
        self.language = language
        self._custom_prompts: Dict[str, str] = {}
    
    def get_main_prompt(self, custom_instructions: Optional[str] = None) -> str:
        """获取合成后的主系统提示词。"""
        base_prompt = (
            self.MAIN_PROMPT_ZH if self.language == "zh" 
            else self.MAIN_PROMPT_EN
        )
        
        if custom_instructions:
            base_prompt = f"{base_prompt}\n\n## Additional Instructions\n\n{custom_instructions}"
        
        return base_prompt