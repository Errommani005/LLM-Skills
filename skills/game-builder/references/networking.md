# Networking

Read this when the game has more than one player. Pick the mode first (it is an **expensive-to-reverse
decision: ask the user**), then follow only that mode's section.

## Contents
1. Choose the mode
2. How friends actually reach each other for $0
3. Authority rules (who decides what)
4. The tested template: `net.gd`
5. Connecting the game to `net.gd`
6. Room flow and what each screen does
7. Network edge cases (what is handled, what you must handle)
8. Testing
9. Web and WebRTC (not shipped as a template)
10. When $0 networking is not enough
11. Voice chat (proximity)

---

## 1. Choose the mode

| Mode | Use when | How | Cost | Template |
|---|---|---|---|---|
| **none** | Single player, puzzle, narrative, most arcade | no network code, no `network/` folder | $0 | - |
| **local** | Couch co-op, hot-seat, split-screen | One process. Map each player to an input device id; a camera per player or one shared camera. No `Net`. | $0 | - |
| **lan** | Same Wi-Fi / same house | ENet listen server, room code is the host's LAN address | $0 | `net_enet.gd` (tested) |
| **online** (desktop builds) | Friends over the internet | Same ENet listen server; reach the host with VPN overlay, UPnP, or port forward (section 2) | $0 | `net_enet.gd` (tested) |
| **online-web** | Must run in a browser | WebRTC + a free signaling function (section 9) | $0 but some pairs fail | not shipped |
| **dedicated** | Competitive, persistent worlds, >8 players, matchmaking | Needs always-on servers | **not $0** | out of scope: say so |

Default for "play with friends": **online with ENet listen server**, 2-4 players. Rooms of about 2-8 are the
sweet spot for Godot's built-in multiplayer; beyond that plan for trouble and measure.

