# app/controllers/combiner.py
import os
import re

class CombinedCodeGenerator:
    def __init__(self, code_strings):
        self.code_strings = code_strings

    def generate_combined_code(self):
        import_lines = set()
        code_blocks = []

        # Ensure required imports are added.
        import_lines.add("from manim import *")
        import_lines.add("import numpy as np")  # Added to allow np.arange

        for code in self.code_strings:
            # Clean up code to remove markdown delimiters
            code = code.replace("```python", "").replace("```", "")
            
            lines = code.splitlines()
            block = []
            for line in lines:
                # Skip any remaining markdown or explanatory text
                if line.strip().startswith("from manim import"):
                    import_lines.add(line.strip())
                elif line.strip().startswith("import "):
                    import_lines.add(line.strip())
                elif not line.startswith("#") and line.strip() and not "Here is" in line and not "This code" in line:
                    block.append(line)
            code_blocks.append("\n".join(block).strip())
        
        # Basic static content for a working scene
        simple_scene = """
class LSTMScene(Scene):
    def construct(self):
        title = Text("Machine Learning Visualization")
        self.play(Write(title))
        self.wait(1)
        self.play(FadeOut(title))
        
        subtitle = Text("Generated with Nebius AI")
        self.play(Write(subtitle))
        self.wait(1)
        self.play(FadeOut(subtitle))
"""

        # Combine unique import lines at the top.
        combined = "\n".join(sorted(import_lines)) + "\n\n"
        
        # Check if we can extract a usable scene from the generated code
        has_valid_scene = False
        for block in code_blocks:
            if "class LSTMScene(Scene)" in block:
                has_valid_scene = True
                break
        
        # Fix common issues in the generated code
        fixed_blocks = []
        for block in code_blocks:
            # Fix coordinate issues - ensure 3D coordinates
            # Pattern matches things like: Line(start=(-2, 0), end=(-1, 0))
            block = re.sub(r'(Line|Arrow|Vector|Point)(\s*\()(\s*start\s*=\s*\()([^)]+?)(\))', 
                          lambda m: self._fix_coordinate(m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)), 
                          block)
            
            # Pattern matches coordinates like (x, y) but not (x, y, z)
            block = re.sub(r'(\(\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*\))', 
                          lambda m: self._fix_tuple_coord(m.group(1)), 
                          block)
            
            # Fix FunctionGraph parameters
            block = block.replace("FunctionGraph(lambda x: x**2, x_range=[-2, 2], y_range=[0, 4]", 
                                "FunctionGraph(lambda x: x**2, x_range=[-2, 2]")
            
            # Fix class naming issues
            if "class" in block and "Scene" in block and "LSTMScene" not in block:
                block = block.replace("class MainScene", "class LSTMScene")
                block = block.replace("class SimpleScene", "class LSTMScene")
                block = block.replace("class DemoScene", "class LSTMScene")
            
            # Add proper Scene inheritance if missing
            if "class LSTMScene" in block and "Scene" not in block:
                block = block.replace("class LSTMScene", "class LSTMScene(Scene)")
            
            # Fix problematic usage of Tree and Node classes
            if "Tree(" in block or "Node(" in block:
                block = self._remove_tree_nodes(block)
            
            fixed_blocks.append(block)
        
        # Append fixed code blocks separated by two newlines
        if has_valid_scene:
            combined += "\n\n".join(fixed_blocks)
        else:
            # Generate a simple working scene if none was found in the code blocks
            combined += simple_scene
        
        # Fix problematic range() calls by replacing them with np.arange()
        combined = combined.replace("range(-1.5, 2, 1)", "np.arange(-1.5, 2, 1)")
        
        return combined

    def _fix_coordinate(self, obj_type, open_paren, start_part, coords, close_paren):
        """Fix coordinates in Line/Arrow objects by ensuring they're 3D"""
        if ',' in coords and coords.count(',') == 1:  # Only has x,y
            # Split coordinates and add z=0
            x, y = coords.split(',')
            return f"{obj_type}{open_paren}{start_part}np.array([{x.strip()}, {y.strip()}, 0]){close_paren}"
        return f"{obj_type}{open_paren}{start_part}{coords}{close_paren}"
    
    def _fix_tuple_coord(self, coord_tuple):
        """Convert (x, y) tuples to (x, y, 0) format"""
        coord_tuple = coord_tuple.strip('()')
        parts = coord_tuple.split(',')
        if len(parts) == 2:  # Only has x,y
            return f"(np.array([{parts[0].strip()}, {parts[1].strip()}, 0]))"
        return f"({coord_tuple})"
    
    def _remove_tree_nodes(self, block):
        """Replace Tree and Node classes with basic shapes"""
        # If a scene contains Tree or Node, completely replace it with a simple visualization
        # This is a drastic but failsafe approach
        if "def construct" in block:
            construct_match = re.search(r'def\s+construct\s*\([^)]*\):(.*?)(?:def|\Z)', block, re.DOTALL)
            if construct_match:
                # Extract the subtitle if present
                subtitle_match = re.search(r'Text\s*\(\s*["\']([^"\']+)["\']', construct_match.group(1))
                subtitle_text = subtitle_match.group(1) if subtitle_match else "Basic Visualization"
                
                # Create a simplified replacement
                simple_viz = f"""
    def construct(self):
        title = Text("{subtitle_text}")
        self.play(Write(title))
        self.wait(1)
        self.play(FadeOut(title))
        
        # Create simple circle representation instead of Tree
        circle1 = Circle(radius=0.5).shift(UP)
        circle2 = Circle(radius=0.5).shift(LEFT + DOWN)
        circle3 = Circle(radius=0.5).shift(RIGHT + DOWN)
        line1 = Line(start=np.array([0, 0.5, 0]), end=np.array([-0.5, -0.5, 0]))
        line2 = Line(start=np.array([0, 0.5, 0]), end=np.array([0.5, -0.5, 0]))
        
        self.play(Create(circle1), Create(circle2), Create(circle3))
        self.play(Create(line1), Create(line2))
        
        subtitle = Text("{subtitle_text}").to_edge(DOWN)
        self.play(Write(subtitle))
        self.wait(3)
"""
                return re.sub(r'def\s+construct\s*\([^)]*\):(.*?)(?:def|\Z)', simple_viz, block, flags=re.DOTALL)
        return block

    def save_to_file(self, folder="generated_manim", filename="manim.py"):
        if not os.path.exists(folder):
            os.makedirs(folder)

        combined_code = self.generate_combined_code()
        filepath = os.path.join(folder, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(combined_code)
        return filepath
