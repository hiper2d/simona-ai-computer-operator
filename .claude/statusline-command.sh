#!/usr/bin/env bash

input=$(cat)

model=$(echo "$input" | jq -r '.model.display_name // "Unknown"')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# Purple color for "Simona"
PURPLE='\033[35m'
RESET='\033[0m'

# Build context progress bar
if [ -n "$used" ]; then
  used_int=$(printf "%.0f" "$used")
  filled=$(( used_int / 5 ))
  empty=$(( 20 - filled ))
  bar=""
  for i in $(seq 1 $filled); do bar="${bar}#"; done
  for i in $(seq 1 $empty); do bar="${bar}-"; done
  context_str="[${bar}] ${used_int}%"
else
  context_str="[--------------------] --%"
fi

printf "${PURPLE}Simona${RESET} | %s | %s" "$model" "$context_str"
