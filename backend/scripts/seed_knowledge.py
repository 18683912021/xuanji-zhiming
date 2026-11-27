import argparse
import asyncio

from sqlalchemy.dialects.postgresql import insert

from app.agent.knowledge import embed, seed_entries
from app.agent.models import KnowledgeChunk
from app.agent.workflow import make_client
from app.core.config import get_settings
from app.core.db import create_database


async def seed(with_embeddings: bool) -> None:
    settings = get_settings()
    entries = seed_entries()
    if with_embeddings:
        client = make_client(settings)
        if client is None or not settings.ai_embedding_model:
            raise SystemExit("请先配置 AI_API_KEY 和 AI_EMBEDDING_MODEL。")
        async with client:
            vectors = await embed(
                client,
                settings.ai_embedding_model,
                [f"{value['title']}：{value['text']}" for value in entries],
            )
        for entry, vector in zip(entries, vectors, strict=True):
            entry.update(embedding=vector, embedding_model=settings.ai_embedding_model)

    engine, sessions = create_database(settings)
    try:
        async with sessions() as db:
            for entry in entries:
                statement = insert(KnowledgeChunk).values(**entry)
                if with_embeddings:
                    statement = statement.on_conflict_do_update(
                        index_elements=[KnowledgeChunk.id],
                        set_={key: value for key, value in entry.items() if key != "id"},
                    )
                else:
                    statement = statement.on_conflict_do_nothing(index_elements=[KnowledgeChunk.id])
                await db.execute(statement)
            await db.commit()
    finally:
        await engine.dispose()
    print(f"已导入 {len(entries)} 条知识。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--embed", action="store_true")
    asyncio.run(seed(parser.parse_args().embed))
