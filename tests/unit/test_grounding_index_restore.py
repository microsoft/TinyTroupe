import pytest
from llama_index.core import Document, Settings
from llama_index.core.embeddings import MockEmbedding

from tinytroupe.agent.grounding import BaseSemanticGroundingConnector


class RecordingEmbedding(MockEmbedding):
    text_calls: int = 0

    def _get_text_embedding(self, text: str) -> list[float]:
        self.text_calls += 1
        return super()._get_text_embedding(text)


@pytest.mark.parametrize("persisted_index", [True, False])
def test_grounding_restore_only_embeds_when_index_is_missing(
    monkeypatch, persisted_index
):
    embedding = RecordingEmbedding(embed_dim=8)
    monkeypatch.setattr(Settings, "_embed_model", embedding)
    connector = BaseSemanticGroundingConnector()
    text = "The delivery policy requires orders of at least ten packs."
    connector.add_document(
        Document(text=text, metadata={"semantic_memory_id": "delivery-policy"})
    )
    assert embedding.text_calls > 0
    original_calls = embedding.text_calls
    original_index_id = connector.index.index_id
    payload = connector.to_json()
    if not persisted_index:
        payload["index"] = None

    restored = BaseSemanticGroundingConnector.from_json(payload)

    assert embedding.text_calls == original_calls * (1 if persisted_index else 2)
    if persisted_index:
        assert restored.index.index_id == original_index_id
    assert restored.list_sources() == ["delivery-policy"]
    assert text in restored.retrieve_by_name("delivery-policy")[0]
    nodes = restored.index.as_retriever(similarity_top_k=1).retrieve("delivery policy")
    assert nodes[0].text == text
