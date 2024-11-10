from os import environ, system
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
from pygame import init, quit, display, font, time, draw, Rect, Surface, event, QUIT, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE
from importlib import reload
from copy import deepcopy
from necklaces import read_binary_strings, run_necklaces_exe
import symbols

SCALE = 0.88

BLACK, WHITE = (0, 0, 0), (235, 235, 235)
MAIN_BG, LEFT_REGION_BG = (33, 33, 33), (22, 22, 22)
LABEL_TEXT_COLOR = (170, 170, 170)
SELECTOR_TEXT_COLOR, SELECTOR_BG = (190, 190, 190), (50, 50, 50)
ENABLED_WHITE = (200, 201, 200)
SLIDER_COLOR, SLIDER_BG = (218, 194, 195), (70, 70, 70)
GENERATE_BUTTON_COLOR, GENERATE_BUTTON_BG = (210, 210, 210), (17, 17, 17)
BLUE, SELECTED_BG, GRID_LINES_COLOR = (0, 100, 255), (41, 37, 5), (60, 60, 60)

CHARACTERS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
CHAR_TO_VALUE = {char: index for index, char in enumerate(CHARACTERS)}
def base62_to_int(b62_str):
    return sum(CHAR_TO_VALUE[char] * (62 ** i) for i, char in enumerate(reversed(b62_str)))

def generate_chords(edo):
    chord_sizes = []
    chord_states = []
    for density in range(edo+1):
        run_necklaces_exe(2, edo, density)
        binary_strings = read_binary_strings('binaries.bin', edo, density)
        binary_strings = [x[::-1] for x in binary_strings]
        chord_sizes.append(sorted(set(binary_strings), key=lambda x: int(x[::-1], 2)))
        chord_states.append([False for _ in chord_sizes[-1]])
    return chord_sizes, chord_states

