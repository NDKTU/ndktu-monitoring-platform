#!/usr/bin/env bash
# Back up the camera_base database out of the running ndktu_db container.
#
#   ./scripts/backup_db.sh              # write a new backup
#   ./scripts/backup_db.sh --verify     # ...and prove it restores into a scratch container
#
# Backups land OUTSIDE the repo on purpose: they hold personal data (names, passport
# numbers) and this repo has untracked, un-gitignored data directories already.
set -euo pipefail

CONTAINER="${CONTAINER:-ndktu_db}"
DB="${DB:-camera_base}"
USER_NAME="${USER_NAME:-bekzod}"
DEST="${DEST:-$HOME/backups/ndktu-monitoring-platform}"
KEEP="${KEEP:-14}"          # how many dumps to retain
VERIFY=0
[ "${1:-}" = "--verify" ] && VERIFY=1

docker inspect "$CONTAINER" >/dev/null 2>&1 || { echo "container $CONTAINER is not running"; exit 1; }

mkdir -p "$DEST"
TS=$(date +%Y-%m-%d_%H%M)

echo "backing up $DB from $CONTAINER -> $DEST"
docker exec "$CONTAINER" pg_dump -U "$USER_NAME" -d "$DB" -Fc          > "$DEST/${DB}_$TS.dump"
docker exec "$CONTAINER" pg_dump -U "$USER_NAME" -d "$DB" | gzip       > "$DEST/${DB}_$TS.sql.gz"
docker exec "$CONTAINER" pg_dumpall -U "$USER_NAME" --globals-only     > "$DEST/globals_$TS.sql"
( cd "$DEST" && sha256sum "${DB}_$TS.dump" "${DB}_$TS.sql.gz" "globals_$TS.sql" > "checksums_$TS.txt" )

echo "wrote:"
ls -lh "$DEST/${DB}_$TS.dump" "$DEST/${DB}_$TS.sql.gz" | awk '{print "  " $NF, $5}'

if [ "$VERIFY" = 1 ]; then
    echo "verifying by restoring into a scratch container..."
    NAME="backup_verify_$$"
    docker run -d --name "$NAME" -e POSTGRES_USER="$USER_NAME" -e POSTGRES_PASSWORD=verify \
        -e POSTGRES_DB="$DB" postgres:17-alpine >/dev/null
    trap 'docker rm -f "$NAME" >/dev/null 2>&1 || true' EXIT
    for _ in $(seq 1 30); do
        docker exec "$NAME" pg_isready -U "$USER_NAME" >/dev/null 2>&1 && break
        sleep 2
    done
    docker cp "$DEST/${DB}_$TS.dump" "$NAME:/tmp/b.dump" >/dev/null
    docker exec "$NAME" pg_restore -U "$USER_NAME" -d "$DB" --no-owner /tmp/b.dump

    fail=0
    for t in $(docker exec "$CONTAINER" psql -U "$USER_NAME" -d "$DB" -tAc \
               "select table_name from information_schema.tables where table_schema='public' order by 1"); do
        a=$(docker exec "$CONTAINER" psql -U "$USER_NAME" -d "$DB" -tAc "select count(*) from \"$t\"")
        b=$(docker exec "$NAME"      psql -U "$USER_NAME" -d "$DB" -tAc "select count(*) from \"$t\"")
        if [ "$a" = "$b" ]; then printf '  %-20s %8s  ok\n' "$t" "$a"
        else printf '  %-20s %8s vs %s  MISMATCH\n' "$t" "$a" "$b"; fail=1; fi
    done
    [ "$fail" = 0 ] && echo "verified: restore matches the live database" \
                    || { echo "VERIFY FAILED"; exit 1; }
fi

# Retention: keep the newest $KEEP of each artefact kind.
for pattern in "${DB}_*.dump" "${DB}_*.sql.gz" "globals_*.sql" "checksums_*.txt"; do
    # shellcheck disable=SC2012
    ls -1t "$DEST"/$pattern 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm --
done

echo "done. restore with:"
echo "  docker exec -i $CONTAINER pg_restore -U $USER_NAME -d $DB --clean --if-exists < $DEST/${DB}_$TS.dump"
