# net.gd - Autoload "Net". ALL multiplayer code lives in this one file.
# WHAT:     ENet listen server. One player hosts, the others join by room code (or IP).
#           The host is the single source of truth; clients only send requests.
# TALKS TO: ui/room/room.gd listens to the signals below. State.gd may read `players`.
# SIBLINGS: none. To change networking (e.g. WebRTC) replace this file, keep the signals.
extends Node

signal players_changed                 # lobby list changed -> redraw it
signal join_failed(reason: String)     # could not join -> show message on menu
signal left_room(reason: String)       # kicked / host left / disconnected -> back to menu
signal game_starting                   # host pressed Start -> everyone loads the level
signal public_ip_found(ip: String)     # result of find_public_ip(); "" means it failed

const GAME_VERSION := "0.1"            # bump when a new build is incompatible; mismatched joiners are refused
const PORT := 7777
const MAX_PLAYERS := 4                 # host included
const MAX_NAME_LEN := 16
const REGISTER_TIMEOUT := 5.0          # seconds a new peer has to introduce itself
const JOIN_TIMEOUT := 6.0              # seconds before "Joining..." gives up (full room = silence)

var players := {}                      # peer_id -> display name (host's copy is the truth)
var room_open := true                  # false once the game starts: late joiners are refused
var my_name := "Player"
var _reason_from_host := ""            # why the host is about to disconnect us
var _upnp_thread: Thread


func _ready() -> void:
	multiplayer.server_relay = false           # clients only talk to the host (it owns the player list);
	                                           # relaying joins/leaves to everyone just causes noise
	multiplayer.peer_connected.connect(_on_peer_connected)
	multiplayer.peer_disconnected.connect(_on_peer_disconnected)
	multiplayer.connected_to_server.connect(_on_connected_ok)
	multiplayer.connection_failed.connect(_on_connection_failed)
	multiplayer.server_disconnected.connect(_on_server_disconnected)


# ---------- public API (UI calls these) ----------

func host(player_name: String) -> bool:
	leave("")                                              # clean slate, no stale peer
	var peer := ENetMultiplayerPeer.new()
	if peer.create_server(PORT, MAX_PLAYERS - 1) != OK:    # port busy / blocked
		join_failed.emit("Could not host (port %d busy?)" % PORT)
		return false
	multiplayer.multiplayer_peer = peer
	my_name = _clean_name(player_name)
	players = {1: my_name}
	room_open = true
	players_changed.emit()
	return true


func join(room_code_or_ip: String, player_name: String) -> void:
	leave("")
	var address := ip_from_code(room_code_or_ip)
	if address == "":
		address = room_code_or_ip.strip_edges()            # allow typing an IP directly
	if address == "":
		join_failed.emit("Enter a room code")
		return
	var peer := ENetMultiplayerPeer.new()
	if peer.create_client(address, PORT) != OK:
		join_failed.emit("Bad address")
		return
	multiplayer.multiplayer_peer = peer
	my_name = _clean_name(player_name)
	_join_watchdog(peer)


func start_game() -> void:                                 # host only
	if not multiplayer.is_server() or players.size() < 1:
		return
	room_open = false
	_begin.rpc()


func leave(reason: String) -> void:                        # safe to call any time, any number of times
	if multiplayer.multiplayer_peer != null:
		multiplayer.multiplayer_peer.close()
		multiplayer.multiplayer_peer = null
	players.clear()
	room_open = true
	_reason_from_host = ""
	if reason != "":                                       # "" = quiet leave (no message to show)
		left_room.emit(reason)


func kick(peer_id: int) -> void:                           # host only
	if multiplayer.is_server() and peer_id != 1 and peer_id in multiplayer.get_peers():
		multiplayer.multiplayer_peer.disconnect_peer(peer_id)


# ---------- room codes: an IPv4 address written as 8 hex characters ----------
# No server needed. Works on LAN, VPN (Tailscale/ZeroTier), or after port forwarding / UPnP.

func code_from_ip(ip: String) -> String:                   # "192.168.1.20" -> "C0A80114"
	var code := ""
	for part in ip.split("."):
		code += "%02X" % clampi(int(part), 0, 255)
	return code


func ip_from_code(code: String) -> String:                 # "C0A80114" -> "192.168.1.20", "" if invalid
	code = code.strip_edges().to_upper()
	if code.length() != 8 or not code.is_valid_hex_number():
		return ""
	var parts := PackedStringArray()
	for i in 4:
		parts.append(str(code.substr(i * 2, 2).hex_to_int()))
	return ".".join(parts)


