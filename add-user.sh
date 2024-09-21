#!/bin/bash

# run
# chmod +x ./add-user.sh 
# ./add-user.sh example

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
  echo "User $USERNAME is already in the configuration file."
else
  echo "Adding user $USERNAME to the configuration file..."
  # Add the user to the end of the user list
  sed -i "/users:/a \  - $USERNAME" "$CONFIG_FILE"
  ./algo update-users
fi

echo "User Added!"


