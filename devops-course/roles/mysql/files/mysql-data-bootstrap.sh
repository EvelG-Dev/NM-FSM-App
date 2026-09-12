# Idempotent: safe on every boot. All state checks are re-runnable.
set -euo pipefail
DATADIR="/mnt/mysql-data"
MARKER="mysql"        # dir that exists inside an initialised datadir
LOG="/var/log/mysql-data-bootstrap.log"
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }
log "=== bootstrap start ==="

# --- 1. Find the data volume -----------------------
ROOT_DISK=$(lsblk -no PKNAME "$(findmnt -no SOURCE /)" | head -1)
DATA_DEV=""
for i in $(seq 1 30); do
  for dev in $(lsblk -dno NAME,TYPE | awk '$2=="disk"{print $1}'); do
    if [ "$dev" != "$ROOT_DISK" ]; then
      DATA_DEV="/dev/$dev"
      break
    fi
  done
  [ -n "$DATA_DEV" ] && break
  log "waiting for data volume... attempt $i"
  sleep 5
done

if [ -z "$DATA_DEV" ]; then
  log "no data volume attached - running from root volume (Packer build?)"
  exit 0
fi

log "data volume: $DATA_DEV"

# --- 2. Format if blank ----------------------------
if ! blkid "$DATA_DEV" > /dev/null 2>&1; then
  log "no filesystem on $DATA_DEV - formatting XFS"
  mkfs.xfs -q "$DATA_DEV"
fi

# Already mounted at the datadir? Nothing to do.
if findmnt -no SOURCE "$DATADIR" > /dev/null 2>&1; then
  log "$DATADIR already mounted - done"
  exit 0
fi

# --- 3. Seed the volume from the baked datadir if it is empty --------
TMP_MNT="/mnt/.datavol-seed"
mkdir -p "$TMP_MNT"
mount "$DATA_DEV" "$TMP_MNT"

if [ ! -d "$TMP_MNT/$MARKER" ]; then
  if [ -d "$DATADIR/$MARKER" ]; then
    log "volume empty - seeding from baked datadir"
    rsync -a "$DATADIR/" "$TMP_MNT/"
  else
    log "volume empty and no baked datadir found - mysqld will initialise"
  fi
else
  log "volume already contains a datadir - no seeding"
fi

umount "$TMP_MNT"
rmdir "$TMP_MNT"

# --- 4. Mount at the datadir (fstab via UUID for reboot persistence) ------
UUID=$(blkid -s UUID -o value "$DATA_DEV")
if ! grep -q "$UUID" /etc/fstab; then
  echo "UUID=$UUID $DATADIR xfs defaults,nofail 0 2" >> /etc/fstab
  log "fstab entry added (UUID=$UUID)"
fi

mkdir -p "$DATADIR"
mount "$DATADIR"

# --- 5. Ownership + SELinux context for MySQL --------------------
chown -R mysql:mysql "$DATADIR"
command -v restorecon > /dev/null 2>&1 && restorecon -R "$DATADIR" || true

log "bootstrap complete - $DATADIR is on $DATA_DEV"
exit 0
