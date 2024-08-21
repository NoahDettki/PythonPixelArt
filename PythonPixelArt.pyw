import os
import math
import pygame
import pygame_gui
from pygame.locals import *
from PIL import Image
from enum import Enum
import colorsys
from win32 import win32gui
import win32con

PATH = os.path.dirname(os.path.abspath(__file__))
SIZE_ON_STARTUP = (800, 600)
WHITE = (255, 255, 255, 255)
GRAY = (127, 127, 127, 255)
BLACK = (0, 0, 0, 255)
BLACK_50 = (0, 0, 0, 0)
HIGHLIGHT = (66, 135, 245, 255)

Tool = Enum('Tool', ['PENCIL', 'COMING SOON'])

class Canvas:
    def __init__(self, x:int, y:int, width:int, height:int, columns:int, rows:int):
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._columns = columns
        self._rows = rows
        self._factor = columns / width
        self._surface = pygame.Surface((width, height))
        self._layers = [Image.new('RGBA', (columns, rows), (0,0,0,0))]
        print(f"Created canvas with factor {self._factor}")
    def s2pixel(self, x, y) -> tuple:
        '''Screen position to pixel position'''
        x = math.floor((x - self._x) * self._factor)
        y = math.floor((y - self._y) * self._factor)
        return (x, y)
    def set(self, mouse_pos:tuple, color:tuple):
        canvas_pos = self.s2pixel(mouse_pos[0], mouse_pos[1])
        # Check if inputs are valid
        if canvas_pos[0] < 0 or canvas_pos[0] >= self._columns or canvas_pos[1] < 0 or canvas_pos[1] >= self._rows:
            #print(f"{canvas_pos} is out of bounds")
            return
        self._layers[0].putpixel((canvas_pos[0], canvas_pos[1]), color)
    def render(self, surface):
        cell_size = self._width / self._columns
        for x in range(self._columns):
            for y in range(self._rows):
                pygame.draw.rect(self._surface, self._layers[0].getpixel((x, y)),
                                 pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size))
        surface.blit(self._surface, (self._x, self._y))
    def save_image(self):
        self._layers[0].save('myImage.png')
    def get_rect(self):
        return pygame.Rect(self._x, self._y, self._width, self._height)

