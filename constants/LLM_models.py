import os
from enum import Enum

from dotenv import load_dotenv


load_dotenv()
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
PORTKEY_API_KEY = os.environ["PORTKEY_API_KEY"]
PORTKEY_GATEWAY_URL = os.environ["PORTKEY_GATEWAY_URL"]


class Provider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class ModelName(Enum):
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    GPT_4 = "gpt-4"
    CLAUDE_3_7_SONNET = "claude-3-7-sonnet-20250219"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-20241022"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    GEMINI_2_5_PRO_EXP_03_25 = "gemini-2.5-pro-exp-03-25"
    GEMINI_2_0_PRO_EXP_02_05 = "gemini-2.0-pro-exp-02-05"
    GEMINI_2_0_FLASH_LITE_001 = "gemini-2.0-flash-lite-001"
    GEMINI_2_0_FLASH_001 = "gemini-2.0-flash-001"
    GEMINI_FLASH_1_5 = "gemini-1.5-flash"
    GEMINI_PRO_1_5 = "gemini-1.5-pro"
    GPT_O1 = "o1"#Thinking
    GPT_O3_MINI_2025_01_31 = "o3-mini"#Thinking


# Define all available models and their providers
MODELS = {
    ModelName.GPT_3_5: {
        "provider": Provider.OPENAI,
        "api_key": OPENAI_KEY,
        "override_params": {"model": ModelName.GPT_3_5.value, "max_tokens": 4096},
    },
    ModelName.GPT_4O_MINI: {
        "provider": Provider.OPENAI,
        "api_key": OPENAI_KEY,
        "override_params": {"model": ModelName.GPT_4O_MINI.value, "max_tokens": 4096},
    },
    ModelName.GPT_4O: {
        "provider": Provider.OPENAI,
        "api_key": OPENAI_KEY,
        "override_params": {"model": ModelName.GPT_4O.value, "max_tokens": 4096},
    },
    ModelName.GPT_4: {
        "provider": Provider.OPENAI,
        "api_key": OPENAI_KEY,
        "override_params": {"model": ModelName.GPT_4.value, "max_tokens": 4096},
    },
    ModelName.CLAUDE_3_7_SONNET: {
        "provider": Provider.ANTHROPIC,
        "api_key": ANTHROPIC_API_KEY,
        "override_params": {
            "model": ModelName.CLAUDE_3_7_SONNET.value,
            "max_tokens": 4096,
        },
    },
    ModelName.CLAUDE_3_5_HAIKU: {
        "provider": Provider.ANTHROPIC,
        "api_key": ANTHROPIC_API_KEY,
        "override_params": {
            "model": ModelName.CLAUDE_3_5_HAIKU.value,
            "max_tokens": 4096,
        },
    },
    ModelName.CLAUDE_3_5_SONNET: {
        "provider": Provider.ANTHROPIC,
        "api_key": ANTHROPIC_API_KEY,
        "override_params": {
            "model": ModelName.CLAUDE_3_5_SONNET.value,
            "max_tokens": 4096,
        },
    },
    ModelName.CLAUDE_3_HAIKU: {
        "provider": Provider.ANTHROPIC,
        "api_key": ANTHROPIC_API_KEY,
        "override_params": {
            "model": ModelName.CLAUDE_3_HAIKU.value,
            "max_tokens": 4096,
        },
    },
    ModelName.CLAUDE_3_SONNET: {
        "provider": Provider.ANTHROPIC,
        "api_key": ANTHROPIC_API_KEY,
        "override_params": {
            "model": ModelName.CLAUDE_3_SONNET.value,
            "max_tokens": 4096,
        },
    },
    ModelName.CLAUDE_3_OPUS: {
        "provider": Provider.ANTHROPIC,
        "api_key": ANTHROPIC_API_KEY,
        "override_params": {
            "model": ModelName.CLAUDE_3_OPUS.value,
            "max_tokens": 4096,
        },
    },
    ModelName.GEMINI_2_5_PRO_EXP_03_25: {
        "provider": Provider.GOOGLE,
        "api_key": GEMINI_API_KEY,
        "override_params": {
            "model": ModelName.GEMINI_2_5_PRO_EXP_03_25.value,
            "max_tokens": 4096,
        },
    },
    ModelName.GEMINI_2_0_PRO_EXP_02_05: {
        "provider": Provider.GOOGLE,
        "api_key": GEMINI_API_KEY,
        "override_params": {
            "model": ModelName.GEMINI_2_0_PRO_EXP_02_05.value,
            "max_tokens": 4096,
        },
    },
    ModelName.GEMINI_2_0_FLASH_LITE_001: {
        "provider": Provider.GOOGLE,
        "api_key": GEMINI_API_KEY,
        "override_params": {
            "model": ModelName.GEMINI_2_0_FLASH_LITE_001.value,
            "max_tokens": 4096,
        },
    },
    ModelName.GEMINI_2_0_FLASH_001: {
        "provider": Provider.GOOGLE,
        "api_key": GEMINI_API_KEY,
        "override_params": {
            "model": ModelName.GEMINI_2_0_FLASH_001.value,
            "max_tokens": 4096,
        },
    },
    ModelName.GEMINI_FLASH_1_5: {
        "provider": Provider.GOOGLE,
        "api_key": GEMINI_API_KEY,
        "override_params": {
            "model": ModelName.GEMINI_FLASH_1_5.value,
            "max_tokens": 4096,
        },
    },
    ModelName.GEMINI_PRO_1_5: {
        "provider": Provider.GOOGLE,
        "api_key": GEMINI_API_KEY,
        "override_params": {
            "model": ModelName.GEMINI_PRO_1_5.value,
            "max_tokens": 4096,
        },
    },
    ModelName.GPT_O1: {
        "provider": Provider.OPENAI,
        "api_key": OPENAI_KEY,
        "override_params": {"model": ModelName.GPT_O1.value},
    },
    ModelName.GPT_O3_MINI_2025_01_31: {
        "provider": Provider.OPENAI,
        "api_key": OPENAI_KEY,
        "override_params": {"model": ModelName.GPT_O3_MINI_2025_01_31.value},
    }
    
}