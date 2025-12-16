import httpx
from datetime import datetime, timezone, timedelta
from app.core.config import get_settings

settings = get_settings()

# 东八区时区
UTC8 = timezone(timedelta(hours=8))


class AIService:
    """OpenAI兼容的AI服务"""

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url  # 保留原始格式，用于判断URL拼接方式
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature

    def is_configured(self) -> bool:
        """检查是否已配置API密钥"""
        return bool(self.api_key)

    async def chat_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        expert_mode: bool = False,
    ) -> str:
        """
        调用Chat Completion API

        Args:
            prompt: 用户输入的提示词
            system_prompt: 系统提示词（可选）
            expert_mode: 专家模式，使用更详细的提示

        Returns:
            AI生成的回复内容
        """
        if not self.is_configured():
            return self._generate_mock_response(prompt, expert_mode)

        # 构建消息列表
        messages = []

        # 获取当前东八区时间
        now_utc8 = datetime.now(UTC8)
        current_time_str = now_utc8.strftime('%Y年%m月%d日 %H:%M:%S')
        weekday_names = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        weekday = weekday_names[now_utc8.weekday()]

        # 系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        elif expert_mode:
            messages.append({
                "role": "system",
                "content": (
                    f"当前时间：{current_time_str} {weekday}（北京时间）\n\n"
                    "你是一个专业的信息分析助手。请提供详细、深入、专业的分析和见解。"
                    "回复应该结构清晰，包含具体的数据、来源引用和专业建议。"
                    "直接使用markdown格式输出内容，不要用代码块（如```html或```markdown）包裹整个回复。"
                )
            })
        else:
            messages.append({
                "role": "system",
                "content": (
                    f"当前时间：{current_time_str} {weekday}（北京时间）\n\n"
                    "你是一个智能助手，帮助用户获取和整理信息。"
                    "请提供简洁、准确、有用的回复。"
                    "直接使用markdown格式输出内容，不要用代码块（如```html或```markdown）包裹整个回复。"
                )
            })

        # 用户提示词
        messages.append({"role": "user", "content": prompt})

        # 调用API
        try:
            # 兼容不同的base_url格式
            # 如果以/结尾，直接拼接 chat/completions
            # 否则拼接 /v1/chat/completions
            if self.base_url.endswith("/"):
                url = f"{self.base_url}chat/completions"
            else:
                url = f"{self.base_url}/v1/chat/completions"

            print(f"[AI Service] 调用API: {url}")
            print(f"[AI Service] 模型: {self.model}")

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                    },
                )

                if response.status_code != 200:
                    error_text = response.text
                    print(f"[AI Service] API调用失败: {response.status_code} - {error_text}")
                    return f"AI服务调用失败 (HTTP {response.status_code}): {error_text[:200]}"

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return content

        except httpx.TimeoutException:
            print("[AI Service] API调用超时")
            return "AI服务调用超时，请稍后重试"
        except Exception as e:
            print(f"[AI Service] API调用异常: {e}")
            return f"AI服务调用异常: {str(e)}"

    def _generate_mock_response(self, prompt: str, expert_mode: bool) -> str:
        """生成模拟响应（未配置API时使用）"""
        mode_text = "专家模式" if expert_mode else "普通模式"
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return f"""
## 任务执行结果 ({mode_text})

**执行时间**: {current_time}

**任务指令**: {prompt[:200]}{'...' if len(prompt) > 200 else ''}

---

### ⚠️ 提示

当前未配置AI服务API密钥。请在 `.env` 文件中配置以下参数：

```
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

配置完成后，系统将自动调用AI服务执行您的任务指令。

---

**支持的API类型**: OpenAI兼容格式（如OpenAI、Azure OpenAI、本地LLM等）
"""


# 全局AI服务实例
ai_service = AIService()
