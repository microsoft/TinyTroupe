import types
import pytest
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')


def _install_llama_index_stub():
    if 'llama_index' in sys.modules:
        return

    llama_index = types.ModuleType('llama_index')
    embeddings = types.ModuleType('llama_index.embeddings')
    openai_mod = types.ModuleType('llama_index.embeddings.openai')
    core_mod = types.ModuleType('llama_index.core')
    storage_context_mod = types.ModuleType('llama_index.core.storage')
    vector_stores_mod = types.ModuleType('llama_index.core.vector_stores')
    readers_mod = types.ModuleType('llama_index.readers')
    readers_web_mod = types.ModuleType('llama_index.readers.web')

    class _OpenAIEmbedding:
        def __init__(self, *args, **kwargs):
            pass

    openai_mod.OpenAIEmbedding = _OpenAIEmbedding

    class _Settings:
        def __init__(self, *args, **kwargs):
            pass

    class _Document:
        def __init__(self, *args, **kwargs):
            pass

    class _VectorStoreIndex:
        def __init__(self, *args, **kwargs):
            pass

    class _SimpleDirectoryReader:
        def __init__(self, *args, **kwargs):
            pass

        def load_data(self):
            return []

    class _SimpleWebPageReader:
        def __init__(self, *args, **kwargs):
            pass

        def load_data(self):
            return []

    embeddings.openai = openai_mod
    core_mod.Settings = _Settings
    core_mod.Document = _Document
    core_mod.VectorStoreIndex = _VectorStoreIndex
    core_mod.SimpleDirectoryReader = _SimpleDirectoryReader
    core_mod.Document = _Document
    core_mod.load_index_from_storage = lambda *args, **kwargs: _VectorStoreIndex()
    core_mod.StorageContext = object
    storage_context_mod.StorageContext = object
    vector_stores_mod.SimpleVectorStore = object
    readers_web_mod.SimpleWebPageReader = _SimpleWebPageReader

    llama_index.embeddings = embeddings
    llama_index.core = core_mod
    llama_index.readers = readers_mod
    readers_mod.web = readers_web_mod

    sys.modules['llama_index'] = llama_index
    sys.modules['llama_index.embeddings'] = embeddings
    sys.modules['llama_index.embeddings.openai'] = openai_mod
    sys.modules['llama_index.core'] = core_mod
    sys.modules['llama_index.core.storage'] = storage_context_mod
    sys.modules['llama_index.core.vector_stores'] = vector_stores_mod
    sys.modules['llama_index.readers'] = readers_mod
    sys.modules['llama_index.readers.web'] = readers_web_mod


_install_llama_index_stub()


def _install_pandas_stub():
    if 'pandas' in sys.modules:
        return

    pandas_mod = types.ModuleType('pandas')

    class _DataFrame:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def to_csv(self, *args, **kwargs):
            return ""

    pandas_mod.DataFrame = _DataFrame
    pandas_mod.Series = _DataFrame

    def _read_csv(*args, **kwargs):
        return _DataFrame()

    pandas_mod.read_csv = _read_csv

    sys.modules['pandas'] = pandas_mod


_install_pandas_stub()


def _install_pypandoc_stub():
    if 'pypandoc' in sys.modules:
        return

    pypandoc_mod = types.ModuleType('pypandoc')

    def _convert_text(*args, **kwargs):
        return ""

    pypandoc_mod.convert_text = _convert_text

    sys.modules['pypandoc'] = pypandoc_mod


_install_pypandoc_stub()


def _install_markdown_stub():
    if 'markdown' in sys.modules:
        return

    markdown_mod = types.ModuleType('markdown')

    def _markdown(text, *args, **kwargs):
        return text

    markdown_mod.markdown = _markdown

    sys.modules['markdown'] = markdown_mod


_install_markdown_stub()


