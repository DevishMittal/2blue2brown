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
        
        # Add labels using Text instead of MathTex
        x_label = Text("x", font_size=24).next_to(axes.x_axis, DOWN)
        y_label = Text("f(x)", font_size=24).next_to(axes.y_axis, LEFT)
        labels = VGroup(x_label, y_label)
        
        # Graph a function
        quadratic = axes.plot(lambda x: x**2, color=BLUE)
        quadratic_label = Text("f(x) = x²", font_size=24).next_to(quadratic, UP + RIGHT, buff=0.5)
        
        # Add point with coordinates
        point = Dot(axes.c2p(1, 1), color=RED)
        point_label = Text("(1, 1)", font_size=24).next_to(point, RIGHT, buff=0.2)
        
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
        tangent_label = Text("Tangent: y = 2x - 1", font_size=24).next_to(tangent_line, UP + RIGHT, buff=0.5)
        
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
        
        # Demonstrate equations with plain text
        title_eq = Text("Mathematical Equations")
        self.play(Transform(title, title_eq))
        self.wait(1)
        
        # Create various math equations using Text instead of MathTex
        eq1 = Text("d/dx(x²) = 2x", font_size=30)
        eq2 = Text("∫₀¹ x² dx = 1/3", font_size=30)
        eq3 = Text("e^(iπ) + 1 = 0", font_size=30)
        
        equations = VGroup(eq1, eq2, eq3).arrange(DOWN, buff=0.5)
        self.play(Write(equations))
        self.wait(2)
        
        # Highlight Euler's identity
        self.play(eq3.animate.set_color(YELLOW).scale(1.5))
        self.wait(2) 