class ColorPicker:
    def __init__(self, x:int, y:int, picker_dimension:int, gap_width:int, slider_width:int):
        self._x = x
        self._y = y
        self._size = picker_dimension
        self._gap = gap_width
        self._hue_x = slider_width
        self._surface = pygame.Surface((picker_dimension + gap_width + slider_width, picker_dimension), pygame.SRCALPHA)
        self._crosshair = pygame.image.load(PATH + "\sprites\crosshair.png").convert_alpha()
        self._knob = pygame.image.load(PATH + "\sprites\knob.png").convert_alpha()
        self._crosshair_center_size = (11, 11)
        self._knob_center_size =(20, 5)
        self._picker_rect = pygame.Rect(x, y, picker_dimension, picker_dimension)
        self._slider_rect = pygame.Rect(x + picker_dimension + gap_width, y, slider_width, picker_dimension)
        self.render_slider()
        self.move_picker((0, 0))
        self.move_slider(0)
        self.is_picking = False
        self.is_sliding = False
    def render_picker(self, hue:float):
        '''Rerenders the color picker square with a new hue value'''
        for x in range(self._size):
            s = x / (self._size-1)
            for y in range(self._size):
                v = 1 - y / (self._size-1)
                rgb = colorsys.hsv_to_rgb(hue, s, v)
                self._surface.set_at((x, y), tuple([255.0 * i for i in rgb]))
    def render_slider(self):
        '''Rerenders the color slider'''
        for y in range(self._size):
            h = y / (self._size-1)
            for x in range(self._hue_x):
                rgb = colorsys.hsv_to_rgb(h, 1, 1)
                self._surface.set_at((self._size + self._gap + x, y), tuple([255.0 * i for i in rgb]))
    def get_picker_rect(self) -> pygame.Rect:
        return self._picker_rect
    def get_slider_rect(self) -> pygame.Rect:
        return self._slider_rect
    def s2picker(self, mouse_position:tuple) -> tuple:
        '''Converts the mouse position (screen space) to the position on the picker'''
        return (mouse_position[0] - self._x, mouse_position[1] - self._y)
    def s2slider(self, mouse_position:tuple) -> int:
        '''Converts the mouse position (screen space) to the y position on the slider'''
        return mouse_position[1] - self._y
    def move_picker(self, pos:tuple):
        '''Moves the knob to the given position on the picker'''
        x, y = pos
        if x < 0: x = 0
        if x >= self._size: x = self._size-1
        if y < 0: y = 0
        if y >= self._size: y = self._size-1
        self._crosshair_pos = (x, y)
        self._color = self._surface.get_at(self._crosshair_pos)
    def move_slider(self, y:int):
        '''Moves the knob to the given y position on the slider and rerenders the picker and slider'''
        if y < 0: y = 0
        if y > self._size: y = self._size
        self._knob_pos = (self._size + self._gap + self._hue_x/2, y)
        hue = y / self._size
        self.render_picker(hue)
        self._knob_color = [i * 255.0 for i in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
        self._color = self._surface.get_at(self._crosshair_pos)
    def render(self, surface:pygame.Surface):
        # Surface
        surface.blit(self._surface, (self._x, self._y))
        # Crosshair
        global_c_pos = (self._x + self._crosshair_pos[0],
                        self._y + self._crosshair_pos[1])
        crosshair_image_pos_with_offset = (global_c_pos[0] - int(self._crosshair.get_rect().width/2),
                                           global_c_pos[1] - int(self._crosshair.get_rect().height/2))
        surface.blit(self._crosshair, crosshair_image_pos_with_offset)
        pygame.draw.rect(screen, self._color, pygame.Rect((global_c_pos[0] - int(self._crosshair_center_size[0]/2),
                                                          global_c_pos[1] - int(self._crosshair_center_size[1]/2)),
                                                          self._crosshair_center_size))
        # Slider knob
        global_k_pos = (self._x + self._knob_pos[0],
                        self._y + self._knob_pos[1])
        knob_image_pos_with_offset = (global_k_pos[0] - int(self._knob.get_rect().width/2),
                                      global_k_pos[1] - int(self._knob.get_rect().height/2))
        surface.blit(self._knob, knob_image_pos_with_offset)
        pygame.draw.rect(screen, self._knob_color, pygame.Rect((global_k_pos[0] - int(self._knob_center_size[0]/2),
                                                                global_k_pos[1] - int(self._knob_center_size[1]/2)),
                                                                self._knob_center_size))
    def get_color(self) -> tuple:
        return (self._color.r, self._color.g, self._color.b)

def wndProc(oldWndProc, draw_callback, hWnd, message, wParam, lParam):
    '''sloth's solution from stackoverflow on how to remove graphic bugs while resizing the window'''
    if message == win32con.WM_SIZE:
        draw_callback()
        win32gui.RedrawWindow(hWnd, None, None, win32con.RDW_INVALIDATE | win32con.RDW_ERASE)
    return win32gui.CallWindowProc(oldWndProc, hWnd, message, wParam, lParam)

def init_surfaces_with_current_resolution(resolution:tuple, is_first_init:bool):
    '''Resizing the window brings the need to re-initialize all surfaces, that were created.'''
    global screen, manager
    screen = pygame.display.set_mode(resolution, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SRCALPHA | pygame.RESIZABLE)
    if is_first_init:
        manager = pygame_gui.UIManager(resolution)
    else:
        manager.set_window_resolution(resolution)
        #manager.clear_and_reset()

def render():
    screen.fill((235, 226, 192))
    # Canvas
    canvas.render(screen)
    cp.render(screen)
    pencil_size = canvas._width / canvas._columns
    if not pygame.mouse.get_visible():
        pygame.draw.rect(screen, BLACK, pygame.Rect((mp[0] - pencil_size/2 - 1, mp[1] - pencil_size/2 - 1), (pencil_size + 2, pencil_size + 2)), 1)
        pygame.draw.rect(screen, WHITE, pygame.Rect((mp[0] - pencil_size/2, mp[1] - pencil_size/2), (pencil_size, pencil_size)), 1)
        #pygame.draw.rect(screen, WHITE, pygame.Rect((mp[0] - pencil_size/2 + 1, mp[1] - pencil_size/2 + 1), (pencil_size - 2, pencil_size - 2)), 1)
    manager.update(time_delta)
    manager.draw_ui(screen)
    pygame.display.flip() # use update() if I only want to update specific surfaces.

# INIT
pygame.init()
pygame.display.set_caption("Pyxel v0.1")
screen = None
manager = None
init_surfaces_with_current_resolution(SIZE_ON_STARTUP, True)
oldWndProc = win32gui.SetWindowLong(win32gui.GetForegroundWindow(), win32con.GWL_WNDPROC, lambda *args: wndProc(oldWndProc, render, *args))
# TODO: Some of the following line are better handled in the init_surfaces funciton
button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 0), (100, 50)), text='Save Image', manager=manager)
canvas = Canvas(10, 60, 300, 300, 15, 15)
cp = ColorPicker(330, 210, 150, 15, 20)
clock = pygame.time.Clock()
is_running = True
is_drawing = False
#is_mouse_down = False
mp = (0, 0)
selected_tool = Tool.PENCIL

# MAINLOOP
while is_running:
    time_delta = clock.tick(60)/1000.0

    # EVENTS
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        # Mouse position
        mp = pygame.mouse.get_pos()
        if canvas.get_rect().collidepoint(mp):
            pygame.mouse.set_visible(False)
        else:
            pygame.mouse.set_visible(True)
        # Drawing on a canvas
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Left mouse button
            if event.button == 1:
                is_drawing = True
                #is_mouse_down = True
                if cp.get_picker_rect().collidepoint(event.pos):
                    cp.is_picking = True
                if cp.get_slider_rect().collidepoint(event.pos):
                    cp.is_sliding = True
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                is_drawing = False
                #is_mouse_down = False
                cp.is_picking = False
                cp.is_sliding = False
        # UI events
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == button:
                print("Saving image!")
                canvas.save_image()
        # Window resize
        if event.type == pygame.VIDEORESIZE:
            window_size = (event.w, event.h)
            init_surfaces_with_current_resolution(window_size, False)
        manager.process_events(event)
    
    # COMPUTING
    if is_drawing:
        canvas.set(mp, cp.get_color()) #TODO: layer support
    if cp.is_picking:
        cp.move_picker(cp.s2picker(mp))
    if cp.is_sliding:
        cp.move_slider(cp.s2slider(mp))

    # RENDERING
    render()

# QUIT PYGAME
pygame.quit()