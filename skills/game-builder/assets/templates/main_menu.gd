# main_menu.gd - The first screen. Replace the placeholder with real buttons (Play / Host / Join / Quit).
# WHAT:     start of the game.
# TALKS TO: State (resets it), and Net (online games) through the room screen.
# SIBLINGS: ui/room/room.gd, ui/hud/hud.gd.
extends Control


func _ready() -> void:
	State.reset()
	print("%s booted." % ProjectSettings.get_setting("application/config/name"))
