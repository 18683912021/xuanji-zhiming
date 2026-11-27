from dataclasses import dataclass

from openai import AsyncOpenAI, OpenAIError
from sqlalchemy import select

from app.agent.models import EMBEDDING_DIMENSIONS, KnowledgeChunk
from app.agent.prompts import ROLES
from app.agent.schemas import Citation
from app.core.config import Settings

# Original editorial knowledge with stable references for the first release.
SEED_CHUNKS = [
    (
        "tarot-positions",
        "tarot",
        "牌位与牌阵",
        "先读清牌位对问题的限定，再将同一牌阵内的线索联系起来。过去、现在、未来是观察层次，未来位置不代表已经确定的事件。",
        ["牌位", "牌阵", "过去", "现在", "未来"],
    ),
    (
        "tarot-orientation",
        "tarot",
        "正位与逆位",
        "正位和逆位可以提示同一主题的不同表达。逆位可用来观察受阻、过度或尚在发展中的环节，再结合牌位和具体问题核对。",
        ["正位", "逆位", "反向"],
    ),
    (
        "astrology-houses",
        "astrologer",
        "宫位",
        "宫位指盘面中与不同生活领域相对应的区域。第七宫常用来谈一对一的关系与合作。个人解读还需查看宫制、宫头、所在行星和宫主。",
        ["宫位", "第七宫", "合作", "宫主"],
    ),
    (
        "astrology-aspects",
        "astrologer",
        "行星与相位",
        "相位描述两颗天体在黄道经度上的角距。判断时需要实际经度、相位类型和容许度。仅有太阳星座时无法确定个人盘中的相位。",
        ["相位", "行星", "容许度", "刑", "冲", "合相"],
    ),
    (
        "divination-lines",
        "diviner",
        "本卦、动爻与变卦",
        "爻从初爻往上记录。老阴、老阳为动爻，分别变为阳、阴。所有动爻翻转后得到变卦。六爻均静时保留本卦。",
        ["本卦", "变卦", "动爻", "静卦", "六爻", "老阴", "老阳"],
    ),
    (
        "divination-verse",
        "diviner",
        "签文与问题",
        "可以从签文的具体意象出发，记录它和问题中哪项可验证的事实相关。签文为传统文化形式，解释可以随问题产生不同阅读角度。",
        ["问签", "签文", "签", "意象"],
    ),
    (
        "dream-observation",
        "dream",
        "记录梦境时的情绪",
        "可以把梦里的画面、醒来时的感觉和最近的生活线索分开写。讨论意象时，优先询问它对本人意味着什么。",
        ["梦境", "醒来", "情绪", "感受"],
    ),
    (
        "report-chart-basis",
        "report",
        "核对排盘口径",
        "读报告时可先核对盘型、时区和计算口径，分清已确定的盘面字段与输入缺失导致的空项。",
        ["报告", "四柱", "命盘", "星盘", "时辰"],
    ),
]


@dataclass(frozen=True)
class Evidence:
    citation: Citation
    text: str


async def embed(client: AsyncOpenAI, model: str, texts: list[str]) -> list[list[float]]:
    response = await client.embeddings.create(
        input=texts, model=model, dimensions=EMBEDDING_DIMENSIONS
    )
    return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]


async def retrieve(
    sessions, settings: Settings, client: AsyncOpenAI | None, role: str, query: str
) -> dict[str, Evidence]:
    vector = None
    if client is not None and settings.ai_embedding_model:
        try:
            vector = (await embed(client, settings.ai_embedding_model, [query]))[0]
        except OpenAIError:
            # A temporary embedding failure still allows retrieval by editorial aliases.
            pass

    async with sessions() as db:
        scoped = select(KnowledgeChunk).where(KnowledgeChunk.role == role)
        candidates: dict[str, KnowledgeChunk] = {}
        if vector is not None:
            distance = KnowledgeChunk.embedding.cosine_distance(vector)
            nearest = await db.scalars(
                scoped.where(
                    KnowledgeChunk.embedding_model == settings.ai_embedding_model,
                    KnowledgeChunk.embedding.is_not(None),
                    distance <= 0.55,
                )
                .order_by(distance)
                .limit(4)
            )
            candidates.update((chunk.id, chunk) for chunk in nearest)
        lexical = await db.scalars(scoped.order_by(KnowledgeChunk.id).limit(100))
        ranked = sorted(
            ((sum(len(tag) for tag in chunk.tags if tag in query), chunk) for chunk in lexical),
            key=lambda match: -match[0],
        )
        matched = {chunk.id: chunk for score, chunk in ranked if score}
        ordered = {**matched, **candidates}
    return {
        chunk.id: Evidence(
            citation=Citation(
                id=chunk.id, title=chunk.title, source=chunk.source, version=chunk.version
            ),
            text=chunk.text,
        )
        for chunk in list(ordered.values())[:4]
    }


def seed_entries() -> list[dict]:
    return [
        {
            "id": identifier,
            "role": role,
            "title": title,
            "text": text,
            "tags": tags,
            "source": "玄机知命知识条目 · " + ROLES[role]["name"],
            "version": "1.0.0",
        }
        for identifier, role, title, text, tags in SEED_CHUNKS
    ]
