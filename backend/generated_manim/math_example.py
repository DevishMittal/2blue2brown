from manim import *
import numpy as np

class LSTMScene(Scene):
    def construct(self):
        # Title
        title = Text("Mathematical Functions")
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        
        # Create axes
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2, 6, 1],
            axis_config={"include_tip": True},
        )
        
        # Add labels
        x_label = axes.get_x_axis_label("x")
        y_label = axes.get_y_axis_label("f(x)")
        labels = VGroup(x_label, y_label)
        
        # Graph a function
        quadratic = axes.plot(lambda x: x**2, color=BLUE)
        quadratic_label = MathTex("f(x) = x^2").next_to(quadratic, UR, buff=0.5)
        
        # Add point with coordinates
        point = Dot(axes.c2p(1, 1), color=RED)
        point_label = MathTex("(1, 1)").next_to(point, RIGHT, buff=0.2)
        
        # Animate the creation of these objects
        self.play(Create(axes), Create(labels))
        self.wait(1)
        
        self.play(Create(quadratic))
        self.play(Write(quadratic_label))
        self.wait(1)
        
        self.play(Create(point), Write(point_label))
        self.wait(1)
        
        # Draw tangent line at the point (1, 1)
        tangent_line = axes.plot(lambda x: 2*x - 1, x_range=[-0.5, 2.5], color=GREEN)
        tangent_label = MathTex("\\text{Tangent: } y = 2x - 1").next_to(tangent_line, UR, buff=0.5)
        
        self.play(Create(tangent_line), Write(tangent_label))
        self.wait(1)
        
        # Add explanation text
        explanation = Text("The derivative at x=1 is 2", font_size=30).to_edge(DOWN)
        self.play(Write(explanation))
        self.wait(2)
        
        # Clear screen for next demonstration
        self.play(
            FadeOut(axes),
            FadeOut(labels),
            FadeOut(quadratic),
            FadeOut(quadratic_label),
            FadeOut(point),
            FadeOut(point_label),
            FadeOut(tangent_line),
            FadeOut(tangent_label),
            FadeOut(explanation)
        )
        self.wait(1)
        
        # Demonstrate LaTeX equations
        title_eq = Text("Mathematical Equations")
        self.play(Transform(title, title_eq))
        self.wait(1)
        
        # Create various math equations
        eq1 = MathTex("\\frac{d}{dx}x^2 = 2x")
        eq2 = MathTex("\\int_0^1 x^2 dx = \\frac{1}{3}")
        eq3 = MathTex("e^{i\\pi} + 1 = 0")
        
        equations = VGroup(eq1, eq2, eq3).arrange(DOWN, buff=0.5)
        self.play(Write(equations))
        self.wait(2)
        
        # Highlight Euler's identity
        self.play(eq3.animate.set_color(YELLOW).scale(1.5))
        self.wait(2) 