# events.gd - Autoload "Events". A signal bus: categories announce things without knowing who listens.
# WHAT:     one line per "something happened" message. Nothing else lives here.
# TALKS TO: anyone emits (Events.round_ended.emit(true)), anyone listens (Events.round_ended.connect(f)).
# SIBLINGS: net.gd (network) and state.gd (game phase) are the other two shared files.
extends Node

signal round_started
signal round_ended(won: bool)                  # emitted by the level script, heard by ui/game_over and ui/victory
signal player_died(player_id: int)             # emitted by player.gd, heard by the level script
# Add new messages below. Keep each to one line and say who emits / who listens.
