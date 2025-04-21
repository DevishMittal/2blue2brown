from manim import *
import numpy as np

class LSTMScene(Scene):
    def construct(self):
        # Test subtitle
        subtitle = Text("Testing coordinate fixes")
        self.play(Write(subtitle))
        self.wait(1)
        self.play(FadeOut(subtitle))
        
        # Test basic shapes with proper 3D coordinates
        circle = Circle(radius=0.5).shift(np.array([0, 0, 0]))
        self.play(Create(circle))
        
        # Test Line with proper 3D coordinates
        line = Line(
            start=np.array([-2, 0, 0]), 
            end=np.array([2, 0, 0])
        )
        self.play(Create(line))
        
        # Test positioning
        square = Square().shift(UP + RIGHT)
        self.play(Create(square))
        
        # Final text
        final_text = Text("Success!").to_edge(DOWN)
        self.play(Write(final_text))
        self.wait(2) 