class ChordSizeSelector:
    def __init__(self):
        init()
        self.setup()
        self.generate_chord_sizes()

    def setup(self):
        self.SELECTOR_HEIGHT, self.CHAR_WIDTH = round(SCALE * 31), round(SCALE * 20)
        self.MARGIN, self.LABEL_HEIGHT = round(SCALE * 13), round(SCALE * 19)
        self.REGION_HEIGHT, self.MIN_BUTTON_WIDTH = round(SCALE * 39), round(SCALE * 26)
        self.TOP_MARGIN, self.BOTTOM_MARGIN = round(SCALE * 4), round(SCALE * 27)
        self.BINARY_SQUARE_SIZE, self.SLIDER_HEIGHT = round(SCALE * 17), round(SCALE * 11)
        font_path = 'assets/JetBrainsMono-Light.otf'
        self.fonts = {'main': font.Font(font_path, round(SCALE * 34)),
                      'label': font.Font(font_path, round(SCALE * 16)),
                      'selector': font.Font(font_path, round(SCALE * 25)),
                      'print': font.Font(font_path, round(SCALE * 23))}
        self.labels = ["edo", "shapes", "rotations", "interval variations",
                       "filter shapes", "filter rotations", "filter interval variations"]
        self.selector_panel = {"buttons": list(CHARACTERS[:21]), "rects": [], "selected": 12}
        self.calculate_window_size()
        self.screen = display.set_mode((self.width, self.height))
        display.set_caption("chord selector v0.3")
        self.regions = self.create_regions()
        self.create_buttons()
        self.drag_state = {'dragging': False,'start': None,'end': None,'active_region': None,'binary_drag': False,'initial_binary_states': None}
        self.symbols = []
        self.slider_positions = {1: None, 4: None}
        self.scroll = {'offset': 0, 'max_offset': 0, 'velocity': 0, 'deceleration': 0.8}
        self.binary_surface = None
        self.binary_surface_height = 0
        self.slider_last_moved = {1: 0, 4: 0}

    def calculate_window_size(self):
        edo = base62_to_int(self.selector_panel["buttons"][self.selector_panel["selected"]])
        self.left_region_width = edo * self.BINARY_SQUARE_SIZE - 1
        selector_width = len(self.selector_panel["buttons"]) * self.CHAR_WIDTH
        toggleable_width = (self.selector_panel["selected"] + 1) * self.MIN_BUTTON_WIDTH
        self.width = max(self.left_region_width + selector_width, self.left_region_width + toggleable_width, self.left_region_width + 200)
        self.height = 7 * (self.REGION_HEIGHT + self.LABEL_HEIGHT) + 8 * self.MARGIN + self.BOTTOM_MARGIN
        self.update_selector_rects()

    def update_selector_rects(self):
        self.selector_panel["rects"] = [Rect(self.left_region_width + i * self.CHAR_WIDTH, self.TOP_MARGIN + self.LABEL_HEIGHT, 
                                                    self.CHAR_WIDTH, self.SELECTOR_HEIGHT) for i in range(len(self.selector_panel["buttons"]))]

    def create_regions(self):
        regions = []
        region_width = (self.selector_panel["selected"] + 1) * self.MIN_BUTTON_WIDTH
        for i, label in enumerate(self.labels):
            x, y = self.left_region_width, i * (self.REGION_HEIGHT + self.LABEL_HEIGHT + self.MARGIN) + self.TOP_MARGIN
            if i == 0:
                regions.append({"buttons": self.selector_panel["buttons"], "rects": self.selector_panel["rects"],
                                "rect": Rect(x, y + self.LABEL_HEIGHT, 0, 0), "label": label, "is_top_bar": True})
            else:
                adjusted_width = region_width - (0 if i in [1, 4] else self.MIN_BUTTON_WIDTH)
                region = self.create_region(x, y, adjusted_width, label, i in [1, 4], i in [2, 5])
                if i in [1, 4]:
                    region["slider_rect"] = Rect(x, y + self.LABEL_HEIGHT + self.REGION_HEIGHT, adjusted_width, self.SLIDER_HEIGHT)
                regions.append(region)
        return regions

    def create_region(self, x, y, width, label, is_extended, is_rotations):
        button_labels = self.selector_panel["buttons"][:self.selector_panel["selected"] + (1 if is_extended else 0)]
        button_width = width // len(button_labels)
        buttons = [{"rect": Rect(x + i * button_width, y + self.LABEL_HEIGHT, button_width, self.REGION_HEIGHT),
                    "label": button_label,
                    "enabled": (is_rotations and (i < 1))} for i, button_label in enumerate(button_labels)]
        return {"buttons": buttons, "rect": Rect(x, y + self.LABEL_HEIGHT, width, self.REGION_HEIGHT), "label": label, "is_top_bar": False}

    def create_buttons(self):
        button_margin = 0 # round(SCALE * 2)
        y = self.height - self.BOTTOM_MARGIN
        self.buttons = {}
        labels = ["r", "i", "and", "all", "generate"]
        widths = [self.fonts['print'].render(label, True, WHITE).get_width()+round(SCALE*7) for label in labels]
        start_x = self.left_region_width + button_margin
        for i, label in enumerate(labels[:4]):
            rect = Rect(start_x, y, widths[i], self.fonts['print'].get_height()-round(SCALE*3))
            self.buttons[label] = {"rect": rect, "enabled": False, "label": label}
            start_x += widths[i] + button_margin
        generate_rect = Rect(self.width - widths[4] - button_margin, y, widths[4], self.fonts['print'].get_height()-round(SCALE*3))
        self.buttons["generate"] = {"rect": generate_rect, "label": "generate"}

    def draw(self):
        self.screen.fill(MAIN_BG)
        draw.rect(self.screen, LEFT_REGION_BG, Rect(0, 0, self.left_region_width, self.height))
        self.draw_persistent_binaries()
        for region in self.regions:
            self.draw_region(region)
        self.draw_buttons()
        display.flip()

    def draw_persistent_binaries(self):
        edo = base62_to_int(self.regions[0]["buttons"][self.selector_panel["selected"]])
        top_time = self.slider_last_moved[1]
        bottom_time = self.slider_last_moved[4]
        if top_time > bottom_time:
            rows = [1, 4]
        else:
            rows = [4, 1]
        for row in rows:
            if self.slider_positions[row] is not None:
                button_index = self.slider_positions[row]
                chord_states = self.chord_states1 if row == 1 else self.chord_states2
                self.draw_binaries(self.chord_sizes[button_index], chord_states[button_index], edo)
                return
        if self.symbols:
            self.draw_binaries(self.symbols, [False] * len(self.symbols), edo)

    def draw_binaries(self, binaries, states, edo):
        visible_height = self.height
        total_height = len(binaries) * self.BINARY_SQUARE_SIZE
        self.scroll['max_offset'] = max(0, total_height - visible_height)
        if self.binary_surface is None or self.binary_surface_height != total_height:
            self.binary_surface = Surface((self.left_region_width, total_height))
            self.binary_surface_height = total_height
        self.binary_surface.fill(BLACK)
        start_index = max(0, int(self.scroll['offset'] // self.BINARY_SQUARE_SIZE))
        end_index = min(len(binaries), int((self.scroll['offset'] + visible_height) // self.BINARY_SQUARE_SIZE) + 1)
        for i in range(start_index, end_index):
            binary = binaries[i]
            y = i * self.BINARY_SQUARE_SIZE - int(self.scroll['offset'])
            in_drag_selection = False
            should_be_selected = states[i]
            if self.drag_state['binary_drag'] and self.drag_state['current_range']:
                drag_start, drag_end = self.drag_state['current_range']
                in_drag_selection = drag_start <= i <= drag_end
                if in_drag_selection:
                    should_be_selected = self.drag_state['toggle_to']
                else:
                    should_be_selected = states[i]
            if should_be_selected:
                draw.rect(self.binary_surface, SELECTED_BG, 
                        Rect(0, y, self.left_region_width, self.BINARY_SQUARE_SIZE))
            for j, bit in enumerate(binary):
                if bit == '1':
                    color = BLUE if should_be_selected else ENABLED_WHITE
                    draw.rect(self.binary_surface, color, 
                            Rect(j * self.BINARY_SQUARE_SIZE, y, self.BINARY_SQUARE_SIZE - 1, self.BINARY_SQUARE_SIZE))
        for i in range(start_index + 1, end_index):
            y = i * self.BINARY_SQUARE_SIZE - int(self.scroll['offset'])
            draw.line(self.binary_surface, GRID_LINES_COLOR, (0, y), (self.left_region_width, y))
        for i in range(1, edo):
            x = i * self.BINARY_SQUARE_SIZE - 1
            draw.line(self.binary_surface, GRID_LINES_COLOR, (x, 0), (x, visible_height))
        self.screen.blit(self.binary_surface, (0, 0))
        if total_height < visible_height:
            draw.rect(self.screen, LEFT_REGION_BG, 
                    Rect(0, total_height, self.left_region_width, visible_height - total_height))

    def draw_region(self, region):
        label_surf = self.fonts['label'].render(region["label"], True, LABEL_TEXT_COLOR)
        label_rect = label_surf.get_rect(topleft=(self.left_region_width, region["rect"].top - self.LABEL_HEIGHT))
        self.screen.blit(label_surf, label_rect)
        if region["is_top_bar"]:
            self.draw_top_bar(region)
        else:
            self.draw_buttons_region(region)
            if region["label"] in ["shapes", "filter shapes"]:
                self.draw_slider(region)

    def draw_top_bar(self, region):
        for j, (char, rect) in enumerate(zip(region["buttons"], region["rects"])):
            color = ENABLED_WHITE if j == self.selector_panel["selected"] else SELECTOR_BG
            draw.rect(self.screen, color, rect)
            text_surf = self.fonts['selector'].render(char, True, BLACK if j == self.selector_panel["selected"] else SELECTOR_TEXT_COLOR)
            text_rect = text_surf.get_rect(center=(rect.centerx, rect.centery))
            self.screen.blit(text_surf, text_rect)

    def draw_buttons_region(self, region):
        for i, button in enumerate(region["buttons"]):
            if self.drag_state['dragging'] and self.drag_state['active_region'] == region and self.is_in_drag_range(button["rect"].centerx):
                bg_color = ENABLED_WHITE if not self.initial_states[i] else BLACK
                text_color = BLACK if not self.initial_states[i] else WHITE
            else:
                bg_color = ENABLED_WHITE if button["enabled"] else BLACK
                text_color = BLACK if button["enabled"] else WHITE
            draw.rect(self.screen, bg_color, button["rect"])
            text_surf = self.fonts['main'].render(button["label"], True, text_color)
            text_rect = text_surf.get_rect(center=button["rect"].center)
            self.screen.blit(text_surf, text_rect)

    def draw_slider(self, region):
        row = 1 if region["label"] == "shapes" else 4
        chord_states = self.chord_states1 if row == 1 else self.chord_states2
        for i, button in enumerate(region["buttons"]):
            chord_size = base62_to_int(button["label"])
            any_chord_true = any(chord_states[chord_size]) if chord_size < len(chord_states) else False
            slider_x = region["slider_rect"].left + i * region["slider_rect"].width // len(region["buttons"])
            slider_width = region["slider_rect"].width // len(region["buttons"])
            slider_color = BLUE if any_chord_true else SLIDER_BG
            draw.rect(self.screen, slider_color, Rect(slider_x, region["slider_rect"].top, slider_width, region["slider_rect"].height))
        if self.slider_positions[row] is not None:
            slider_x = region["slider_rect"].left + self.slider_positions[row] * region["slider_rect"].width // len(region["buttons"])
            slider_width = region["slider_rect"].width // len(region["buttons"])
            draw.rect(self.screen, SLIDER_COLOR, Rect(slider_x, region["slider_rect"].top, slider_width, region["slider_rect"].height))

    def draw_buttons(self):
        text_offset_y = round(SCALE * -1)
        for button_name, button in self.buttons.items():
            bg_color = GENERATE_BUTTON_BG if button_name == "generate" else (ENABLED_WHITE if button.get("enabled", False) else BLACK)
            text_color = GENERATE_BUTTON_COLOR if button_name == "generate" else (BLACK if button.get("enabled", False) else WHITE)
            draw.rect(self.screen, bg_color, button["rect"])
            label = button["label"]
            if button_name == "and":
                label = "and" if button.get("enabled", False) else "or"
            elif button_name == "all":
                label = "all" if button.get("enabled", False) else "any"
            text_surf = self.fonts['print'].render(label, True, text_color)
            text_rect = text_surf.get_rect()
            text_rect.centerx = button["rect"].centerx
            text_rect.centery = button["rect"].centery + text_offset_y
            self.screen.blit(text_surf, text_rect)

    def handle_events(self):
        for e in event.get():
            if e.type == QUIT:
                return False
            elif e.type == MOUSEBUTTONDOWN:
                if e.button == 1:
                    self.handle_mouse_down(e.pos)
                elif e.button == 4:  # scroll up
                    self.scroll['velocity'] -= 30
                elif e.button == 5:  # scroll down
                    self.scroll['velocity'] += 30
            elif e.type == MOUSEBUTTONUP and e.button == 1:
                self.handle_mouse_up(e.pos)
            elif e.type == MOUSEMOTION and e.buttons[0]:
                self.handle_mouse_drag(e.pos)
            elif e.type == VIDEORESIZE:
                self.handle_resize(e.size)
        self.update_scroll()
        self.draw()
        return True

    def handle_mouse_down(self, pos):
        self.drag_state['start'] = pos
        if self.handle_selector_click(pos) or self.handle_region_click(pos) or self.handle_slider_click(pos) or self.handle_binary_click(pos) or self.handle_button_click(pos):
            return

    def handle_selector_click(self, pos):
        for i, rect in enumerate(self.selector_panel["rects"]):
            if rect.collidepoint(pos):
                if self.selector_panel["selected"] != i:
                    self.selector_panel["selected"] = i
                    self.clear_binary_display()
                    self.update_layout()
                    self.generate_chord_sizes()
                return True
        return False

    def handle_region_click(self, pos):
        for region in self.regions:
            if region["rect"].collidepoint(pos) and not region["is_top_bar"]:
                self.drag_state['active_region'] = region
                self.initial_states = [button["enabled"] for button in region["buttons"]]
                return True
        return False

    def handle_slider_click(self, pos):
        for region in self.regions:
            if region["label"] in ["shapes", "filter shapes"]:
                row = 1 if region["label"] == "shapes" else 4
                if region["slider_rect"].collidepoint(pos):
                    self.drag_state['dragging_slider'] = row
                    self.handle_slider_drag(pos, row)
                    return True
        return False

    def handle_binary_click(self, pos):
        if pos[0] >= self.left_region_width:
            return False
        top_time = self.slider_last_moved[1]
        bottom_time = self.slider_last_moved[4]
        rows = [1, 4] if top_time > bottom_time else [4, 1]
        for row in rows:
            if self.slider_positions[row] is not None:
                button_index = self.slider_positions[row]
                binaries = self.chord_sizes[button_index]
                chord_states = self.chord_states1 if row == 1 else self.chord_states2
                click_y = pos[1] + self.scroll['offset']
                binary_index = int(click_y // self.BINARY_SQUARE_SIZE)
                if 0 <= binary_index < len(binaries):
                    self.drag_state['binary_drag'] = True
                    self.drag_state['start'] = pos
                    self.drag_state['initial_binary_states'] = chord_states[button_index].copy()
                    self.drag_state['toggle_to'] = not chord_states[button_index][binary_index]
                    self.drag_state['current_range'] = (binary_index, binary_index)
                    self.drag_state['active_row'] = row
                    self.drag_state['active_button_index'] = button_index
                    return True
        return False
    
    def handle_binary_drag(self, pos):
        if not self.drag_state['binary_drag']:
            return
        top_time = self.slider_last_moved[1]
        bottom_time = self.slider_last_moved[4]
        rows = [1, 4] if top_time > bottom_time else [4, 1]
        for row in rows:
            if self.slider_positions[row] is not None:
                start_y = self.drag_state['start'][1] + self.scroll['offset']
                end_y = pos[1] + self.scroll['offset']
                self.drag_state['current_range'] = (
                    int(min(start_y, end_y) // self.BINARY_SQUARE_SIZE),
                    int(max(start_y, end_y) // self.BINARY_SQUARE_SIZE)
                )
                return

    def apply_binary_drag(self):
        if self.drag_state['current_range'] is None:
            return
        row = self.drag_state['active_row']
        button_index = self.drag_state['active_button_index']
        chord_states = self.chord_states1 if row == 1 else self.chord_states2
        start_index, end_index = self.drag_state['current_range']
        binaries = self.chord_sizes[button_index]
        start_index = max(0, min(start_index, len(binaries) - 1))
        end_index = max(0, min(end_index, len(binaries) - 1))
        toggle_to = self.drag_state['toggle_to']
        for i in range(start_index, end_index + 1):
            chord_states[button_index][i] = toggle_to

    def handle_button_click(self, pos):
        for button_name, button in self.buttons.items():
            if button["rect"].collidepoint(pos):
                if button_name == "generate":
                    self.print_all_enabled()
                elif button_name in ["r", "i", "and", "all"]:
                    button["enabled"] = not button.get("enabled", False)
                    self.print_all_enabled()
                else:
                    button["enabled"] = not button.get("enabled", False)
                return True
        return False

    def handle_mouse_up(self, pos):
        if self.drag_state['binary_drag']:
            self.apply_binary_drag()
        elif self.drag_state['dragging'] and self.drag_state['active_region']:
            self.apply_drag_selection()
        elif self.drag_state['start'] == pos:
            self.handle_click(pos)
        self.reset_drag_state()

    def handle_click(self, pos):
        for region in self.regions:
            if region["rect"].collidepoint(pos) and not region["is_top_bar"]:
                for button in region["buttons"]:
                    if button["rect"].collidepoint(pos):
                        button["enabled"] = not button["enabled"]
                        return

    def handle_mouse_drag(self, pos):
        if self.drag_state.get('dragging_slider') is not None:
            self.handle_slider_drag(pos, self.drag_state['dragging_slider'])
        elif self.drag_state['binary_drag']:
            self.handle_binary_drag(pos)
        elif not self.drag_state['dragging'] and self.drag_state['active_region']:
            if abs(pos[0] - self.drag_state['start'][0]) > 5 or abs(pos[1] - self.drag_state['start'][1]) > 5:
                self.drag_state['dragging'] = True
        if self.drag_state['dragging']:
            self.drag_state['end'] = pos
            
    def handle_slider_drag(self, pos, row):
        region = self.regions[row]
        relative_x = pos[0] - region["slider_rect"].left
        total_width = region["slider_rect"].width
        num_buttons = len(region["buttons"])
        button_index = max(0, min(num_buttons-1, int(relative_x * num_buttons / total_width)))
        if 0 <= relative_x < total_width:
            self.slider_positions[row] = button_index
            self.slider_last_moved[row] = time.get_ticks()
            self.scroll['offset'] = 0
            self.scroll['velocity'] = 0
            self.binary_surface = None
        else:
            self.slider_positions[row] = None

    def handle_resize(self, size):
        self.width, self.height = size
        edo = base62_to_int(self.regions[0]["buttons"][self.selector_panel["selected"]])
        self.left_region_width = edo * self.BINARY_SQUARE_SIZE
        self.width = max(self.width, self.left_region_width + len(self.selector_panel["buttons"]) * self.CHAR_WIDTH)
        self.screen = display.set_mode((self.width, self.height))
        self.update_layout()
        self.binary_surface = None

    def apply_drag_selection(self):
        if self.drag_state['active_region'] and not self.drag_state['active_region']["is_top_bar"]:
            for i, button in enumerate(self.drag_state['active_region']["buttons"]):
                if self.is_in_drag_range(button["rect"].centerx):
                    button["enabled"] = not self.initial_states[i]

    def is_in_drag_range(self, x):
        if self.drag_state['start'] is None or self.drag_state['end'] is None:
            return False
        start_x, end_x = sorted([self.drag_state['start'][0], self.drag_state['end'][0]])
        return start_x <= x <= end_x

    def reset_drag_state(self):
        self.drag_state = {
            'dragging': False,'start': None,'end': None,'active_region': None,'binary_drag': False,'initial_binary_states': None,
            'current_range': None,'toggle_to': None,'active_row': None,'active_button_index': None}

    def clear_binary_display(self):
        self.symbols = []
        self.slider_positions = {1: None, 4: None}
        self.slider_last_moved = {1: 0, 4: 0}
        self.scroll['offset'] = 0
        self.scroll['velocity'] = 0
        self.binary_surface = None

    def print_all_enabled(self):
        self.clear_binary_display()
        edo = base62_to_int(self.regions[0]["buttons"][self.selector_panel["selected"]])
        settings = {
            "EDO": edo,
            "ALL_UNIQUE_BINARIES1": [base62_to_int(b["label"]) for b in self.regions[1]["buttons"] if b["enabled"]],
            "ROTATIONS1": [base62_to_int(b["label"]) for b in self.regions[2]["buttons"] if b["enabled"]],
            "INTERVAL_VARIATIONS1": [base62_to_int(b["label"]) for b in self.regions[3]["buttons"] if b["enabled"]],
            "ALL_UNIQUE_BINARIES2": [base62_to_int(b["label"]) for b in self.regions[4]["buttons"] if b["enabled"]],
            "ROTATIONS2": [base62_to_int(b["label"]) for b in self.regions[5]["buttons"] if b["enabled"]],
            "INTERVAL_VARIATIONS2": [base62_to_int(b["label"]) for b in self.regions[6]["buttons"] if b["enabled"]],
            "SPECIFIC_CHORDS1": [(i, j) for i, chord_set in enumerate(self.chord_states1) for j, is_selected in enumerate(chord_set) if is_selected],
            "SPECIFIC_CHORDS2": [(i, j) for i, chord_set in enumerate(self.chord_states2) for j, is_selected in enumerate(chord_set) if is_selected],
            "REDUCE_FINAL_SET": self.buttons["r"]["enabled"],
            "FILTER_INVERTED": self.buttons["i"]["enabled"],
            "FILTER_GATE_AND": self.buttons["and"]["enabled"],
            "FILTER_ALL": self.buttons["all"]["enabled"]}
        with open("settings.py", "w") as f:
            for key, value in settings.items():
                f.write(f"{key} = {value}\n")
        system("python necklaces.py")
        reload(symbols)
        self.symbols = symbols.SYMBOLS

    def update_layout(self):
        self.calculate_window_size()
        self.update_selector_rects()
        self.regions = self.create_regions()
        self.create_buttons()
        self.screen = display.set_mode((self.width, self.height))
        self.draw()

    def generate_chord_sizes(self):
        edo = base62_to_int(self.regions[0]["buttons"][self.selector_panel["selected"]])
        self.chord_sizes, self.chord_states1 = generate_chords(edo)
        self.chord_states2 = deepcopy(self.chord_states1)

    def update_scroll(self):
        self.scroll['offset'] += self.scroll['velocity']
        self.scroll['velocity'] *= self.scroll['deceleration']
        if abs(self.scroll['velocity']) < 0.1:
            self.scroll['velocity'] = 0
        self.scroll['offset'] = max(0, min(self.scroll['offset'], self.scroll['max_offset']))
        if self.scroll['offset'] <= 0:
            self.scroll['offset'], self.scroll['velocity'] = 0, 0
        elif self.scroll['offset'] >= self.scroll['max_offset']:
            self.scroll['offset'], self.scroll['velocity'] = self.scroll['max_offset'], 0

    def run(self):
        clock = time.Clock()
        running = True
        while running:
            running = self.handle_events()
            clock.tick(60)
        quit()

if __name__ == "__main__":
    ChordSizeSelector().run()