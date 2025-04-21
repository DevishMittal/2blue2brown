from manim import *
import numpy as np

class LSTMScene(Scene):
    def construct(self):
        scene_description = self.input_scene_description()
        if scene_description == "On a blank canvas, draw a simple graph of a function f(x) = x^2 from x = -2 to x = 2, with the x-axis and y-axis labeled. Add a Text object 'f(x) = x^2' above the graph. Draw a point P on the graph at x = 1, and a line tangent to the graph at point P.":
            self.scene1()
        elif scene_description == "On a blank canvas, draw the same graph of f(x) = x^2 as in Scene 1. Draw a secant line through two points on the graph, Q and R, close to point P. Label the points Q, R, and P. Add a Text object 'Secant Line' above the secant line.":
            self.scene2()
        elif scene_description == "On a blank canvas, draw the same graph of f(x) = x^2 as in Scene 1. Draw the tangent line at point P again. Add a Text object 'Tangent Line' above the tangent line. Draw an arrow from the secant line in Scene 2 to the tangent line, indicating the secant line approaching the tangent line as Q and R approach P.":
            self.scene3()
        elif scene_description == "On a blank canvas, draw a zoomed-in view of the graph around point P, showing the tangent line and the curve of the function. Add a Text object 'Slope of Tangent' above the tangent line. Draw a right triangle with the tangent line as the hypotenuse, and label the legs 'dx' and 'dy'.":
            self.scene4()
        elif scene_description == "On a blank canvas, draw the same right triangle as in Scene 4. Add a Text object 'dy/dx' above the triangle. Draw an arrow from the triangle to a Text object 'f\'(x) = 2x' below, indicating the derivative of the function f(x) = x^2.":
            self.scene5()
        elif scene_description == "On a blank canvas, draw a graph of the derivative function f\'(x) = 2x, with the x-axis and y-axis labeled. Add a Text object 'Derivative of f(x)' above the graph.":
            self.scene6()

    def input_scene_description(self):
        scene_descriptions = [
            "On a blank canvas, draw a simple graph of a function f(x) = x^2 from x = -2 to x = 2, with the x-axis and y-axis labeled. Add a Text object 'f(x) = x^2' above the graph. Draw a point P on the graph at x = 1, and a line tangent to the graph at point P.",
            "On a blank canvas, draw the same graph of f(x) = x^2 as in Scene 1. Draw a secant line through two points on the graph, Q and R, close to point P. Label the points Q, R, and P. Add a Text object 'Secant Line' above the secant line.",
            "On a blank canvas, draw the same graph of f(x) = x^2 as in Scene 1. Draw the tangent line at point P again. Add a Text object 'Tangent Line' above the tangent line. Draw an arrow from the secant line in Scene 2 to the tangent line, indicating the secant line approaching the tangent line as Q and R approach P.",
            "On a blank canvas, draw a zoomed-in view of the graph around point P, showing the tangent line and the curve of the function. Add a Text object 'Slope of Tangent' above the tangent line. Draw a right triangle with the tangent line as the hypotenuse, and label the legs 'dx' and 'dy'.",
            "On a blank canvas, draw the same right triangle as in Scene 4. Add a Text object 'dy/dx' above the triangle. Draw an arrow from the triangle to a Text object 'f\'(x) = 2x' below, indicating the derivative of the function f(x) = x^2.",
            "On a blank canvas, draw a graph of the derivative function f\'(x) = 2x, with the x-axis and y-axis labeled. Add a Text object 'Derivative of f(x)' above the graph."
        ]
        return random.choice(scene_descriptions)

    def scene1(self):
        axes = Axes(
            x_range=[-2, 2, 1],
            y_range=[-1, 5, 1],
            axis_config={"include_tip": False}
        )
        graph = axes.plot(lambda x: x**2, x_range=[-2, 2], color=BLUE)
        point_p = Dot(axes.coords_to_point(1, 1), color=YELLOW)
        tangent_line = axes.plot(lambda x: 2*x - 1, x_range=[-2, 2], color=GREEN)
        func_label = axes.get_graph_label(graph, label=r"f(x) = x^2")
        self.add(axes, graph, point_p, tangent_line, func_label)
        self.wait(2)
        subtitle = Text("Visualizing a function")
        self.play(Write(subtitle))
        self.wait(2)

    def scene2(self):
        axes = Axes(
            x_range=[-2, 2, 1],
            y_range=[-1, 5, 1],
            axis_config={"include_tip": False}
        )
        graph = axes.plot(lambda x: x**2, x_range=[-2, 2], color=BLUE)
        point_p = Dot(axes.coords_to_point(1, 1), color=YELLOW)
        point_q = Dot(axes.coords_to_point(0.9, 0.81), color=YELLOW)
        point_r = Dot(axes.coords_to_point(1.1, 1.21), color=YELLOW)
        secant_line = Line(axes.coords_to_point(0.9, 0.81), axes.coords_to_point(1.1, 1.21), color=RED)
        self.add(axes, graph, point_p, point_q, point_r, secant_line)
        self.wait(2)
        subtitle = Text("Introducing the secant line")
        self.play(Write(subtitle))
        self.wait(2)

    def scene3(self):
        axes = Axes(
            x_range=[-2, 2, 1],
            y_range=[-1, 5, 1],
            axis_config={"include_tip": False}
        )
        graph = axes.plot(lambda x: x**2, x_range=[-2, 2], color=BLUE)
        point_p = Dot(axes.coords_to_point(1, 1), color=YELLOW)
        tangent_line = axes.plot(lambda x: 2*x - 1, x_range=[-2, 2], color=GREEN)
        secant_line = Line(axes.coords_to_point(0.9, 0.81), axes.coords_to_point(1.1, 1.21), color=RED)
        arrow = Arrow(secant_line.get_end(), tangent_line.get_end(), color=YELLOW)
        self.add(axes, graph, point_p, tangent_line, secant_line, arrow)
        self.wait(2)
        subtitle = Text("Approaching the tangent line")
        self.play(Write(subtitle))
        self.wait(2)

    def scene4(self):
        axes = Axes(
            x_range=[0.5, 1.5, 0.1],
            y_range=[0.5, 1.5, 0.1],
            axis_config={"include_tip": False}
        )
        graph = axes.plot(lambda x: x**2, x_range=[0.5, 1.5], color=BLUE)
        point_p = Dot(axes.coords_to_point(1, 1), color=YELLOW)
        tangent_line = axes.plot(lambda x: 2*x - 1, x_range=[0.5, 1.5], color=GREEN)
        right_triangle = Polygon(axes.coords_to_point(1, 1), axes.coords_to_point(1.1, 1), axes.coords_to_point(1, 1.1), color=YELLOW)
        dx_label = Text("dx", color=YELLOW).next_to(right_triangle, DOWN)
        dy_label = Text("dy", color=YELLOW).next_to(right_triangle, RIGHT)
        self.add(axes, graph, point_p, tangent_line, right_triangle, dx_label, dy_label)
        self.wait(2)
        subtitle = Text("Defining the derivative")
        self.play(Write(subtitle))
        self.wait(2)

    def scene5(self):
        axes = Axes(
            x_range=[0.5, 1.5, 0.1],
            y_range=[0.5, 1.5, 0.1],
            axis_config={"include_tip": False}
        )
        right_triangle = Polygon(axes.coords_to_point(1, 1), axes.coords_to_point(1.1, 1), axes.coords_to_point(1, 1.1), color=YELLOW)
        dx_label = Text("dx", color=YELLOW).next_to(right_triangle, DOWN)
        dy_label = Text("dy", color=YELLOW).next_to(right_triangle, RIGHT)
        dy_dx_label = Text("dy/dx", color=YELLOW).next_to(right_triangle, UP)
        f_prime_label = Text("f'(x) = 2x", color=YELLOW).next_to(right_triangle, DOWN)
        arrow = Arrow(dy_dx_label.get_bottom(), f_prime_label.get_top(), color=YELLOW)
        self.add(right_triangle, dx_label, dy_label, dy_dx_label, f_prime_label, arrow)
        self.wait(2)
        subtitle = Text("Calculating the derivative")
        self.play(Write(subtitle))
        self.wait(2)

    def scene6(self):
        axes = Axes(
            x_range=[-2, 2, 1],
            y_range=[-2, 4, 1],
            axis_config={"include_tip": False}
        )
        graph = axes.plot(lambda x: 2*x, x_range=[-2, 2], color=BLUE)
        func_label = axes.get_graph_label(graph, label=r"f'(x) = 2x")
        self.add(axes, graph, func_label)
        self.wait(2)
        subtitle = Text("Visualizing the derivative")
        self.play(Write(subtitle))
        self.wait(2)
