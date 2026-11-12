from Classes import Helpers
from Classes.Monitor import Monitor
import Classes.Renderer as Renderer

monitors: list[Monitor] = Helpers.get_monitors()

Renderer.run(monitors)