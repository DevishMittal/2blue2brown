# app/controllers/combiner.py
import os

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

    def save_to_file(self, folder="generated_manim", filename="manim.py"):
        if not os.path.exists(folder):
            os.makedirs(folder)

        combined_code = self.generate_combined_code()
        filepath = os.path.join(folder, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(combined_code)
        return filepath
