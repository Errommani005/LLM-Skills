# state.gd - Autoload "State". The one place that knows what phase the game is in and the score.
# WHAT:     phase, round number, score. No gameplay logic - just the facts everyone may read.
# TALKS TO: the level script sets it; ui/hud reads it; net.gd (online games) lets the host set it.
# SIBLINGS: events.gd announces changes, state.gd stores them.
extends Node

enum Phase { MENU, LOBBY, PLAYING, ROUND_END, GAME_OVER }

var phase := Phase.MENU
var round_number := 0
var score := 0


func reset() -> void:                          # call when starting a fresh game: no leftovers from last run
	phase = Phase.MENU
	round_number = 0
	score = 0
