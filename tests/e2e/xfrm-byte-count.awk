/lifetime current:/ {
    line = $0
    if (line !~ /\(bytes\)/) {
        if (getline line <= 0) {
            exit 2
        }
    }
    sub(/^.*current:[[:space:]]*/, "", line)
    sub(/\(bytes\).*$/, "", line)
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
    if (line !~ /^[0-9]+$/) {
        exit 2
    }
    total += line
}
END {
    print total + 0
}
