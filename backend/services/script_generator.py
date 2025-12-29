"""
Script Generator Service
Uses LangChain and an LLM to convert educational content into a structured screenplay.
Supports both OpenAI API and local Ollama.
"""
import logging
import httpx
from typing import List

from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from models.story import Screenplay, Scene
from config import Config
from services.cache_manager import CacheManager

# Conditional imports for LangChain LLMs
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_community.llms import Ollama
except ImportError:
    Ollama = None


logger = logging.getLogger(__name__)


class ScriptGenerator:
    """Generates an educational screenplay from document text."""

    def __init__(self):
        self.use_local_llm = Config.USE_LOCAL_LLM
        self.cache = CacheManager()

        self.grade_prompts = {
            1: "like they are a 6-year-old kindergartener. Use very simple words and short sentences.",
            2: "like they are a first grader. Use simple sentences and basic vocabulary.",
            3: "for a second grader, with clear, easy-to-understand language.",
            4: "for a third grader, with straightforward concepts and slightly more detail.",
            5: "for a fourth grader, with moderate complexity and vocabulary.",
            6: "for a fifth grader, introducing more detailed concepts and terminology.",
            7: "for a sixth grader, using appropriate academic language and more complex sentences.",
        }

    async def generate_screenplay(self, text: str, grade_level: int, avatar_type: str) -> Screenplay:
        """Generates an interactive screenplay from educational content."""
        cache_key_params = {"text": text, "grade_level": grade_level, "avatar_type": avatar_type}
        
        cached_screenplay_dict = await self.cache.get_json("screenplay", **cache_key_params)
        if cached_screenplay_dict:
            logger.info("Screenplay cache hit.")
            return Screenplay(**cached_screenplay_dict)
        
        logger.info("Screenplay cache miss. Generating new screenplay.")
        
        parser = PydanticOutputParser(pydantic_object=Screenplay)
        prompt_template = self._create_screenplay_prompt_template(parser, grade_level, avatar_type)
        
        llm = self._get_llm(parser)
        if not llm:
             logger.warning("No LLM is configured. Returning mock screenplay.")
             return self._generate_mock_screenplay(text, grade_level, avatar_type)

        chain = prompt_template | llm | parser

        try:
            screenplay = await chain.ainvoke({"educational_content": text})
            if not screenplay or not screenplay.scenes:
                 raise ValueError("LLM returned an empty or invalid screenplay.")
            
            await self.cache.set_json("screenplay", screenplay.model_dump(), **cache_key_params)
            return screenplay
        except Exception as e:
            logger.error(f"Error generating screenplay: {e}", exc_info=True)
            return self._generate_mock_screenplay(text, grade_level, avatar_type)
    
    def _get_llm(self, parser: PydanticOutputParser):
        """Initializes and returns the appropriate LLM based on config."""
        if self.use_local_llm:
            if Ollama is None:
                logger.error("Ollama is selected but `langchain_community` is not installed.")
                return None
            
            # Ollama with JSON mode support is preferred
            return Ollama(
                base_url=Config.OLLAMA_BASE_URL,
                model=Config.OLLAMA_MODEL,
                temperature=0.7,
                # For Llama 3 and other models that support it
                format="json", 
            )

        if Config.OPENAI_API_KEY:
            if ChatOpenAI is None:
                logger.error("OpenAI is selected but `langchain_openai` is not installed.")
                return None
            # GPT-4 and newer models are good at following JSON instructions
            return ChatOpenAI(
                model_name=Config.OPENAI_MODEL,
                temperature=0.7,
                openai_api_key=Config.OPENAI_API_KEY,
                model_kwargs={"response_format": {"type": "json_object"}}
            )
        
        return None


    def _create_screenplay_prompt_template(self, parser: PydanticOutputParser, grade_level: int, avatar_type: str) -> ChatPromptTemplate:
        """Creates the LangChain prompt template for screenplay generation."""
        grade_instruction = self.grade_prompts.get(grade_level, "for an elementary school student.")
        
        prompt = f"""
You are an expert educational content creator for children's animated storybooks. Your task is to transform educational text into an engaging screenplay.

**Character/Narrator:** The story will be told by a friendly {avatar_type}.
**Target Audience:** Explain the content {grade_instruction}.

**Instructions:**
1.  Read the educational content provided.
2.  Break it down into exactly 5 engaging scenes.
3.  For each scene, provide:
    - `scene_number`: A unique integer for the scene order.
    - `visual_description`: A brief, vivid description of what is shown on screen.
    - `narration`: The {avatar_type}'s dialogue, which should be conversational and educational.
    - `learning_point`: A single, concise key takeaway for the scene.
4.  Make the story interactive. Have the {avatar_type} ask questions to engage the viewer.

**Educational Content:**
{{educational_content}}

**Output Format:**
{{format_instructions}}
"""
        return ChatPromptTemplate.from_messages([
            ("system", prompt),
        ]).partial(format_instructions=parser.get_format_instructions())


    def _generate_mock_screenplay(self, text: str, grade_level: int, avatar_type: str) -> Screenplay:
        """Generates a mock screenplay for testing or fallback."""
        logger.info("Generating mock screenplay.")
        topic = text[:50] + "..." if len(text) > 50 else text
        scenes = [
            Scene(scene_number=1, visual_description=f"A friendly {avatar_type} waves hello.", narration=f"Hi there! I'm a {avatar_type} and we're going to learn about {topic}", learning_point="Introduction"),
            Scene(scene_number=2, visual_description="The scene shows a colorful diagram.", narration="First, let's look at the main idea.", learning_point="Main Concept"),
            Scene(scene_number=3, visual_description="An animation plays, showing how it works.", narration="Wow, look at that! Isn't that cool?", learning_point="Demonstration"),
            Scene(scene_number=4, visual_description=f"The {avatar_type} asks a question.", narration="What do you think happens next?", learning_point="Engagement Question"),
            Scene(scene_number=5, visual_description=f"The {avatar_type} gives a thumbs-up.", narration="You're doing great! We learned so much today.", learning_point="Conclusion")
        ]
        return Screenplay(scenes=scenes)