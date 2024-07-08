#!/bin/bash

# Skip branches
BRANCHES_TO_SKIP=("main")

# Get the current branch name
BRANCH_NAME=$(git symbolic-ref --short HEAD)
BRANCH_NAME="${BRANCH_NAME##*/}"

# Extract JIRA ID from the branch name using the pattern feature/SWM-123-commit-test
JIRA_ID=$(echo $BRANCH_NAME | egrep -o 'SWM-[0-9]+')

# Check if the branch is in the excluded list
BRANCH_EXCLUDED=$(printf "%s\n" "${BRANCHES_TO_SKIP[@]}" | grep -c "^$BRANCH_NAME$")

# Check if the commit message already contains the JIRA ID
BRANCH_IN_COMMIT=$(grep -c "$JIRA_ID" $1)

# Add JIRA ID to the commit message if conditions are met
if [ -n "$JIRA_ID" ] && ! [[ $BRANCH_EXCLUDED -eq 1 ]] && ! [[ $BRANCH_IN_COMMIT -ge 1 ]]; then 
  sed -i.bak -e "1s/^/[$JIRA_ID] /" $1
fi
