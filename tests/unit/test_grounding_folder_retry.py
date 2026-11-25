import pytest
from llama_index.core import Settings
from llama_index.core.embeddings import MockEmbedding

from tinytroupe.agent.grounding import LocalFilesGroundingConnector


@pytest.mark.parametrize("existing_empty_directory", [False, True])
def test_failed_folder_read_can_be_retried(
    monkeypatch, tmp_path, existing_empty_directory
):
    monkeypatch.setattr(Settings, "_embed_model", MockEmbedding(embed_dim=8))
    folder = tmp_path / "documents"
    if existing_empty_directory:
        folder.mkdir()
    connector = LocalFilesGroundingConnector()

    with pytest.raises((FileNotFoundError, ValueError)):
        connector.add_folder(str(folder))

    folder.mkdir(exist_ok=True)
    text = "Delivery is available on weekdays."
    (folder / "policy.txt").write_text(text, encoding="utf-8")
    connector.add_folder(str(folder))

    assert len(connector.documents) == 1
    assert connector.list_sources() == ["policy.txt"]
    assert text in connector.retrieve_by_name("policy.txt")[0]
    assert connector.index is not None
    connector.add_folder(str(folder))
    assert len(connector.documents) == 1
    assert connector.loaded_folders_paths == [str(folder)]
