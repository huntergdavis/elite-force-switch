#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$root/sp-probe/build"
run=$(mktemp -d "$root/sp-probe/build/combined-run.XXXXXXXX")
echo "Combined experiment logs: $run"
"$root/sp-probe/build-game-archive.sh" > "$run/game.log" 2>&1
game_dir=$(sed -n 's/^Archive experiment directory: //p' "$run/game.log")
[ -n "$game_dir" ] && [ -f "$game_dir/build/libefgame.a" ] || { echo 'Game archive missing; inspect game.log' >&2; exit 1; }
"$root/sp-probe/build-ui-archive.sh" > "$run/ui.log" 2>&1
ui_dir=$(sed -n 's/^UI experiment directory: //p' "$run/ui.log")
[ -n "$ui_dir" ] && [ -f "$ui_dir/build/libefui.a" ] || { echo 'UI archive missing; inspect ui.log' >&2; exit 1; }
"$root/sp-probe/test-static-collisions.sh" "$game_dir/build/libefgame.a" "$ui_dir/build/libefui.a" > "$run/collisions.log" 2>&1
collision_dir=$(sed -n 's/^Collision experiment directory: //p' "$run/collisions.log")
[ -n "$collision_dir" ] && [ -f "$collision_dir/ui-renamed.a" ] || { echo 'Renamed UI archive missing; inspect collisions.log' >&2; exit 1; }
"$root/sp-probe/build-combined-api.sh" "$game_dir" "$collision_dir" > "$run/combined-api.log" 2>&1
api_dir=$(sed -n 's/^Combined API experiment directory: //p' "$run/combined-api.log")
[ -n "$api_dir" ] && [ -f "$api_dir/combined-api.nro" ] || { echo 'Combined API NRO missing; inspect combined-api.log' >&2; exit 1; }
cat "$run/collisions.log"
echo "Combined API NRO: $api_dir/combined-api.nro"
sha256sum "$api_dir/combined-api.nro"
