#!/bin/bash

# run
# chmod +x ./remove-user.sh  
# ./remove-user.sh example

# Checks if the username was passed as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <username>"
  exit 1
fi

USERNAME=$1

# Define the path to the configuration file
CONFIG_FILE="./config.cfg"

# Check if the configuration file exists
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Configuration file not found: $CONFIG_FILE"
  exit 1
fi

# Check if the user is already in the config.cfg file
if grep -q "  - $USERNAME" "$CONFIG_FILE"; then
  echo "Removing user $USERNAME from the configuration file..."
  # Remove the user from the user list
  sed -i "/  - $USERNAME/d" "$CONFIG_FILE"
  echo "User $USERNAME successfully removed."
else
  echo "User $USERNAME not found in the configuration file."
  ./algo update-users
fi

echo "User Removed!"