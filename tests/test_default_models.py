import configparser
from pathlib import Path


def test_default_reasoning_model_is_still_served() -> None:
    config = configparser.ConfigParser()
    config.read(Path(__file__).parents[1] / "tinytroupe" / "config.ini")

    assert config["OpenAI"]["REASONING_MODEL"] == "gpt-5-mini"
