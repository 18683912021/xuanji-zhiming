import json
from dataclasses import dataclass, field
from uuid import UUID

from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelRetry, RunContext, UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.providers.openai import OpenAIProvider

from app.agent.knowledge import Evidence, retrieve
from app.agent.prompts import ROLES, SYSTEM
from app.agent.schemas import Answer, Citation, Reply, Task
from app.core.config import Settings


@dataclass
class TurnContext:
    role: str
    task: Task
    question: str
    history: list[dict]
    reference_id: UUID | None
    snapshot: dict | None
    knowledge: dict[str, Evidence] = field(default_factory=dict)
    used_sources: dict[str, Citation] = field(default_factory=dict)


def make_client(settings: Settings) -> AsyncOpenAI | None:
    if settings.ai_api_key is None or not settings.ai_api_key.get_secret_value():
        return None
    return AsyncOpenAI(
        api_key=settings.ai_api_key.get_secret_value(),
        base_url=settings.model_base_url,
        timeout=min(settings.ai_timeout_seconds, 15),
        max_retries=0,
    )


def build_agent(
    client: AsyncOpenAI, model_name: str, *, provider_name: str = "openai"
) -> Agent[TurnContext, Answer]:
    deepseek = provider_name == "deepseek"
    provider = (
        DeepSeekProvider(openai_client=client) if deepseek else OpenAIProvider(openai_client=client)
    )
    agent = Agent(
        OpenAIChatModel(model_name, provider=provider),
        deps_type=TurnContext,
        output_type=Answer,
        model_settings={"thinking": False} if deepseek else None,
        retries=1,
    )

    @agent.instructions
    def instructions(ctx: RunContext[TurnContext]) -> str:
        return SYSTEM + "\n" + ROLES[ctx.deps.role]["instruction"]

    @agent.tool
    def read_snapshot(ctx: RunContext[TurnContext]) -> dict:
        """读取会话绑定的一份体验结果，不接收外部结果 ID。"""
        deps = ctx.deps
        if deps.task != "reading" or deps.snapshot is None or deps.reference_id is None:
            return {"available": False}
        source_id = str(deps.reference_id)
        deps.used_sources[source_id] = Citation(
            id=source_id,
            title="本次体验结果",
            source="玄机知命业务计算",
            version=deps.snapshot["rules_version"],
        )
        return {"source_id": source_id, "snapshot": deps.snapshot}

    @agent.tool
    def read_reference(ctx: RunContext[TurnContext], source_id: str) -> dict:
        """读取本轮检索结果列出的一个知识条目。"""
        source = ctx.deps.knowledge.get(source_id)
        if source is None:
            raise ModelRetry("只能读取本轮检索提供的 source_id。")
        ctx.deps.used_sources[source_id] = source.citation
        return {"source_id": source_id, "text": source.text}

    @agent.output_validator
    def verify_sources(ctx: RunContext[TurnContext], output: Answer) -> Answer:
        cited = set(output.source_ids)
        if not cited.issubset(ctx.deps.used_sources):
            raise ModelRetry("引用必须来自当前轮次实际读取的工具结果。")
        if ctx.deps.task == "reading" and str(ctx.deps.reference_id) not in cited:
            raise ModelRetry("解读当次体验时必须读取并引用本次体验。")
        return output

    return agent


def ask_for_input(context: TurnContext) -> Reply | None:
    if context.task != "reading" or context.snapshot is not None:
        return None
    if context.role == "astrologer":
        return Reply(
            text="请先生成本命盘，再从盘面开启对话，或选择已有本命盘作为依据。",
            needs_input=True,
        )
    return Reply(
        text="请先完成一次抽牌或起卦，再从结果页开启或关联这次对话。",
        needs_input=True,
    )


async def run_model(app_state, context: TurnContext) -> tuple[Reply, dict]:
    context.knowledge = await retrieve(
        app_state.sessions, app_state.settings, app_state.ai_client, context.role, context.question
    )
    prompt = {
        "task": context.task,
        "history": context.history,
        "question": context.question,
        "reference_available": bool(context.snapshot),
        "knowledge_candidates": [
            {"id": item.citation.id, "title": item.citation.title}
            for item in context.knowledge.values()
        ],
    }
    result = await app_state.agent.run(
        json.dumps(prompt, ensure_ascii=False),
        deps=context,
        usage_limits=UsageLimits(request_limit=4, tool_calls_limit=4, total_tokens_limit=7000),
        model_settings={"max_tokens": 1000},
    )
    answer = result.output
    usage = result.usage
    return Reply(
        text=answer.text,
        citations=[context.used_sources[key] for key in dict.fromkeys(answer.source_ids)],
        follow_up=answer.follow_up,
    ), {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "requests": usage.requests,
    }
