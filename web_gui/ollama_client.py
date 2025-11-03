"""Ollama client for local LLM integration (llama3)."""

import requests
import json
from typing import Generator, Optional

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3"


def is_ollama_available() -> bool:
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def list_models() -> list:
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass
    return []


def generate(prompt: str, model: str = DEFAULT_MODEL, system: str = "",
             temperature: float = 0.7, max_tokens: int = 2048) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if system:
        payload["system"] = system

    resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json().get("response", "")


def generate_stream(prompt: str, model: str = DEFAULT_MODEL, system: str = "",
                    temperature: float = 0.7) -> Generator[str, None, None]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
        },
    }
    if system:
        payload["system"] = system

    with requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload,
                       stream=True, timeout=120) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done"):
                    break


def chat(messages: list, model: str = DEFAULT_MODEL,
         temperature: float = 0.7) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }
    resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json().get("message", {}).get("content", "")


def chat_stream(messages: list, model: str = DEFAULT_MODEL,
                temperature: float = 0.7) -> Generator[str, None, None]:
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": temperature,
        },
    }
    with requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload,
                       stream=True, timeout=120) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                token = data.get("message", {}).get("content", "")
                if token:
                    yield token
                if data.get("done"):
                    break


def get_chat_system_prompt(model: str = DEFAULT_MODEL) -> str:
    """Build a chat system prompt that reflects the active Ollama model."""
    model_lower = (model or DEFAULT_MODEL).lower()
    if model_lower.startswith("gemma"):
        identity = f"Gemma ({model}), a large language model by Google"
    elif model_lower.startswith("llama"):
        identity = f"Llama ({model}), a large language model by Meta"
    elif model_lower.startswith("qwen"):
        identity = f"Qwen ({model}), a large language model by Alibaba"
    elif model_lower.startswith("deepseek"):
        identity = f"DeepSeek ({model})"
    elif model_lower.startswith("mistral"):
        identity = f"Mistral ({model})"
    elif model_lower.startswith("granite"):
        identity = f"Granite ({model}), a large language model by IBM"
    else:
        identity = f"{model}, running locally via Ollama"

    return f"""You are {identity}, running locally on the user's machine via Ollama.
You are integrated into an MCP (Model Context Protocol) development dashboard.

IMPORTANT: When asked about your identity or which model you are:
- You are {model}, running locally via Ollama
- Do not claim to be a different model than {model}
- You run offline/locally - no data leaves the machine

You help with:
- OpenShift/Kubernetes operations and debugging
- Code review and development best practices
- Test case generation and QA planning
- Jira issue analysis and workflow automation
Be concise, technical, and helpful. Do not make up facts about yourself."""


# Specialized prompts for MCP tools
SYSTEM_PROMPTS = {
    "code_review": """You are an expert code reviewer specializing in Go, Python, and Kubernetes/OpenShift.
Provide line-by-line analysis focusing on:
- Security vulnerabilities
- Performance issues
- Code quality and best practices
- Potential bugs
Format your response with clear sections and severity levels (Critical, High, Medium, Low).""",

    "test_generation": """You are an expert QA engineer specializing in OpenShift and Kubernetes testing.
Generate comprehensive test cases including:
- Functional tests (positive scenarios)
- Negative tests (error handling)
- Edge cases
- Performance considerations
Format as structured test cases with steps and expected results.""",

    "cluster_debug": """You are an expert OpenShift/Kubernetes cluster administrator and debugger.
Analyze the provided cluster state and:
- Identify root causes of issues
- Suggest remediation steps
- Provide oc commands for further diagnosis
- Rate severity of each finding
Be specific and actionable in your recommendations.""",
}


def review_code(code: str, language: str = "go", model: str = DEFAULT_MODEL) -> str:
    prompt = f"Review the following {language} code:\n\n```{language}\n{code}\n```\n\nProvide a detailed line-by-line review."
    return generate(prompt, model=model, system=SYSTEM_PROMPTS["code_review"])


def generate_tests(description: str, context: str = "", model: str = DEFAULT_MODEL) -> str:
    prompt = f"Generate test cases for:\n{description}"
    if context:
        prompt += f"\n\nAdditional context:\n{context}"
    return generate(prompt, model=model, system=SYSTEM_PROMPTS["test_generation"])


def debug_cluster(state: str, model: str = DEFAULT_MODEL) -> str:
    prompt = f"Analyze and debug the following OpenShift cluster state:\n\n{state}"
    return generate(prompt, model=model, system=SYSTEM_PROMPTS["cluster_debug"])
