#!/bin/bash
IFS=$''
cd "$(dirname "$0")"

if [[ $1 == "update" ]]; then
    source "./venv/bin/activate"
    print=$(python extractor.py)
fi

events_file="events.txt"
count=0

while read -r line; do
    events[$count]="$line"
    ((count=$count+1))
done <"$events_file"

# echo -n f"COUNT: {$count}\n"
if [[ $count -gt 0 ]]; then
    # rng=$RANDOM
    # (("rng %= $count"))

    rng=0

    for ((i = 0; i < count; i++)); do
        if (( i != rng )); then
            if [[ -n $tooltip ]]; then
                tooltip+=$'\n'
            fi
            tooltip+="${events[$i]}"
        fi
    done
    echo -n $(jq --unbuffered --compact-output --args --arg \
        title "${events[$rng]}" --args --arg tooltip "${tooltip}"\
        -n '{text: $title, class: "todo", tooltip: $tooltip}' \
    )
else
    echo -n $(jq --unbuffered --compact-output --args --arg \
        title "No Upcoming Assignments" \
        -n '{text: $title, class: "done"}' \
    )
fi

