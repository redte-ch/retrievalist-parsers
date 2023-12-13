from typing import List
import json


class Section:
    def __init__(self, element, level):
        self.heading = element
        self.children = []
        self.level = 0

    def to_dict(self):
        return {
            'heading': {
                'text': self.heading.text,
                'style': self.heading.style.to_dict()  # Use the to_dict method of Style
            },
            'children': [child.to_dict() for child in self.children]
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    def __str__(self):
        return f"Section(Heading: {self.heading.text}, Level: {self.level}, Children: {len(self.children)})"


def serialize_section(obj):
    if isinstance(obj, Section):
        return obj.to_dict()
    raise TypeError("Type not serializable")


class TextElement:
    def __init__(self, text, style, bbox):
        self.text = text
        self.style = style
        self.bbox = bbox


class Style:
    def __init__(self, font, size, color):
        self.font = font
        self.size = size
        self.color = color

    def to_dict(self):
        return {
            'font': self.font,
            'size': self.size,
            'color': self.color
        }


class DanglingTextSection:
    def __init__(self):
        self.children = []
        self.level = 0

    def to_dict(self):
        return {
            'children': [child.to_dict() for child in self.children],
            'level': self.level,
            'text': self.children[0].heading.text if self.children else "",
            'style': self.children[0].heading.style.to_dict() if self.children else {}
        }

# now this basically convert each list element into this form of text_element we defined abive.


def convert_to_text_elements(element_data):
    lines = element_data['lines']
    text_elements = []

    for line in lines:
        spans = line['spans'][0]
        text_element = TextElement(
            text=spans['text'],
            style=Style(
                font=spans['font'],
                size=spans['size'],
                color=spans['color']
            ),
            bbox=line['bbox']
        )
        text_elements.append(text_element)

    return text_elements


def create_hierarchy(extracted_data: List[dict], style_distribution: dict) -> List[Section]:
    structured = []
    level_stack = []

    for element_data in extracted_data:
        text_elements = convert_to_text_elements(element_data)

        for text_element in text_elements:
            style = text_element.style

            if header_detector(text_element, style_distribution):
                child = Section(text_element, level=len(level_stack))
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
                        dangling_content.level = len(level_stack)
                        structured.append(dangling_content)

    return structured


def header_detector(element, style_distribution):
    """
    Sample header detection logic based on font size.
    You may need to adjust this based on your specific data characteristics.
    """
    # detect if the particular text element is an header
    if (len(element.text) <= 2):
        return False

    if (element.style.size > (style_distribution['_body_size']+1)):
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
with open('block_list.json') as f:
    samplee_data = json.load(f)


# this is the meta deta for the whole document this i need where to get this
distribution_data = {
    '_data': {12.0: 35, 13.55: 3, 13.56: 3, 11.99: 2},
    '_body_size': 11.99,
    '_min_found_size': 11.99,
    '_max_found_size': 29.99,
    '_line_margin': 0.5
}

# print(type(samplee_data)) : this is the list
print(samplee_data[0])
output_structure = create_hierarchy(samplee_data, distribution_data)


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)

# Test the create_hierarchy function with the sample data


# Save to JSON file with custom encoder
with open('output.json', 'w') as f:
    json.dump(output_structure, f, cls=CustomEncoder, indent=4)
