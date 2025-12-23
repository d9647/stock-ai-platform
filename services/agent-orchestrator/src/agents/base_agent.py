"""
Base agent class for all agent implementations.
Provides LLM wrapper and common utilities.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import hashlib
import json
from datetime import datetime
from uuid import uuid4

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from loguru import logger

from ..config import config


class BaseAgent(ABC):
    """
    Base class for all agents.
    Provides LLM integration and prompt hashing.
    """

    def __init__(
        self,
        agent_type: str,
        model_version: str = None,
        database_url: str = None
    ):
        self.agent_type = agent_type
        self.model_version = model_version or config.AGENT_MODEL_VERSION
        self.database_url = database_url or config.DATABASE_URL

        # Initialize LLM (temperature=0 for determinism)
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            temperature=config.LLM_TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )

        logger.info(f"Initialized {agent_type} agent (model: {config.OPENAI_MODEL})")

    @abstractmethod
    def analyze(
        self,
        ticker: str,
        as_of_date,
        feature_snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze feature snapshot and return agent output.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Date of analysis
            feature_snapshot: Full feature snapshot dict

        Returns:
            Dict with: output_id, signal, strength, reasoning, metadata
        """
        pass

    def _create_prompt_hash(self, prompt: str) -> str:
        """Create SHA-256 hash of prompt for versioning."""
        return hashlib.sha256(prompt.encode()).hexdigest()

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """
        Call LLM with system and user prompts.

        Returns:
            LLM response as string
        """
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            # Try to find the first { and last } to extract just the JSON object
            # This handles cases where LLM adds explanatory text after the JSON
            first_brace = response.find('{')
            if first_brace != -1:
                # Find matching closing brace
                brace_count = 0
                for i in range(first_brace, len(response)):
                    if response[i] == '{':
                        brace_count += 1
                    elif response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found matching closing brace
                            response = response[first_brace:i+1]
                            break

            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response}")
            raise
