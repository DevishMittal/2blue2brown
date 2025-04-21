from app.controllers.grant import Grant
import asyncio

async def run_clip_agent(index, scene, grant_instance):
    print(f"prompt being passed in. {scene}")
    prompt = (
        "You are an expert code animator creating a single Manim (Python) scene in the style of 3Blue1Brown.\n\n"
        f"Use the following scene description and subtitle to generate the code:\n\n"
        f"Scene Description:\n{scene['scene_description']}\n"
        f"Subtitle:\n\"{scene['subtitle_script']}\"\n\n"
        "❗Important:\n"
        "- Output **only** the complete Python code as plain text. Do NOT include any explanations, comments, or markdown (no ```python).\n"
        "- Do NOT include phrases like 'Here is the code:' or 'This code creates...'.\n"
        "- Your output will be compiled directly, so it must be a standalone, valid Python script using the Manim library.\n"
        "- Use a single Scene class with the name `LSTMScene`.\n"
        "- Only use standard Manim objects like Circle, Rectangle, Arrow, Line, Text, etc. Do not use custom classes like Tree or Node.\n"
        "- ALWAYS use 3D coordinates even for 2D objects. For example, use `Line(start=np.array([-2, 0, 0]), end=np.array([-1, 0, 0]))` NOT `Line(start=(-2, 0), end=(-1, 0))`.\n"
        "- For all geometric objects, always provide the z-coordinate (even if it's 0).\n"
        "- Remember that Manim works in 3D space, so all points must be 3D vectors with x, y, and z coordinates.\n"
        "- All position specifications must use either: np.array([x, y, z]), or specific position methods like .shift(UP), .next_to(obj, direction).\n"
        "- For math equations, use regular Text objects instead of MathTex to avoid LaTeX dependencies. For example, use `Text(\"f(x) = x²\")` instead of MathTex.\n"
        "- When generating random data, always use proper numpy functions (np.random.uniform, np.random.normal, etc.) and ensure they're provided with the correct shape and dimensions.\n"
        "- For statistical visualizations, use np.random.seed(42) at the beginning to ensure reproducibility.\n"
        "- When working with random values, do NOT use random.uniform(np.array([min, max, 0])) as this is invalid. Instead use: np.random.uniform(min, max) to generate scalar values.\n"
        "- For numerical operations like polyfit, ensure data arrays have compatible shapes and dimensions.\n"
        "- Use only ASCII characters in your code and avoid special Unicode characters that might cause encoding issues.\n"
        "- Stay on each scene long enough so that all the information on that scene can be spoken before changing the scene.\n"
        "- The subtitle must appear on screen using a `Text` object.\n\n"
        "Here is a well-structured example of a valid Manim scene with random data points:\n\n"
        "from manim import *\n"
        "import numpy as np\n\n"
        "class LSTMScene(Scene):\n"
        "    def construct(self):\n"
        "        # Create the subtitle\n"
        "        subtitle = Text(\"Data Visualization Example\")\n"
        "        self.play(Write(subtitle))\n"
        "        self.wait(1)\n"
        "        self.play(subtitle.animate.to_edge(UP))\n\n"
        "        # Create axes\n"
        "        axes = Axes(\n"
        "            x_range=[-3, 3, 1],\n"
        "            y_range=[-2, 2, 1],\n"
        "            axis_config={\"include_tip\": True},\n"
        "        )\n"
        "        self.play(Create(axes))\n"
        "        self.wait(1)\n\n"
        "        # Generate random data points properly\n"
        "        np.random.seed(42)  # For reproducibility\n"
        "        x_values = np.random.uniform(-2, 2, 10)\n"
        "        y_values = x_values * 0.5 + np.random.normal(0, 0.3, 10)\n\n"
        "        # Create dots at each point\n"
        "        dots = [Dot(axes.c2p(x, y, 0), radius=0.05) for x, y in zip(x_values, y_values)]\n"
        "        self.play(*[Create(dot) for dot in dots])\n"
        "        self.wait(1)\n\n"
        "        # Draw a trend line\n"
        "        m, b = np.polyfit(x_values, y_values, 1)\n"
        "        line = axes.plot(lambda x: m*x + b, color=YELLOW)\n"
        "        self.play(Create(line))\n"
        "        self.wait(2)\n\n"
        "Begin your output now:"
    )

    
    return index, grant_instance.code_response(prompt)

def generate_clips(state):
    scene_plan = state.get("scene_plan", [])
    grant = Grant()
    
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for index, scene in enumerate(scene_plan):
            futures.append(executor.submit(run_clip_agent_sync, index, scene, Grant()))

        results = [f.result() for f in futures]

    results.sort(key=lambda x: x[0])
    code_chunks = [r[1] for r in results]
    for i, chunk in enumerate(code_chunks):
        print(f"Chunk {i}: {chunk}")
    return {
        "code_chunks": code_chunks
    }
    
def run_clip_agent_sync(index, scene, grant_instance):
    return asyncio.run(run_clip_agent(index, scene, grant_instance))