def _install_tiktoken_stub():
    if 'tiktoken' in sys.modules:
        return

    tiktoken_mod = types.ModuleType('tiktoken')

    class _Encoding:
        def encode(self, text):
            return text.split()

        def decode(self, tokens):
            return " ".join(tokens)

    def _get_encoding(*args, **kwargs):
        return _Encoding()

    tiktoken_mod.get_encoding = _get_encoding

    sys.modules['tiktoken'] = tiktoken_mod


_install_tiktoken_stub()

from tinytroupe.extraction.results_extractor import ResultsExtractor, ExtractionRefusedException
from tinytroupe.extraction.normalizer import Normalizer, NormalizationRefusedException


def _make_structured_message(parsed=None, content=None, refusal=None):
    message = {}
    if parsed is not None:
        message["parsed"] = parsed
    if content is not None:
        message["content"] = content
    if refusal is not None:
        message["refusal"] = refusal
    return message


@patch('tinytroupe.openai_utils.client')
def test_results_extractor_agent_structured_parsed(mock_client):
    client_instance = Mock()
    mock_client.return_value = client_instance
    client_instance.send_message.return_value = _make_structured_message(parsed={"foo": "bar"})

    extractor = ResultsExtractor()
    agent = Mock()
    agent.name = "Agent"
    agent.pretty_current_interactions.return_value = "history"

    message = extractor.extract_results_from_agent(agent)

    assert message == {"foo": "bar"}


@patch('tinytroupe.openai_utils.client')
def test_results_extractor_agent_structured_json(mock_client):
    client_instance = Mock()
    mock_client.return_value = client_instance
    client_instance.send_message.return_value = _make_structured_message(content='{"foo": "bar"}')

    extractor = ResultsExtractor()
    agent = Mock()
    agent.name = "Agent"
    agent.pretty_current_interactions.return_value = "history"

    message = extractor.extract_results_from_agent(agent)

    assert message == {"foo": "bar"}


@patch('tinytroupe.openai_utils.client')
def test_results_extractor_agent_refusal(mock_client):
    client_instance = Mock()
    mock_client.return_value = client_instance
    client_instance.send_message.return_value = _make_structured_message(refusal={"reason": "violated"})

    extractor = ResultsExtractor()

    agent = Mock()
    agent.name = "Agent"
    agent.pretty_current_interactions.return_value = "history"

    with pytest.raises(ExtractionRefusedException):
        extractor.extract_results_from_agent(agent)


@patch('tinytroupe.openai_utils.client')
def test_results_extractor_world_fields_schema(mock_client):
    client_instance = Mock()
    mock_client.return_value = client_instance
    parsed_payload = {"field_a": "value", "field_b": None}
    client_instance.send_message.return_value = _make_structured_message(parsed=parsed_payload)

    extractor = ResultsExtractor()
    world = Mock()
    world.name = "World"
    world.pretty_current_interactions.return_value = "history"
    result = extractor.extract_results_from_world(world, fields=["field_a", "field_b"])

    assert result == parsed_payload


@patch('tinytroupe.openai_utils.client')
def test_normalizer_initialization_structured(mock_client):
    client_instance = Mock()
    mock_client.return_value = client_instance
    client_instance.send_message.return_value = _make_structured_message(parsed=["cat", "dog"])

    normalizer = Normalizer(["tabby", "hound"], n=2)

    assert normalizer.normalized_elements == ["cat", "dog"]


@patch('tinytroupe.openai_utils.client')
def test_normalizer_mapping_structured(mock_client):
    client_instance = Mock()
    mock_client.return_value = client_instance
    client_instance.send_message.side_effect = [
        _make_structured_message(parsed=["fruit", "vehicle"]),
        _make_structured_message(parsed=["fruit"]),
    ]

    normalizer = Normalizer(["apple", "car"], n=2)
    result = normalizer.normalize(["banana"])

    assert result == ["fruit"]


@patch('tinytroupe.openai_utils.client')
def test_normalizer_refusal(mock_client):
    client_instance = Mock()
    mock_client.return_value = client_instance
    client_instance.send_message.return_value = _make_structured_message(refusal={"reason": "policy"})

    with pytest.raises(NormalizationRefusedException):
        Normalizer(["apple"], n=1)