"Peer to peer" in friend games means **host-authoritative listen server** (one friend's game is the server).
True mesh P2P (every peer simulates and syncs with every other) is much harder to keep bug-free: avoid it.

---

## 2. How friends actually reach each other for $0

Godot's multiplayer uses UDP. Most home connections sit behind NAT, so the host's port must be reachable.
These are the free ways, most reliable first. Show the player the right hint in the UI when joining fails.

| Method | Reliability | What players do |
|---|---|---|
| **LAN** | Always works | Same network; code = host's local IP |
| **VPN overlay** (Tailscale, ZeroTier free tiers; check current limits) | Works through nearly all NATs | Everyone installs the VPN client and joins one network; code = host's VPN IP |
| **UPnP** | Works on many home routers | Automatic: `Net.find_public_ip()` asks the router to open the port and returns the public IP |
| **Manual port forward** | Works if the router allows | Host forwards **UDP 7777** to their PC |
| **Carrier-grade NAT** | Hosting impossible | Some ISPs share one public IP among customers: another friend hosts, or use the VPN |

The **room code** in `net.gd` is the host's IPv4 address written as 8 hex characters
(`192.168.1.20` becomes `C0A80114`). It needs no server. The host's lobby shows the code; friends type it.

Free third-party services (signaling, VPN) have changing terms: record the limits you rely on in `TOOLCHAIN.md`.

---

## 3. Authority rules (who decides what)

Plain rules, same for every genre:

1. **The host is the truth** for anything that affects more than one player: score, round state, timers, doors,
   shared items, who holds what, who is alive.
2. **Clients send requests, never results.** "I want to grab crate 7", not "I now hold crate 7".
3. **Each player controls their own movement** (client-authoritative for the own character). It feels
   instant and is fine between friends. Switch to host-authoritative only for competitive games.
4. **The host validates every request**: Is the sender alive? Is the item free? Is it in range? Is the room open?
5. Announcements go **host to everyone**; requests go **client to host**. Nothing client-to-client.

RPC cheat sheet (Godot 4):
```gdscript
@rpc("any_peer", "call_remote", "reliable")        # client -> host REQUEST
func request_grab(item_path: NodePath) -> void:
	var who := multiplayer.get_remote_sender_id()   # never trust a "who" argument
	if not multiplayer.is_server(): return
	# ...validate, then apply and announce...

@rpc("authority", "call_local", "reliable")        # host -> everyone ANNOUNCEMENT (host runs it too)
func announce_grab(item_path: NodePath, who: int) -> void: ...

@rpc("any_peer", "call_remote", "unreliable")      # frequent data like position: lossy is fine
func send_position(pos: Vector3) -> void: ...
```
- Set authority explicitly: `player.set_multiplayer_authority(peer_id)`; never rely on the default.
- Name player nodes by peer id (`str(peer_id)`) so everyone resolves the same node path.
- Use `MultiplayerSpawner` so late and re-joining players get existing objects, and `MultiplayerSynchronizer`
  for plain properties (transform, health). Both are built in: no code beats built-in.
- Physics props: the host simulates them; clients only display synchronized transforms.

---

## 4. The tested template: `net.gd`

`assets/templates/net_enet.gd` (copied to `network/net.gd` by the scaffold). Autoload name: **Net**.
It was tested with real multi-instance runs on Godot 4.7.1 (headless): host plus clients on loopback.

Public API: `Net.host(name)`, `Net.join(code_or_ip, name)`, `Net.start_game()`, `Net.leave(reason)`,
`Net.kick(id)`, `Net.find_public_ip()`, `Net.code_from_ip(ip)`, `Net.ip_from_code(code)`, `Net.local_ip()`.
Signals: `players_changed`, `join_failed(reason)`, `left_room(reason)`, `game_starting`, `public_ip_found(ip)`.
Data: `Net.players` (peer id to name), `Net.room_open`.

Design choices inside it, and why:
- `multiplayer.server_relay = false`: clients only talk to the host, and relaying joins/leaves caused engine
  error spam whenever several players left at once.
- Names are cleaned, length-capped, and de-duplicated ("Bob" then "Bob 2").
- A join **watchdog**: a full room or wrong address gives silence, not an error: after 6 s the player sees a
  clear message instead of a frozen "Joining...".
- A peer that connects but never introduces itself is kicked after 5 s.
- `GAME_VERSION` mismatch is refused with a readable reason (bump it whenever a build is incompatible).
- Port busy when hosting returns a readable error, not a crash.
- Host leaving closes the room for everyone (no host migration: logged decision D-005 in the standard).

Customize only the constants at the top (`PORT`, `MAX_PLAYERS`, `MAX_NAME_LEN`, `GAME_VERSION`).

---

## 5. Connecting the game to `net.gd`

The lobby screen (`ui/room/room.gd`) listens; the level script reacts to the game starting. Pattern:

```gdscript
# room.gd - Lobby screen. WHAT: shows the room code and the player list; host presses Start.
extends Control

func _ready() -> void:
	Net.players_changed.connect(_redraw)
	Net.game_starting.connect(func(): get_tree().change_scene_to_file("res://levels/level1/level1.tscn"))
	Net.left_room.connect(func(why): _back_to_menu(why))
	Net.join_failed.connect(func(why): $Message.text = why)

func _redraw() -> void:
	$PlayerList.text = "\n".join(Net.players.values())
	$StartButton.visible = multiplayer.is_server() and Net.players.size() >= 2
```
In the level, spawn one player per entry in `Net.players` (host spawns, `MultiplayerSpawner` replicates).
When a player disconnects mid-game, `multiplayer.peer_disconnected` fires on the host: the level script must
remove that player's node **and drop anything they carried**. That part is game-specific: `net.gd` can't do it.

---

## 6. Room flow

```
MENU -> (Host | Join) -> LOBBY -> Start -> PLAYING (room closed) -> ROUND_END -> LOBBY or MENU
                          ^                                               |
                          +---------------- host or player leaves --------+  (everyone gets a message)
```
`State.phase` mirrors this. Every transition has an exit: no screen without a Back or Leave button.

---

## 7. Network edge cases

| Case | In `net.gd`? | Notes |
|---|---|---|
| Room full | Yes | Watchdog message |
| Wrong code / nobody hosting | Yes | Watchdog message |
| Duplicate / empty / long / multiline names | Yes | Cleaned and numbered |
| Join after game started | Yes | Refused with reason |
| Different build versions | Yes | Refused with reason |
| Peer never introduces itself | Yes | Kicked after 5 s |
| Host leaves | Yes | `left_room("Host left the room")` for all |
| Port already in use | Yes | `join_failed` message |
| Many players leave at once | Yes | No error spam (`server_relay` off) |
| Player leaves mid-game | **No: you** | Remove node, drop carried items, update win condition |
| Everyone but one leaves | **No: you** | Decide: end round, or continue solo? Log it |
| Two players act on one object | **No: you** | Host grants the first request received, ignores the second |
| Host lag spike / alt-tab | **No: you** | Test it; keep timers on the host |
| Latency and packet loss | **No: you** | Test with `tc netem` on Linux (`sudo tc qdisc add dev lo root netem delay 100ms loss 5%`) or a Windows tool; use `unreliable` for frequent updates and interpolate |
| Cheating | Accepted | Friend game: host validates requests, but anti-cheat is out of scope |

---

## 8. Testing

`scripts/net_test.sh <project>` (gate **G4**) launches real instances and checks: four players with
duplicate names, start, late joiner refused, full room refused, host leaving. Run it after any change to
`net.gd`. Also play two real windows by hand once per feature: launch two instances from the editor
(Debug menu: Run Multiple Instances, called Customize Run Instances in newer versions) or two Godot MCP `run_project` sessions.

---

## 9. Web and WebRTC (not shipped as a template)

Browsers cannot open raw UDP, so ENet does not work in a web export. The browser option is **WebRTC**
(`WebRTCMultiplayerPeer`): peers connect directly but first need a **signaling** exchange (offer/answer) through a small
server, and a **STUN** server to discover public addresses (free public STUN servers exist). A **TURN relay** is
needed for strict NATs and is *not* free: accept that some pairs will fail and show a clear message with a fallback.
Plan: room code = key in a free serverless signaling function; host registers, joiners fetch the host's offer.
Desktop builds need the pinned WebRTC native extension; web builds have it built in.

Because this adds an external service, **ask the user before choosing web multiplayer**, record the free-tier limits in
`TOOLCHAIN.md`, and keep the same `Net` signals so the rest of the game does not change.
Also note: Godot 4 web export uses the Compatibility renderer and has a smaller feature set; check the pinned version's docs.

---

## 10. When $0 networking is not enough
11. Voice chat (proximity)

Say it plainly to the user and offer the nearest $0 alternative:
- Matchmaking with strangers, ranked play, persistent accounts: needs servers. Alternative: friends-only rooms.
- Voice chat: needs relay infrastructure. Alternative: tell players to use Discord.
- Steam lobbies/relay: has a developer fee and ties the game to a store. Only if the user chooses to ship there.

---

## 11. Voice chat (proximity)

Voice is the hardest $0 requirement: engines do not ship a free, ready voice stack. Decide it early (it is an expensive choice: ask) and vet the option in the engine's
`tools-<engine>.md` (Godot: TwoVoip; Unity: OpenVoiceSharp, or Vivox after verifying limits; Unreal: EOS Voice after verifying terms). Fallback: players use Discord and the game shows a speaking indicator.

**Pattern (all engines):**
1. Capture the microphone and compress with Opus (the vetted addon does this; push-to-talk by default, voice-activation as an option).
2. Send the packets through the **Net seam**, never a second network path. Voice packets are small and frequent: send them **unreliable**.
3. The host forwards each speaker's packets **only to peers within hearing range** (distance check on the host), which keeps bandwidth flat as players are added.
4. The receiver plays them from a **3D audio source attached to the speaker's character**, so volume and panning follow distance for free.
5. A jitter buffer smooths late packets (the addons include one).

**Voice edge cases:** no microphone or permission denied (the game must still start; show a muted icon), device unplugged mid-match, wrong sample rate (Opus wants 48 kHz or a resample), echo when using speakers
(push-to-talk default helps), player muted by someone else, speaking while knocked down, a player leaving mid-sentence (stop their stream), joining mid-sentence, many people talking at once (cap simultaneous voices), voice during pause, host migration is not supported (room closes).

**Test:** two real instances, speak, confirm the indicator, distance falloff and that a player out of range is not heard. Automated G4 cannot test audio: log it as a manual check in `DECISIONS.md`.
