"""Constants and enumerations for Pixel Asset Manager."""

# File extension mappings
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
GIF_EXTENSIONS = {".gif"}
ASEPRITE_EXTENSIONS = {".aseprite", ".ase"}
JSON_EXTENSIONS = {".json"}

# File types
FILE_TYPE_IMAGE = "image"
FILE_TYPE_ASEPRITE = "aseprite"
FILE_TYPE_SPRITESHEET = "spritesheet"
FILE_TYPE_JSON = "json"
FILE_TYPE_GIF = "gif"
FILE_TYPE_FOLDER = "folder"
FILE_TYPE_OTHER = "other"

# File roles
ROLE_AI_SOURCE = "ai_source"
ROLE_ASEPRITE_SOURCE = "aseprite_source"
ROLE_EXPORT_PNG = "export_png"
ROLE_PREVIEW = "preview"
ROLE_SPRITESHEET = "spritesheet"
ROLE_REFERENCE = "reference"
ROLE_MASK = "mask"
ROLE_COLLISION_REF = "collision_ref"
ROLE_ANIMATION_FRAME = "animation_frame"
ROLE_OTHER = "other"

ROLE_LABELS = {
    ROLE_AI_SOURCE: "AI原图",
    ROLE_ASEPRITE_SOURCE: "Aseprite源文件",
    ROLE_EXPORT_PNG: "导出PNG",
    ROLE_PREVIEW: "预览图",
    ROLE_SPRITESHEET: "Spritesheet",
    ROLE_REFERENCE: "参考图",
    ROLE_MASK: "遮罩",
    ROLE_COLLISION_REF: "碰撞参考",
    ROLE_ANIMATION_FRAME: "动画帧",
    ROLE_OTHER: "其他",
}

# Thumbnail sizes
THUMBNAIL_SIZES = [128, 192, 256]
DEFAULT_THUMBNAIL_SIZE = 192

# UI constants
APP_NAME = "美术资源管理工具"
APP_VERSION = "0.1.0"

# Theme colors
COLOR_BACKGROUND = "#1E1E1E"
COLOR_SIDEBAR = "#252526"
COLOR_CARD = "#2D2D30"
COLOR_CARD_HOVER = "#3A3A3D"
COLOR_TEXT_PRIMARY = "#E6E6E6"
COLOR_TEXT_SECONDARY = "#A0A0A0"
COLOR_ACCENT = "#6CA0DC"
COLOR_DANGER = "#D9534F"
COLOR_BORDER = "#3F3F46"
