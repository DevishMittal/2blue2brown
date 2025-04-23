# app/langgraph_nodes/voiceover_script_agent.py

import os
import re
import json
import tempfile
from openai import OpenAI
import numpy as np
from typing import Dict, Any, List
from dotenv import load_dotenv

class VoiceoverScriptAgent:
    """
    Agent specialized in creating educational voiceover scripts for mathematical animations.
    Instead of literal descriptions like "making circle", it generates natural, educational
    explanations that enrich the visuals with context and insights.
    """
    
    def __init__(self, nebius_api_key=None, nebius_api_url=None):
        """Initialize the VoiceoverScriptAgent with Nebius API credentials"""
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client with Nebius credentials
        self.client = OpenAI(
            api_key=nebius_api_key or os.getenv("NEBIUS_API_KEY") or os.getenv("LLM_KEY"),
            base_url=nebius_api_url or os.getenv("NEBIUS_API_URL", "https://api.studio.nebius.ai/v1/")
        )
        
    def generate_script(self, manim_code: str, topic: str = None, educational_level: str = "general") -> Dict[str, Any]:
        """
        Generate a natural educational voiceover script for a Manim animation.
        
        Args:
            manim_code: The Manim Python code of the animation
            topic: Optional topic to focus the explanation (e.g., "calculus", "gravity")
            educational_level: Target audience level (e.g., "primary", "high school", "university", "general")
            
        Returns:
            Dictionary containing the voiceover script segments mapped to animation sections
        """
        # Parse the Manim code to extract animation segments
        animation_segments = self._parse_animations(manim_code)
        
        # Create a system prompt that emphasizes educational narration
        system_prompt = self._create_system_prompt(educational_level)
        
        # Extract topic from code comments if not provided
        if not topic:
            topic = self._extract_topic_from_code(manim_code)
        
        # Generate a complete educational script
        complete_script = self._generate_complete_script(animation_segments, topic, system_prompt)
        
        # Map the script parts to specific animation segments
        mapped_script = self._map_script_to_animations(complete_script, animation_segments)
        
        return mapped_script
    
    def _create_system_prompt(self, educational_level: str) -> str:
        """Create a system prompt for the LLM based on educational level"""
        base_prompt = """You are an expert mathematics and science educator specializing in creating engaging educational voiceover scripts for animations. 
Your task is to create a natural, conversational script that explains mathematical and scientific concepts in a clear, engaging way.

Guidelines:
1. Use conversational language that feels like a teacher speaking, not reading text
2. Avoid phrases like "as you can see" or "now we're drawing" - instead explain the meaning
3. Use precise mathematical language when appropriate, but explain complex terms
4. Connect the visual elements to the underlying concepts they represent
5. Build a narrative that flows from one animation to the next
6. Each sentence should provide educational insight, not just describe what's happening visually
7. Include introductory context at the beginning and summarize insights at the end
8. Be concise - script segments should be short enough to fit the animation timing
"""
        
        # Add level-specific guidance
        if educational_level == "primary":
            base_prompt += "\nUse simple vocabulary and short sentences appropriate for young students (ages 8-11). Use analogies to everyday objects and experiences. Focus on building intuition rather than formalism."
        elif educational_level == "high school":
            base_prompt += "\nUse vocabulary appropriate for high school students (ages 14-18). Balance conceptual understanding with some formal mathematical language. Make connections to curriculum topics they might be studying."
        elif educational_level == "university":
            base_prompt += "\nUse sophisticated vocabulary and precise mathematical language appropriate for university students. Don't shy away from formalism, but ensure concepts are still clearly explained. Make connections to advanced topics and applications."
        
        return base_prompt
    
    def _parse_animations(self, manim_code: str) -> List[Dict[str, Any]]:
        """
        Parse the Manim code to extract animation segments and their details
        
        Returns:
            List of dictionaries containing animation details
        """
        segments = []
        
        # Extract the construct method
        construct_match = re.search(r'def\s+construct\s*\(\s*self\s*\):(.*?)(?:def|\Z)', manim_code, re.DOTALL)
        if not construct_match:
            return segments
            
        construct_code = construct_match.group(1)
        
        # Extract animation blocks with play() and wait()
        # Format: self.play(...) followed by optional self.wait()
        play_pattern = r'(\s*)self\.play\((.*?)\)(?:[\s\n]*self\.wait\(([0-9.]+)\))?'
        
        # Look for existing comments before animations
        comment_play_pattern = r'(?:#\s*(.*?)\s*\n)?\s*self\.play\((.*?)\)(?:[\s\n]*self\.wait\(([0-9.]+)\))?'
        
        for match in re.finditer(comment_play_pattern, construct_code, re.DOTALL):
            existing_comment = match.group(1)
            animation_code = match.group(2)
            wait_time = float(match.group(3) or 1.0)
            
            # Extract objects being animated
            animated_objects = self._extract_animated_objects(animation_code)
            
            segments.append({
                "type": "animation",
                "animation_code": animation_code,
                "wait_time": wait_time,
                "existing_comment": existing_comment,
                "animated_objects": animated_objects
            })
        
        # Also extract standalone wait() calls with comments
        wait_pattern = r'(?:#\s*(.*?)\s*\n)?\s*self\.wait\(([0-9.]+)\)'
        
        for match in re.finditer(wait_pattern, construct_code, re.DOTALL):
            if not re.search(r'self\.play\(.*?\)[\s\n]*self\.wait\(' + match.group(2) + r'\)', construct_code, re.DOTALL):
                # This is a standalone wait() not attached to a play()
                comment = match.group(1)
                wait_time = float(match.group(2))
                
                if comment or wait_time >= 2.0:  # Only include if it has a comment or significant wait time
                    segments.append({
                        "type": "wait",
                        "wait_time": wait_time,
                        "existing_comment": comment
                    })
        
        return segments
    
    def _extract_animated_objects(self, animation_code: str) -> List[str]:
        """Extract names and types of objects being animated"""
        objects = []
        
        # Look for common Manim animation methods
        animation_methods = ["Create", "Write", "FadeIn", "FadeOut", "Transform", "MoveAlongPath"]
        
        for method in animation_methods:
            matches = re.finditer(rf'{method}\s*\(\s*(\w+)', animation_code)
            for match in matches:
                objects.append({"name": match.group(1), "animation_type": method})
        
        # Look for Text objects which often contain educational content
        text_matches = re.finditer(r'Text\s*\(\s*[\'"]([^\'"]+)[\'"]', animation_code)
        for match in text_matches:
            objects.append({"content": match.group(1), "type": "Text"})
            
        return objects
    
    def _extract_topic_from_code(self, manim_code: str) -> str:
        """Extract the mathematical topic from code comments"""
        # Look for a title in the code
        title_match = re.search(r'[Tt]itle\s*=\s*Text\s*\(\s*[\'"]([^\'"]+)[\'"]', manim_code)
        if title_match:
            return title_match.group(1)
            
        # Look at the first comment block
        comment_block_match = re.match(r'#\s*(.*?)(?=\n\s*(?:#|\n|from|import))', manim_code, re.DOTALL)
        if comment_block_match:
            comment_text = comment_block_match.group(1).strip()
            # Try to identify topic from first sentence
            first_sentence = re.split(r'(?<=[.!?])\s+', comment_text)[0]
            return first_sentence
            
        # Default topic
        return "mathematical visualization"
    
    def _generate_complete_script(self, animation_segments: List[Dict[str, Any]], topic: str, system_prompt: str) -> Dict[str, Any]:
        """
        Generate a complete educational script for the animation using the Nebius QwenCoder model
        """
        # Create a prompt that includes animation details
        user_prompt = f"""Create an educational voiceover script for an animation about "{topic}".

The animation consists of these segments:
"""
        
        # Add each animation segment to the prompt
        for i, segment in enumerate(animation_segments):
            user_prompt += f"\nSegment {i+1}:"
            
            if segment["type"] == "animation":
                animated_objects = segment["animated_objects"]
                object_descriptions = []
                
                for obj in animated_objects:
                    if "content" in obj:
                        object_descriptions.append(f'Text "{obj["content"]}"')
                    elif "name" in obj:
                        object_descriptions.append(f'{obj["animation_type"]} of {obj["name"]}')
                
                if object_descriptions:
                    user_prompt += f" {', '.join(object_descriptions)}"
                else:
                    user_prompt += f" Animation code: {segment['animation_code']}"
                    
                user_prompt += f", duration: {segment['wait_time']} seconds"
                
                if segment["existing_comment"]:
                    user_prompt += f" (Existing description: \"{segment['existing_comment']}\")"
            else:
                user_prompt += f" Pause for {segment['wait_time']} seconds"
                
                if segment["existing_comment"]:
                    user_prompt += f" (Existing description: \"{segment['existing_comment']}\")"
        
        user_prompt += """

For each segment, create a natural, conversational, educational script part. Each script part should:
1. Explain the mathematical concept being visualized, not just describe what's being drawn
2. Build on previous segments to create a coherent narrative
3. Be timed appropriately for the segment duration (longer durations need more content)
4. Use natural, conversational language as if you were an engaging educator

Format your response as JSON with numbered segments like this:
{
  "title": "Brief descriptive title",
  "segments": {
    "1": "Script for segment 1...",
    "2": "Script for segment 2...",
    ...
  }
}

The script should be educational, engaging, and aligned with a 3Blue1Brown style of explanation.
"""
        
        # Use the Nebius QwenCoder model to generate a complete script
        try:
            response = self.client.chat.completions.create(
                model="Qwen/Qwen2.5-Coder-32B-Instruct",  # Use QwenCoder model from Nebius
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=8192,
                temperature=0.7,
                top_p=0.95,
                response_format={"type": "json_object"}
            )
            
            script_text = response.choices[0].message.content
            
            try:
                script = json.loads(script_text)
                return script
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from the text
                json_match = re.search(r'(\{[\s\S]*\})', script_text)
                if json_match:
                    try:
                        script = json.loads(json_match.group(1))
                        return script
                    except json.JSONDecodeError:
                        pass
                
                # Fallback in case the response isn't proper JSON
                return {
                    "title": topic,
                    "segments": {str(i+1): f"Explanation of {topic}, part {i+1}" 
                               for i in range(len(animation_segments))}
                }
                
        except Exception as e:
            print(f"Error generating script with Nebius API: {e}")
            # Fallback in case of API error
            return {
                "title": topic,
                "segments": {str(i+1): f"Explanation of {topic}, part {i+1}" 
                           for i in range(len(animation_segments))}
            }
    
    def _map_script_to_animations(self, script: Dict[str, Any], animation_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Map the generated script segments to the specific animation segments
        """
        mapped_script = {
            "title": script.get("title", "Mathematical Explanation"),
            "animation_scripts": []
        }
        
        script_segments = script.get("segments", {})
        
        for i, segment in enumerate(animation_segments):
            segment_idx = str(i+1)
            script_text = script_segments.get(segment_idx, f"Explanation part {segment_idx}")
            
            mapped_script["animation_scripts"].append({
                "animation_index": i,
                "animation_type": segment["type"],
                "wait_time": segment["wait_time"],
                "script": script_text,
                "existing_comment": segment["existing_comment"]
            })
            
        return mapped_script

def run_voiceover_script_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node function to run the VoiceoverScriptAgent
    
    Args:
        state: Current state with manim_code and user_input
        
    Returns:
        Updated state with voiceover_script
    """
    # Extract needed info from state
    manim_code = state.get("manim_code", "") or "\n".join(state.get("code_chunks", []))
    user_input = state.get("user_input", "")
    
    if not manim_code:
        return {
            "voiceover_script": {
                "title": "Default Explanation",
                "animation_scripts": []
            }
        }
    
    # Create the agent
    agent = VoiceoverScriptAgent()
    
    # Determine the educational level based on user input
    educational_level = "general"
    if re.search(r'kids|child|children|elementary|primary', user_input, re.IGNORECASE):
        educational_level = "primary"
    elif re.search(r'high school|teenager|teen', user_input, re.IGNORECASE):
        educational_level = "high school"
    elif re.search(r'college|university|advanced|graduate', user_input, re.IGNORECASE):
        educational_level = "university"
    
    # Generate the voiceover script
    voiceover_script = agent.generate_script(
        manim_code=manim_code, 
        topic=None,  # Let the agent extract the topic from the code
        educational_level=educational_level
    )
    
    # Add to state
    return {
        "voiceover_script": voiceover_script
    }