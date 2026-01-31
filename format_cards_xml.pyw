import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import xml.etree.ElementTree as ET
from typing import NamedTuple

class Card(NamedTuple):
    name: str
    rarity: str
    colors: str
    manacost: str
    cmc: int
    type: str
    maintype: str
    pt: str  # power/toughness, empty for non-creatures
    text: str

def parse_cards(xml_path: str) -> list[Card]:
    with open(xml_path, "r", encoding="utf-8") as f:
        tree = ET.parse(f)
    root = tree.getroot()

    cards = []
    for card_elem in root.findall(".//card"):
        name = card_elem.findtext("name", "")

        set_elem = card_elem.find("set")
        rarity = set_elem.get("rarity", "") if set_elem is not None else ""

        props = card_elem.find("prop")
        if props is not None:
            colors = props.findtext("colors", "")
            manacost = props.findtext("manacost", "")
            cmc = int(props.findtext("cmc", "0") or "0")
            card_type = props.findtext("type", "")
            maintype = props.findtext("maintype", "")
            pt = props.findtext("pt", "")
        else:
            colors = manacost = card_type = maintype = pt = ""
            cmc = 0

        text = card_elem.findtext("text", "")

        cards.append(Card(
            name=name,
            rarity=rarity,
            colors=colors,
            manacost=manacost,
            cmc=cmc,
            type=card_type,
            maintype=maintype,
            pt=pt,
            text=text,
        ))

    return cards

def format_card(card: Card) -> str:
    lines = []
    # Name and mana cost
    if card.manacost:
        lines.append(f"{card.name} {card.manacost}")
    else:
        lines.append(card.name)
    # Type line
    lines.append(card.type.strip())
    # Rarity
    if card.rarity:
        lines.append(card.rarity.title())
    # Rules text
    if card.text:
        lines.append(card.text)
    # Power/toughness for creatures
    if card.pt:
        lines.append(card.pt)
    return "\n".join(lines)

def print_card(card: Card) -> None:
    print(format_card(card))
    print()

COLOR_ORDER = ["W", "U", "B", "R", "G"]
RARITY_ORDER = ["common", "uncommon", "rare", "mythic"]

COLOR_NAMES = {
    "W": "White",
    "U": "Blue",
    "B": "Black",
    "R": "Red",
    "G": "Green",
}

def card_sort_key(card: Card) -> tuple:
    # Lands last, then single colors in WUBRG order, then multicolor, then colorless
    if card.maintype == "Land":
        color_key = (3, 0)  # Lands
    elif len(card.colors) == 1 and card.colors in COLOR_ORDER:
        color_key = (0, COLOR_ORDER.index(card.colors))
    elif len(card.colors) > 1:
        color_key = (1, 0)  # Multicolor
    else:
        color_key = (2, 0)  # Colorless

    rarity = card.rarity.lower()
    if rarity in RARITY_ORDER:
        rarity_key = RARITY_ORDER.index(rarity)
    else:
        rarity_key = len(RARITY_ORDER)

    return (color_key, rarity_key, card.name)

def get_color_header(card: Card) -> str:
    if card.maintype == "Land":
        return "Land"
    colors = card.colors
    if len(colors) == 1 and colors in COLOR_NAMES:
        return COLOR_NAMES[colors]
    elif len(colors) > 1:
        return "Multicolor"
    else:
        return "Colorless"

def format_cards_with_headers(cards: list[Card]) -> str:
    sorted_cards = sorted(cards, key=card_sort_key)
    sections = []
    current_color = None

    for card in sorted_cards:
        color_header = get_color_header(card)
        if color_header != current_color:
            current_color = color_header
            sections.append(f"=== {color_header} ===")
        sections.append(format_card(card))

    return "\n\n".join(sections)

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Card XML Formatter")

        self.input_path = ""
        self.output_path = ""

        # Input file selection
        input_frame = tk.Frame(root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(input_frame, text="Select Input XML", command=self.select_input).pack(side=tk.LEFT)
        self.input_label = tk.Label(input_frame, text="No file selected", anchor="w")
        self.input_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Output file selection
        output_frame = tk.Frame(root)
        output_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(output_frame, text="Select Output File", command=self.select_output).pack(side=tk.LEFT)
        self.output_label = tk.Label(output_frame, text="No file selected", anchor="w")
        self.output_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Save to File", command=self.convert).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Copy to Clipboard", command=self.copy_to_clipboard).pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_label = tk.Label(root, text="")
        self.status_label.pack(pady=5)

    def select_input(self):
        path = filedialog.askopenfilename(
            title="Select Input XML",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if path:
            self.input_path = path
            self.input_label.config(text=path)

    def select_output(self):
        path = filedialog.asksaveasfilename(
            title="Select Output File",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            self.output_path = path
            self.output_label.config(text=path)

    def convert(self):
        if not self.input_path:
            messagebox.showerror("Error", "Please select an input file")
            return
        if not self.output_path:
            messagebox.showerror("Error", "Please select an output file")
            return

        try:
            cards = parse_cards(self.input_path)
            output = format_cards_with_headers(cards)
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(output)
                f.write("\n")
            self.status_label.config(text=f"Converted {len(cards)} cards!")
            messagebox.showinfo("Success", f"Converted {len(cards)} cards to {self.output_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def copy_to_clipboard(self):
        if not self.input_path:
            messagebox.showerror("Error", "Please select an input file")
            return

        try:
            cards = parse_cards(self.input_path)
            output = format_cards_with_headers(cards)
            self.root.clipboard_clear()
            self.root.clipboard_append(output)
            self.status_label.config(text=f"Copied {len(cards)} cards to clipboard!")
            messagebox.showinfo("Success", f"Copied {len(cards)} cards to clipboard")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = App(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Startup Error", str(e))
