"""
Script Generator Service
Uses LangChain and LLM to convert educational content into screenplay format
"""

import os
from typing import List, Dict
from dataclasses import dataclass

try:
    from langchain.chat_models import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.output_parsers import PydanticOutputParser
except ImportError:
    ChatOpenAI = None
    ChatPromptTemplate = None
    PydanticOutputParser = None

from models.story import Screenplay, Scene


class ScriptGenerator:
    """Generates educational screenplay from document text"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Grade-appropriate language mapping
        self.grade_prompts = {
            1: "Explain this like talking to a 6-year-old kindergartener. Use very simple words.",
            2: "Explain this for a first grader using simple sentences and basic vocabulary.",
            3: "Explain this for a second grader with clear, easy-to-understand language.",
            4: "Explain this for a third grader with straightforward concepts.",
            5: "Explain this for a fourth grader with moderate complexity.",
            6: "Explain this for a fifth grader introducing more detailed concepts.",
            7: "Explain this for a sixth grader with appropriate academic language.",
        }
    
    async def generate_screenplay(
        self,
        text: str,
        grade_level: int,
        avatar_type: str
    ) -> Screenplay:
        """
        Generate interactive screenplay from educational content
        
        Args:
            text: Extracted document text
            grade_level: Target grade (1-7)
            avatar_type: Character to use as narrator
        
        Returns:
            Screenplay object with scenes
        """
        if not self.api_key:
            # Return mock screenplay for testing without API key
            return self._generate_mock_screenplay(text, grade_level, avatar_type)
        
        # Get grade-appropriate language instruction
        grade_instruction = self.grade_prompts.get(
            grade_level,
            "Explain this for an elementary school student."
        )
        
        # Create the prompt
        prompt = self._create_screenplay_prompt(
            text=text,
            grade_instruction=grade_instruction,
            avatar_type=avatar_type
        )
        
        try:
            if ChatOpenAI is not None:
                # Use LangChain with OpenAI
                llm = ChatOpenAI(
                    model="gpt-4",
                    temperature=0.7,
                    openai_api_key=self.api_key
                )
                
                response = await llm.apredict(prompt)
                return self._parse_screenplay(response)
            else:
                # Fallback to mock if LangChain not installed
                return self._generate_mock_screenplay(text, grade_level, avatar_type)
        
        except Exception as e:
            print(f"Error generating screenplay: {e}")
            return self._generate_mock_screenplay(text, grade_level, avatar_type)
    
    def _create_screenplay_prompt(
        self,
        text: str,
        grade_instruction: str,
        avatar_type: str
    ) -> str:
        """Create the LLM prompt for screenplay generation"""
        
        return f"""You are an expert educational content creator and scriptwriter for children.

Your task is to transform the following educational content into an engaging, interactive screenplay 
for an animated storybook experience.

EDUCATIONAL CONTENT:
{text}

TARGET AUDIENCE:
{grade_instruction}

CHARACTER/NARRATOR:
Use a {avatar_type} as the main character who will guide the learning experience.

INSTRUCTIONS:
1. Break the content into 5-8 distinct scenes
2. Each scene should have:
   - A clear visual description (what the viewer sees)
   - Dialogue/narration from the {avatar_type} character
   - One key learning point
3. Make it conversational and engaging
4. Use storytelling techniques (suspense, questions, surprises)
5. Include interactive moments where the {avatar_type} asks questions or encourages thinking
6. Keep language appropriate for the target age group

FORMAT your response as follows:

SCENE 1:
VISUAL: [Describe what appears on screen]
NARRATION: [What the character says]
LEARNING POINT: [Key concept]

SCENE 2:
...

Generate the complete screenplay now:"""
    
    def _parse_screenplay(self, llm_response: str) -> Screenplay:
        """Parse LLM response into Screenplay object"""
        scenes = []
        current_scene = {}
        
        lines = llm_response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('SCENE'):
                if current_scene:
                    scenes.append(Scene(**current_scene))
                current_scene = {
                    'scene_number': len(scenes) + 1,
                    'visual_description': '',
                    'narration': '',
                    'learning_point': ''
                }
            elif line.startswith('VISUAL:'):
                current_scene['visual_description'] = line.replace('VISUAL:', '').strip()
            elif line.startswith('NARRATION:'):
                current_scene['narration'] = line.replace('NARRATION:', '').strip()
            elif line.startswith('LEARNING POINT:'):
                current_scene['learning_point'] = line.replace('LEARNING POINT:', '').strip()
        
        # Add the last scene
        if current_scene and current_scene.get('narration'):
            scenes.append(Scene(**current_scene))
        
        return Screenplay(scenes=scenes)
    
    def _generate_mock_screenplay(
        self,
        text: str,
        grade_level: int,
        avatar_type: str
    ) -> Screenplay:
        """Generate a mock screenplay for testing purposes"""
        
        # Extract first 200 characters as topic
        topic = text[:200] if len(text) > 200 else text
        
        scenes = [
            Scene(
                scene_number=1,
                visual_description=f"A friendly {avatar_type} appears with a welcoming smile",
                narration=f"Hello! I'm your {avatar_type} friend, and today we're going to learn something amazing!",
                learning_point="Introduction to the topic"
            ),
            Scene(
                scene_number=2,
                visual_description=f"The {avatar_type} points to an illustrated diagram",
                narration=f"Let me show you something interesting about {topic[:50]}...",
                learning_point="Main concept introduction"
            ),
            Scene(
                scene_number=3,
                visual_description=f"The {avatar_type} demonstrates with animated examples",
                narration="Watch how this works! It's easier than you think.",
                learning_point="Practical demonstration"
            ),
            Scene(
                scene_number=4,
                visual_description=f"The {avatar_type} poses a question with a curious expression",
                narration="Now, can you guess what happens next? Think about it!",
                learning_point="Interactive engagement"
            ),
            Scene(
                scene_number=5,
                visual_description=f"The {avatar_type} celebrates with a happy animation",
                narration="You did it! You learned something new today. Great job!",
                learning_point="Conclusion and encouragement"
            )
        ]
        
        return Screenplay(scenes=scenes)
