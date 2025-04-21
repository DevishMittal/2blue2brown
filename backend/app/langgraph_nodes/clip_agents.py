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
        "- CRITICAL SYNTAX FOR RANDOM POINT GENERATION: When generating random points, use the following pattern EXACTLY:\n"
        "  ```\n"
        "  # Generate x and y values separately\n"
        "  x_values = np.random.uniform(-3, 3, 10)\n"
        "  y_values = np.random.uniform(-2, 2, 10)\n"
        "  \n"
        "  # Create 3D points by combining them\n"
        "  points = [np.array([x, y, 0]) for x, y in zip(x_values, y_values)]\n"
        "  ```\n"
        "- NEVER use the pattern `np.random.uniform(low=np.array([...]), high=np.array([...]), size=(...))` as it causes errors.\n"
        "- For machine learning visualizations with decision boundaries, calculate them properly using numpy functions like polyfit, not hardcoded values.\n"
        "- Use only ASCII characters in your code and avoid special Unicode characters that might cause encoding issues.\n"
        "- Stay on each scene long enough so that all the information on that scene can be spoken before changing the scene.\n"
        "- The subtitle must appear on screen using a `Text` object.\n\n"
        "Here are strong examples of common visualization patterns you should follow exactly:\n\n"
        "1. For generating random points for two classes (e.g., for machine learning):\n"
        "```\n"
        "# Set reproducibility\n"
        "np.random.seed(42)\n\n"
        "# Generate class 1 points\n"
        "x1 = np.random.uniform(-3, -1, 5)\n"
        "y1 = np.random.uniform(-2, 2, 5)\n"
        "class1_points = [np.array([x, y, 0]) for x, y in zip(x1, y1)]\n"
        "class1_dots = [Dot(point=p, color=RED, radius=0.05) for p in class1_points]\n\n"
        "# Generate class 2 points\n"
        "x2 = np.random.uniform(1, 3, 5)\n"
        "y2 = np.random.uniform(-2, 2, 5)\n"
        "class2_points = [np.array([x, y, 0]) for x, y in zip(x2, y2)]\n"
        "class2_dots = [Dot(point=p, color=BLUE, radius=0.05) for p in class2_points]\n"
        "```\n\n"
        "2. For creating a decision boundary:\n"
        "```\n"
        "# Draw a decision boundary line\n"
        "decision_line = Line(start=np.array([-3, 0, 0]), end=np.array([3, 0, 0]), color=GREEN)\n"
        "self.play(Create(decision_line))\n"
        "```\n\n"
        "3. For finding the closest points to a line (e.g., support vectors):\n"
        "```\n"
        "# Find closest points to the line\n"
        "def distance_to_line(point):\n"
        "    return abs(point[1])\n"
        "\n"
        "closest_red_dot = class1_dots[np.argmin([distance_to_line(dot.get_center()) for dot in class1_dots])]\n"
        "closest_blue_dot = class2_dots[np.argmin([distance_to_line(dot.get_center()) for dot in class2_dots])]\n"
        "\n"
        "# Highlight them\n"
        "self.play(closest_red_dot.animate.set_color(YELLOW), closest_blue_dot.animate.set_color(YELLOW))\n"
        "```\n\n"
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