import json
from typing import List


class Section:
    def __init__(self, element, level=0):
        self.heading = element
        self.children = []
        self.level = None
        self.set_level(level)

    def set_level(self, level):
        self.level = level

    def to_dict(self):
        heading_text = self.heading.text if self.heading else ""
        heading_style = (
            self.heading.style.to_dict() if self.heading and self.heading.style else {}
        )
        return {
            "heading": {
                "text": heading_text,
                "style": heading_style,
                "tokens": getattr(self.heading, "tokens", []),
                "word_bbox": getattr(self.heading, "word_bbox", []),
            },
            "children": [child.to_dict() for child in self.children],
            "level": self.level,
        }


def serialize_section(obj):
    if isinstance(obj, Section):
        return obj.to_dict()
    raise TypeError("Type not serializable")


class TextElement:
    def __init__(self, text, style, bbox, tokens, word_bbox):
        self.text = text
        self.style = style
        self.bbox = bbox
        self.tokens = tokens
        self.word_bbox = word_bbox


class Style:
    def __init__(self, font, size, color, flags):
        self.font = font
        self.size = size
        self.color = color
        self.flags = flags

    def to_dict(self):
        return {
            "font": self.font,
            "size": self.size,
            "color": self.color,
            "flags": self.flags,
        }


class DanglingTextSection(Section):
    def __init__(self):
        super().__init__(element=None)

    def __str__(self):
        return "{}".format(" ".join([str(e) for e in self.content]))


# now this basically convert each list element into this form of
# text_element we defined abive.


def convert_to_text_elements(element_data):
    lines = element_data["lines"]
    text_elements = []

    for line in lines:
        spans = line["spans"][0]
        text_element = TextElement(
            text=spans["text"],
            style=Style(
                font=spans["font"],
                size=spans["size"],
                color=spans["color"],
                flags=spans["flags"],
            ),
            bbox=line["bbox"],
            tokens=line["tokens"],
            word_bbox=line["word_bbox"],
        )
        text_elements.append(text_element)

    return text_elements


def create_hierarchy(
    extracted_data: List[dict], style_distribution: dict
) -> List[Section]:
    structured = []
    level_stack = []

    for element_data in extracted_data:
        text_elements = convert_to_text_elements(element_data)

        for text_element in text_elements:  # 5
            style = text_element.style

            if header_detector(text_element, style_distribution):
                child = Section(text_element)
                child.set_level(len(level_stack))
                header_size = style.size

                if not level_stack:
                    __push_to_stack(child, level_stack, structured)
                    continue

                stack_peek_size = level_stack[-1].heading.style.size

                if stack_peek_size > header_size:
                    __push_to_stack(child, level_stack, structured)

                else:
                    __pop_stack_until_match(level_stack, header_size, child)
                    __push_to_stack(child, level_stack, structured)

            else:
                content_node = Section(text_element, level=len(level_stack))
                if level_stack:
                    level_stack[-1].children.append(content_node)
                else:
                    if structured and isinstance(structured[-1], DanglingTextSection):
                        structured[-1].children.append(content_node)
                    else:
                        dangling_content = DanglingTextSection()
                        dangling_content.children.append(content_node)
                        dangling_content.set_level(len(level_stack))
                        structured.append(dangling_content)

    return structured


def header_detector(element, style_distribution):
    """
    Sample header detection logic based on font size, bold, and italic properties.
    You may need to adjust this based on your specific data characteristics.
    """
    # Check if the font size is greater than the body size
    if element.style.size > (style_distribution["_body_size"] + 1):
        # Check for bold and italic conditions using flags property
        if element.style.flags & 2**1:  # Check for italic (bit 1)
            return True

        if element.style.flags & 2**4:  # Check for bold (bit 4)
            return True

    return False


def _is_sub_header(poped, header_to_test):
    """
    Sample logic to check if header_to_test is a sub-header of poped element within stack.
    """
    poped_font_size = poped.heading.style.size
    header_to_test_font_size = header_to_test.heading.style.size

    # Check if the font size of header_to_test is smaller than the poped header
    # You may need additional conditions based on your specific requirements
    return header_to_test_font_size < poped_font_size


def __pop_stack_until_match(stack, header_size, header):
    while __top_has_no_header(stack) or __should_pop_higher_level(stack, header):
        poped = stack.pop()
        if poped.heading.style.size == header_size:
            if _is_sub_header(poped, header):
                stack.append(poped)
                return


def __push_to_stack(child, stack, output):
    if stack:
        child.level = len(stack)
        stack[-1].children.append(child)
    else:
        output.append(child)
    stack.append(child)


def __should_pop_higher_level(stack: [Section], header_to_test: Section):
    if not stack:
        return False
    return stack[-1].heading.style.size <= header_to_test.heading.style.size


def __top_has_no_header(stack: [Section]):
    if not stack:
        return False
    return len(stack[-1].heading.text) == 0


# read sample_data from block_list.json
samplee_data = []
with open("block_list.json") as f:
    samplee_data = json.load(f)


# this is the meta deta for the whole document this i need where to get this
distribution_data = {"_body_size": 11.99}  # see

output_structure = create_hierarchy(samplee_data, distribution_data)


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)


# Test the create_hierarchy function with the sample data


# Save to JSON file with custom encoder
with open("output.json", "w") as f:
    json.dump(output_structure, f, cls=CustomEncoder, indent=4)
