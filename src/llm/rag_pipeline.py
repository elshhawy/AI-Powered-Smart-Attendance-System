# src/llm/rag_pipeline.py
from groq import Groq
from src.core.config import settings
from src.llm.prompts import build_prompt


class RAGPipeline:
    """
    Handles communication with the Groq LLM API.

    RAG = Retrieval Augmented Generation:
        1. Retrieve  — pull attendance data from DB (ContextBuilder)
        2. Augment   — inject it into the system prompt (prompts.py)
        3. Generate  — send to Groq LLM and get a response (here)

    Why Groq?
        - Free tier available
        - Very fast inference (LPU hardware)
        - Supports llama3 and mixtral models
    """

    MODEL = "llama-3.3-70b-versatile"  # Fast + free + good quality

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def chat(
        self,
        user_message: str,
        context: str,
        history: list[dict] | None = None,
    ) -> str:
        """
        Send a message to the LLM and get a response.

        Args:
            user_message: what the admin typed
            context:      attendance data from ContextBuilder
            history:      previous messages in the conversation
                          format: [{"role": "user"|"assistant", "content": "..."}]

        Returns:
            The LLM's response as a string
        """
        system_prompt = build_prompt(context)

        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (last 10 messages to stay within token limits)
        if history:
            messages.extend(history[-10:])

        # Add the new user message
        messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=messages,
            temperature=0.3,   # Low temperature = more factual, less creative
            max_tokens=1024,
        )

        return response.choices[0].message.content