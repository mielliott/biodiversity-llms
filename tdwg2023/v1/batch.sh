IN=$1         # TSV with header
CHUNK=$2      # Starting index is CHUNK * CHUNK_SIZE
CHUNK_SIZE=$3 # Stopping index is (CHUNK + 1) * CHUNK_SIZE

cat <(head $IN -n 1) \
    <(tail $IN -n +$((2 + $CHUNK_SIZE * $CHUNK)) | head -n $CHUNK_SIZE)
