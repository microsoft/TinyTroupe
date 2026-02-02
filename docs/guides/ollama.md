# Ollama Support

TinyTroupe now has experimental Ollama support. Yes, even more experimental than the whole experimental project itself! Could be interesting to try with specialized models, besides any other privacy, security or cost considerations. Have fun experimenting!

>[!NOTE]
> Please note that TinyTroupe is developed primarily following OpenAI models, simply for convinience (i.e., we need to choose a default model family, and OpenAI is the most natural for us). Therefore, it might not work as expected if powered by other models. Furtheremore, advanced API capabilities might be occasionally needed, and those might or might not be supported by the Ollama interface. **So please use Ollama support with caution and only when really needd.**

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
