"""Ollama embedding model for LlamaIndex compatibility.

Uses Ollama's /api/embed endpoint; works with nomic-embed-text, mxbai-embed-large, etc.
No OpenAI API key required when using api_type=ollama.
"""

import asyncio
import logging
from typing import List

import requests

from llama_index.core.base.embeddings.base import BaseEmbedding

logger = logging.getLogger("tinytroupe")


class OllamaEmbedding(BaseEmbedding):
    """Embedding model that calls Ollama's /api/embed endpoint."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11444/v1",
        model_name: str = "nomic-embed-text",
        embed_batch_size: int = 10,
        **kwargs,
    ):
        super().__init__(
            model_name=model_name,
            embed_batch_size=embed_batch_size,
            **kwargs,
        )
        # /api/embed is at root, not under /v1
        self._base_url = base_url.rstrip("/").replace("/v1", "")
        self._session = requests.Session()

    def _call_embed(self, inputs: List[str]) -> List[List[float]]:
        url = f"{self._base_url}/api/embed"
        payload = {"model": self.model_name, "input": inputs if len(inputs) > 1 else inputs[0]}
        try:
            resp = self._session.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            embeddings = data.get("embeddings")
            if embeddings is None:
                raise ValueError("Ollama embed response missing 'embeddings'")
            # Single input returns one embedding, batch returns list
            if not isinstance(embeddings, list):
                embeddings = [embeddings]
            return embeddings
        except requests.RequestException as e:
            logger.error("Ollama embed request failed: %s", e)
            raise

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._call_embed([query])[0]

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return await asyncio.to_thread(self._get_query_embedding, query)

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._call_embed([text])[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return self._call_embed(texts)
