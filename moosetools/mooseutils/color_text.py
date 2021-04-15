import colored

def color_text(text, fg=None, bg=None):
    output = ''
    if fg is not None:
        output += colored.fg(fg)
    if bg is not None:
        output += colored.bg(bg)
    output += text
    if (fg is not None) or (bg is not None):
        output += colored.attr('reset')
    return output
