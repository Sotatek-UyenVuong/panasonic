from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
from constants.LLM_models import (
    MODELS,
    ModelName,
    Provider,
)


class LLM_router:
    def __init__(self, model_name: str = "GPT_4O_MINI", temperature: float = 0.0):
        self.model_name = self._get_model_enum(model_name)
        self.temperature = temperature
        self.model_config = self._get_model_config()

    def _get_model_enum(self, model_name: str) -> ModelName:
        """Convert model name string to ModelName enum."""
        try:
            # Try direct conversion from enum name
            return ModelName[model_name]
        except KeyError:
            # If that fails, try to find by value
            try:
                return ModelName(model_name)
            except ValueError:
                # If still not found, use default
                print(f"Warning: Model {model_name} not found in ModelName enum. Using default.")
                return ModelName.GPT_4O_MINI

    def _get_model_config(self):
        """Get model configuration."""
        if self.model_name not in MODELS:
            print(f"Warning: Model {self.model_name} not found in MODELS config. Using default.")
            self.model_name = ModelName.GPT_4O_MINI
        
        return MODELS[self.model_name]

    def get_model(self):
        """Returns appropriate model client based on provider."""
        provider = self.model_config["provider"]
        api_key = self.model_config["api_key"]
        model_params = self.model_config["override_params"].copy()
        model_params["temperature"] = self.temperature

        if provider == Provider.OPENAI:
            client = OpenAI(api_key=api_key)
            return client
        elif provider == Provider.ANTHROPIC:
            client = Anthropic(api_key=api_key)
            return client
        elif provider == Provider.GOOGLE:
            genai.configure(api_key=api_key)
            return genai
        else:
            raise ValueError(f"Unsupported provider: {provider}")
