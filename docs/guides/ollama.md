# Ollama Support

TinyTroupe now has experimental Ollama support. Yes, even more experimental than the whole experimental project itself! Could be interesting to try with specialized models, besides any other privacy, security or cost considerations. Have fun experimenting!

>[!NOTE]
> Please note that TinyTroupe is developed primarily following OpenAI models, simply for convinience (i.e., we need to choose a default model family, and OpenAI is the most natural for us). Therefore, it might not work as expected if powered by other models. Furtheremore, advanced API capabilities might be occasionally needed, and those might or might not be supported by the Ollama interface. **So please use Ollama support with caution and only when really needd.**

## TinyTroupe-Managed Ollama (Dual Agents)

TinyTroupe uses dedicated ports **11444** and **11445** (not the default 11434) and can spawn its own Ollama instances. For tests:

```shell
TINYTROUPE_CONFIG=tests/config_ollama.ini pytest tests/unit/ -v
```

Ollama is auto-started on 11444 and 11445 before tests and stopped after. Requires `ollama` in PATH.

Programmatic use:
```python
from tinytroupe.ollama_runner import OllamaInstances

with OllamaInstances(ports=[11444, 11445]):
    # run your agents
    world.run(2, parallelize=True)
```

Manual start: `./scripts/start_tinytroupe_ollama.sh`

## Multiple Ollama Hosts (Host Pool)

When running multiple Ollama instances on different ports, spread parallel agent requests for better throughput. In `config.ini`:

```ini
[OpenAI]
OLLAMA_BASE_URLS=http://127.0.0.1:11444/v1,http://127.0.0.1:11445/v1
```

The client uses round-robin: each LLM request selects the next URL. With `parallelize=True`, concurrent agent requests go to different hosts.

## Usage Instructions
To get it running, execute the following in your terminal:
```shell
ollama pull gemma3:1b
ollama serve
```

Change your config.ini file to reflect
```
[OpenAI]    
API_TYPE=ollama
MODEL=gemma3:1b
MAX_TOKENS=8192 
```

Set the API key to 
```shell
export OPENAI_API_KEY="ollama"
```

## Acknowledgments
Thanks to user https://github.com/P3GLEG for sending the initial Ollama support PR.
