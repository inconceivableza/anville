#!/bin/sh
# ✨ Dump the environment's database and send it to the backup target over SFTP.
#
# From the environment:
#   DATABASE_URL         what to dump
#   BACKUP_TARGET        sftp://user@host:port/directory/ (a Hetzner Storage Box sub-account uses port 23)
#   BACKUP_SSH_KEY       the private key that sub-account accepts
#   BACKUP_KNOWN_HOSTS   the target's host key, as ssh-keyscan prints it
#   BACKUP_NAME          what the dumps are named after: the environment
#   BACKUP_KEEP          how many dumps to keep at the target
#   WORK                 a writable directory (default /work)

set -eu

WORK=${WORK:-/work}
KEEP=${BACKUP_KEEP:-30}
umask 077

# Add the trailing slash sftp needs to start in the directory.
case "$BACKUP_TARGET" in
  sftp://*/) TARGET=$BACKUP_TARGET ;;
  sftp://*/*) TARGET=$BACKUP_TARGET/ ;;
  *) echo "BACKUP_TARGET must look like sftp://user@host:port/directory/" >&2; exit 1 ;;
esac

printf '%s\n' "$BACKUP_SSH_KEY" > "$WORK/key"
printf '%s\n' "$BACKUP_KNOWN_HOSTS" > "$WORK/known_hosts"

send() {
  # Reads sftp commands from standard input. The host key must match: a dump is never sent to a stranger.
  sftp -q -b - \
    -i "$WORK/key" \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o StrictHostKeyChecking=yes \
    -o UserKnownHostsFile="$WORK/known_hosts" \
    "$TARGET"
}

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
DUMP=$BACKUP_NAME-$STAMP.dump

echo "Dumping to $DUMP"
pg_dump --format=custom --no-owner --no-privileges --file "$WORK/$DUMP" --dbname "$DATABASE_URL"

# A dump that cannot be read back is not a backup.
pg_restore --list "$WORK/$DUMP" > /dev/null
echo "Dumped $(wc -c < "$WORK/$DUMP") bytes"

# Sent under another name and renamed once whole, so a dump cut short is never taken for a good one.
send <<SFTP
put $WORK/$DUMP $DUMP.part
rename $DUMP.part $DUMP
SFTP
echo "Sent $DUMP"

# The names sort by time. Keep the newest, remove the rest.
OLD=$(echo "ls -1" | send | grep "^$BACKUP_NAME-[0-9TZ]*\.dump$" | sort | head -n "-$KEEP" || true)
if [ -n "$OLD" ]; then
  echo "$OLD" | sed 's/^/rm /' | send
  echo "Removed $(echo "$OLD" | wc -l) older dump(s)"
fi