func local_ip() -> String:                                 # first private IPv4, for LAN rooms
	for ip in IP.get_local_addresses():
		if ip.begins_with("192.168.") or ip.begins_with("10.") or ip.begins_with("172."):
			return ip
	return "127.0.0.1"


func find_public_ip() -> void:                             # asks the router (UPnP) to open the port
	_upnp_thread = Thread.new()                            # blocking call -> runs in a thread
	_upnp_thread.start(func(): _upnp_done.call_deferred(_open_port_upnp()))


# ---------- internals ----------

func _clean_name(raw: String) -> String:
	var n := raw.strip_edges().replace("\n", " ").substr(0, MAX_NAME_LEN)
	return n if n != "" else "Player"


func _unique_name(wanted: String) -> String:               # "Bob" taken -> "Bob 2"
	var n := wanted
	var i := 2
	while n in players.values():
		n = "%s %d" % [wanted.substr(0, MAX_NAME_LEN - 3), i]
		i += 1
	return n


func _on_peer_connected(id: int) -> void:
	if not multiplayer.is_server():
		return
	if not room_open:                                      # game already running
		_refuse(id, "Game already started")
		return
	await get_tree().create_timer(REGISTER_TIMEOUT).timeout
	if id in multiplayer.get_peers() and not players.has(id):
		kick(id)                                           # never introduced itself


func _join_watchdog(peer: MultiplayerPeer) -> void:        # a full room never answers: don't hang
	await get_tree().create_timer(JOIN_TIMEOUT).timeout
	if multiplayer.multiplayer_peer == peer and peer.get_connection_status() == MultiplayerPeer.CONNECTION_CONNECTING:
		leave("")
		join_failed.emit("Could not connect (wrong code, full room, or blocked)")


func _on_connected_ok() -> void:                           # client side: introduce myself
	_register.rpc_id(1, my_name, GAME_VERSION)


func _on_connection_failed() -> void:
	leave("")
	join_failed.emit("Could not connect (wrong code, full room, or blocked)")


func _on_server_disconnected() -> void:
	var why := _reason_from_host if _reason_from_host != "" else "Host left the room"
	leave(why)


func _on_peer_disconnected(id: int) -> void:
	if players.erase(id) and multiplayer.is_server():
		players_changed.emit()
		for peer_id in multiplayer.get_peers():            # several players can leave in the same
			if _is_connected(peer_id):                      # instant: skip the ones already closing
				_sync_players.rpc_id(peer_id, players)


func _is_connected(id: int) -> bool:
	var packet_peer: ENetPacketPeer = multiplayer.multiplayer_peer.get_peer(id)
	return packet_peer != null and packet_peer.get_state() == ENetPacketPeer.STATE_CONNECTED


func _refuse(id: int, reason: String) -> void:             # tell the peer why, then drop it
	_tell_reason.rpc_id(id, reason)
	await get_tree().create_timer(0.3).timeout
	kick(id)


func _upnp_done(ip: String) -> void:
	_upnp_thread.wait_to_finish()
	public_ip_found.emit(ip)


func _open_port_upnp() -> String:                          # blocking: only call from a thread
	var upnp := UPNP.new()
	if upnp.discover(2000) != UPNP.UPNP_RESULT_SUCCESS:
		return ""
	var gateway := upnp.get_gateway()
	if gateway == null or not gateway.is_valid_gateway():
		return ""
	if upnp.add_port_mapping(PORT, PORT, "friend-game", "UDP") != UPNP.UPNP_RESULT_SUCCESS:
		return ""
	return upnp.query_external_address()


# ---------- RPCs (the only messages that cross the network) ----------

@rpc("any_peer", "call_remote", "reliable")
func _register(wanted_name: String, version: String) -> void:   # runs on the host
	var id := multiplayer.get_remote_sender_id()
	if not multiplayer.is_server() or players.has(id):
		return
	if not room_open:
		_refuse(id, "Game already started")
		return
	if version != GAME_VERSION:
		_refuse(id, "Different game version (host has %s, you have %s)" % [GAME_VERSION, version])
		return
	players[id] = _unique_name(_clean_name(wanted_name))
	_sync_players.rpc(players)


@rpc("authority", "call_local", "reliable")
func _sync_players(list: Dictionary) -> void:              # host -> everyone
	players = list
	players_changed.emit()


@rpc("authority", "call_local", "reliable")
func _begin() -> void:
	room_open = false
	game_starting.emit()


@rpc("authority", "call_remote", "reliable")
func _tell_reason(reason: String) -> void:
	_reason_from_host = reason
