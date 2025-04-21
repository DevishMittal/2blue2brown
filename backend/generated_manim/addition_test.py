from manim import *
import numpy as np

class LSTMScene(Scene):
    def construct(self):
        # Subtitle
        subtitle = Text("Visualizing Addition of 3 Numbers")
        self.play(Write(subtitle))
        self.wait(2)
        self.play(subtitle.animate.to_edge(UP))
        
        # Create the numbers to add
        num1 = Text("2", font_size=40).shift(np.array([-4, 1, 0]))
        num2 = Text("4", font_size=40).shift(np.array([-4, 0, 0]))
        num3 = Text("5", font_size=40).shift(np.array([-4, -1, 0]))
        
        # Number labels
        label1 = Text("First number", font_size=24).next_to(num1, LEFT, buff=0.5)
        label2 = Text("Second number", font_size=24).next_to(num2, LEFT, buff=0.5)
        label3 = Text("Third number", font_size=24).next_to(num3, LEFT, buff=0.5)
        
        # Show the numbers one by one
        self.play(Write(label1), Write(num1))
        self.wait(1)
        self.play(Write(label2), Write(num2))
        self.wait(1)
        self.play(Write(label3), Write(num3))
        self.wait(1)
        
        # Plus signs
        plus1 = Text("+", font_size=40).shift(np.array([-3, 0, 0]))
        plus2 = Text("+", font_size=40).shift(np.array([-3, -1, 0]))
        
        self.play(Write(plus1), Write(plus2))
        self.wait(1)
        
        # Equals sign and result
        equals = Text("=", font_size=40).shift(np.array([-2, 0, 0]))
        result = Text("11", font_size=60, color=YELLOW).shift(np.array([0, 0, 0]))
        
        # Visual representation - use rectangles to show the quantities
        rect1 = VGroup(*[Square(side_length=0.5, fill_opacity=0.6, fill_color=BLUE) 
                        for _ in range(2)]).arrange(RIGHT, buff=0.1).shift(np.array([0, 1, 0]))
        
        rect2 = VGroup(*[Square(side_length=0.5, fill_opacity=0.6, fill_color=GREEN) 
                        for _ in range(4)]).arrange(RIGHT, buff=0.1).shift(np.array([0, 0, 0]))
        
        rect3 = VGroup(*[Square(side_length=0.5, fill_opacity=0.6, fill_color=RED) 
                        for _ in range(5)]).arrange(RIGHT, buff=0.1).shift(np.array([0, -1, 0]))
        
        # Show the equation and visual representation
        self.play(Write(equals))
        self.wait(1)
        
        # First show each number's visual representation
        self.play(FadeIn(rect1))
        rect1_label = Text("2", font_size=24).next_to(rect1, RIGHT)
        self.play(Write(rect1_label))
        self.wait(1)
        
        self.play(FadeIn(rect2))
        rect2_label = Text("4", font_size=24).next_to(rect2, RIGHT)
        self.play(Write(rect2_label))
        self.wait(1)
        
        self.play(FadeIn(rect3))
        rect3_label = Text("5", font_size=24).next_to(rect3, RIGHT)
        self.play(Write(rect3_label))
        self.wait(1)
        
        # Combining the values
        self.play(rect1.animate.shift(np.array([3, 0, 0])), 
                 rect2.animate.shift(np.array([3, 0, 0])), 
                 rect3.animate.shift(np.array([3, 0, 0])),
                 FadeOut(rect1_label),
                 FadeOut(rect2_label),
                 FadeOut(rect3_label))
        
        # Arrange all squares in a single row to show the sum
        combined_squares = VGroup(*[sq.copy() for sq in rect1] + 
                                [sq.copy() for sq in rect2] + 
                                [sq.copy() for sq in rect3])
        combined_squares.arrange(RIGHT, buff=0.1).shift(np.array([3, 0, 0]))
        
        self.play(FadeOut(rect1), FadeOut(rect2), FadeOut(rect3))
        self.play(FadeIn(combined_squares))
        self.wait(1)
        
        # Show the result
        self.play(Write(result))
        result_label = Text("Total", font_size=24).next_to(result, DOWN)
        self.play(Write(result_label))
        
        # Highlight the final answer
        self.play(combined_squares.animate.set_color(YELLOW))
        
        # Final message
        final_text = Text("2 + 4 + 5 = 11", font_size=40).to_edge(DOWN)
        self.play(Write(final_text))
        self.wait(3) 