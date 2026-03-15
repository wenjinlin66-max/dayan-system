from __future__ import annotations

import httpx

from app.domain.memory.service import MemoryService
from app.domain.memory.service import RuntimeMemoryBundle
from app.integrations.llm.client import LLMClient
from app.runtime.models import NodeExecutionResult, RuntimeNode, RuntimeState


class DialogNodeHandler:
    llm_client: LLMClient

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient.from_settings()

    async def execute(self, node: RuntimeNode, state: RuntimeState, next_nodes: list[str]) -> NodeExecutionResult:
        memory = MemoryService.bind_runtime(state)
        latest_message = str(state.input_payload.get("message") or state.context.get("dialog_message") or "")
        _ = state.context.setdefault("dialog_message", latest_message)
        prompt_hint = str(node.config.get("promptHint") or "")
        intent_tag = str(node.config.get("intentTag") or "")
        response_style = str(node.config.get("responseStyle") or "guide")
        memory_profile = str(node.config.get("memoryProfile") or "standard")
        reply_source = "fallback"
        fallback_reason: str | None = None

        reply = self._build_fallback_reply(latest_message, prompt_hint=prompt_hint, response_style=response_style)
        if latest_message and self.llm_client.enabled:
            messages = self._build_messages(
                latest_message,
                prompt_hint=prompt_hint,
                intent_tag=intent_tag,
                response_style=response_style,
                memory_profile=memory_profile,
                memory=memory,
            )
            try:
                reply = await self.llm_client.chat(messages=messages)
                reply_source = "llm"
            except (httpx.HTTPError, RuntimeError):
                reply = self._build_fallback_reply(latest_message, prompt_hint=prompt_hint, response_style=response_style)
                fallback_reason = "llm_call_failed"
        elif not self.llm_client.enabled:
            fallback_reason = "llm_not_configured"

        state.dialog_outputs[node.id] = {
            "message": latest_message,
            "reply": reply,
            "reply_source": reply_source,
            "intent_tag": intent_tag,
            "response_style": response_style,
            "memory_profile": memory_profile,
            "llm_enabled": self.llm_client.enabled,
            "fallback_reason": fallback_reason,
        }
        state.context["dialog_reply"] = reply
        memory.context.set_context("latest_dialog_node", node.id)
        memory.history.write_history(
            {
                "memory_type": "execution_history",
                "agent_type": "dialog_agent",
                "workflow_id": state.workflow_id,
                "execution_id": state.execution_id,
                "summary": f"{node.name} 处理了一次对话输入并生成回复",
                "payload": {"message": latest_message, "reply": reply, "intent_tag": intent_tag},
            }
        )
        return NodeExecutionResult(next_node_id=next_nodes[0] if next_nodes else None)

    @staticmethod
    def _build_messages(
        latest_message: str,
        *,
        prompt_hint: str,
        intent_tag: str,
        response_style: str,
        memory_profile: str,
        memory: RuntimeMemoryBundle,
    ) -> list[dict[str, str]]:
        system_prompt = (
            "你是大衍系统工作流中的对话型智能体节点。"
            "请基于当前输入生成一段适合继续流转的中文回复，"
            "不要编造不存在的数据，长度控制在 1-3 句。"
        )
        style_prompt = f"响应风格：{response_style}；意图标签：{intent_tag or '未设置'}；节点提示：{prompt_hint or '无'}。"
        memory_prompt = f"记忆强度：{memory_profile}。请在回复中只使用与当前问题直接相关的历史信息。"
        history_items = memory.history.search_history(latest_message)
        history_text = "\n".join(str(item.get("summary") or "") for item in history_items[-5:]) or "无"
        return [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": style_prompt},
            {"role": "system", "content": memory_prompt},
            {"role": "system", "content": f"相关历史摘要：{history_text}"},
            {"role": "user", "content": latest_message},
        ]

    @staticmethod
    def _build_fallback_reply(latest_message: str, *, prompt_hint: str, response_style: str) -> str:
        prefix = {
            "confirm": "已收到，",
            "explain": "说明如下：",
            "guide": "建议先这样处理：",
        }.get(response_style, "建议先这样处理：")
        topic = prompt_hint or latest_message or "当前请求"
        return f"{prefix}{topic}。"
