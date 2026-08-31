"""
SpiderLang CLI Themes — every command has its own identity.
Each command renders a distinct ASCII emblem + accent colour, so the terminal
feels alive and each action (lunch / build / info / tree) is unmistakable.
Pure ASCII — no emojis.
"""

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# accent base colors
GREY =   "\033[90m"
RED =    "\033[31m"
GREEN =  "\033[32m"
YELLOW = "\033[33m"
BLUE =   "\033[34m"
MAGENTA ="\033[35m"
CYAN =   "\033[36m"
WHITE =  "\033[97m"


def _wrap(accent, art):
    """Return the emblem with its accent colour applied per line."""
    lines = art.strip("\n").splitlines()
    return "\n".join(f"{accent}{ln}{RESET}" for ln in lines)


# Lua-like keyword colours for the identity cards
def theme(name):
    t = THEMES.get(name, THEMES["build"])
    return {
        "accent": t["accent"],
        "accent2": t["accent2"],
        "tag": t["tag"],
        "emblem": t["emblem"],
        "title": t["title"],
    }


# ---- per-command emblems + accents ----
_LUNCH = r"""
            ___
          .'   '.
        _|       |_          L U N C H
      .'   _. \" ._   '.       device selector
     |  .'  /|\  '.  |
      \  \ _/ | \_ /  /
       '. '.__/ \__.' .'
         '.__     __.'
             |   |
           __|   |__
"""
_LUNCH_K = _wrap(MAGENTA, _LUNCH)

_BUILD = r"""
        /\                         
       /  \    B U I L D
      /    \    forge
     |  __  |
     | |  | |   >>> recovery.img
     | |  | |   >>> vendor_boot.img
     | |__| |   >>> boot.img
      \    /
       \  /
        \/
"""
_BUILD_K = _wrap(YELLOW, _BUILD)

_INFO = r"""
        .--.
       / _  \      I N F O
      / \_/  \     diagnostics
     |  ___  |
     | |   | |    codename / variant
     | |___| |    partitions / A.B / images
     |       |
     '-------'
"""
_INFO_K = _wrap(CYAN, _INFO)

_TREE = r"""
       ___           
      /   \___       
     /     \   \     T R E E
    |   ()   \  /
     \       / /     device tree
      \_____/ /
       |     |
       |_____|
"""
_TREE_K = _wrap(GREEN, _TREE)

_SHOW = r"""
     .
    /.\      S H O W
   / | \     source
    /.\
   / | \
"""
_SHOW_K = _wrap(BLUE, _SHOW)

THEMES = {
    "lunch": dict(accent=MAGENTA, accent2=WHITE, tag="LUNCH", emblem=_LUNCH_K,
                  title="SPIDER LUNCH SELECTOR"),
    "build": dict(accent=YELLOW, accent2=RED, tag="BUILD", emblem=_BUILD_K,
                  title="SPIDER BUILD FORGE"),
    "info":  dict(accent=CYAN, accent2=WHITE, tag="INFO", emblem=_INFO_K,
                  title="SPIDER DEVICE DIAGNOSTICS"),
    "tree":  dict(accent=GREEN, accent2=WHITE, tag="TREE", emblem=_TREE_K,
                  title="SPIDER DEVICE TREE"),
    "show":  dict(accent=BLUE, accent2=CYAN, tag="SHOW", emblem=_SHOW_K,
                  title="SPIDER SOURCE VIEWER"),
}


def banner(name, subtitle=""):
    """Full identity block for a command: emblem + header rule."""
    t = THEMES.get(name, THEMES["build"])
    a = t["accent"]
    a2 = t["accent2"]
    rule = a + "-" * 56 + RESET
    head = f"{a}{t['tag']:^56}{RESET}"
    sub = f"{DIM}{subtitle:^56}{RESET}" if subtitle else ""
    return "\n".join([t["emblem"], rule, head, sub, rule])


def image_tag(image_type):
    from . import images as _img
    it = _img.by_name(image_type)
    if not it:
        return f"{WHITE}[ ? ]{RESET}"
    a = it.color
    return f"{a}[ {it.tag:<10} ]{RESET} {it.ext}"


def dim(s):
    return f"{DIM}{s}{RESET}"
