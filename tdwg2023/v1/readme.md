Occurrence records, processed test set, and ChatGPT responses are available in Zenodo at https://doi.org/10.5281/zenodo.8417791.

# Test set T1.1

In total, about 20,000 questions; half are presence (correct answer is "yes") and half are pseudo-absence (correct answer is probably "no"). Includes both terrestrial and aquatic species, mostly in North America.

Compile ~10,000 records into a species presence set

```bash
T1_1="t1-1-presence"

cat raw/*.jsonl | split -n r/1/5 | jq .indexTerms \
| mlr --ijson --otsv template -f "kingdom","phylum","family","genus","specificepithet","country","stateprovince","county" --fill-with MISSING | grep -v MISSING \
| mlr --tsv uniq -a \
| python3 clean.py \
> processed/$T1_1.tsv
```

Shuffle locations in the presence set to make a pseudo-absence set

```bash
T1_1_ABS="t1-1-absence"
paste <(cat processed/$T1_1.tsv | mlr --tsv cut -x -f "country","stateprovince","county") \
      <(cat processed/$T1_1.tsv | mlr --tsv cut -f "country","stateprovince","county" | mlr --tsv shuffle) \
> processed/$T1_1_ABS.tsv
```

Submit questions to ChatGPT

```bash
QA_ARGS="--max-tokens 1 --timeout 10 --num-responses 10 --combine-responses"

cat processed/$T1_1.tsv \
| python3 ~/biodiversity-llms/scripts/nlp/qa.py $QA_ARGS "Does {3} {4} naturally occur in {7}, {6}, {5}? Yes or no." \
> results/$T1_1.tsv

cat processed/$T1_1_ABS.tsv \
| python3 ~/biodiversity-llms/scripts/nlp/qa.py $QA_ARGS "Does {3} {4} naturally occur in {7}, {6}, {5}? Yes or no." \
> results/$T1_1_ABS.tsv
```

# Test set T1.2

Select a subset of presence questions

```bash
SEED=69847
T1_2="t1-2-presence"

# Use `mlr` to shuffle without losing the header line
cat processed/indexTerms-species-location.tsv \
| mlr --tsv --seed $SEED shuffle \
> processed/$T1_2.tsv
```

Use ChatGPT to generate rephrasings: https://chat.openai.com/share/a35e134a-f19e-4026-8b59-cdffdea565f4

```bash
T1_CHUNK_SIZE=999
T1_CHUNK=1
```

Submit rephrased questions

```bash
# ./batch.sh processed/$IN.tsv $T1_CHUNK $T1_CHUNK_SIZE \

IN=$T1_2
QA_ARGS="--max-tokens 1 --timeout 10 --num-responses 10 --combine-responses"

QEND=" Only respond yes or no."
Q1="Can species {3} {4} be found in {7}, {6}, {5}?$QEND"
Q2="Is it possible to encounter species {3} {4} in {7}, {6}, {5}?$QEND"
Q3="Is there a presence of species {3} {4} within {7}, {6}, {5}?$QEND"
Q4="Does {7}, {6}, {5} harbor species {3} {4}?$QEND"
Q5="Is species {3} {4} present in {7}, {6}, {5}?$QEND"
Q6="Can one observe species {3} {4} in {7}, {6}, {5}?$QEND"

cat processed/$T1_1_ABS.tsv \
| python3 ~/biodiversity-llms/scripts/nlp/qa.py $QA_ARGS "$Q1" "$Q2" "$Q3" "$Q4" "$Q5" "$Q6" \
> results/$T1_2_ABS.tsv
```

Combine batches

```bash
mlr --tsvlite cat t1-2-presence-*-$T1_CHUNK_SIZE-phrasing.tsv > t1-2-absence.tsv
```

Make a pseudo-absence subset

```bash
SEED=69847
T1_2_ABS="t1-2-absence"

# Use `mlr` to shuffle without losing the header line
cat processed/indexTerms-species-location-shuffled.tsv \
| mlr --tsv --seed $SEED shuffle \
> processed/$T1_2_ABS.tsv
```

And submit as before

Combine batches

```bash
mlr --tsvlite cat t1-2-absence-*-$T1_CHUNK_SIZE-phrasing.tsv > t1-2-absence.tsv
```

# Test set T1.3

```bash
T1_3="t1-3-presence"
cat processed/$T1_2.tsv \
> processed/$T1_3.tsv
```

First prompt: *Describe the species {3} {4} and the location {7}, {6}, {5}. Then discuss whether {3} {4} naturally occurs in the environment of {7}, {6}, {5}*

Second prompt: *Does {3} {4} occur in {7}, {6}, {5}? Yes or no.*

```bash
PROMPT_THINKING="Describe the species {3} {4} and the location {7}, {6}, {5}. Then discuss whether {3} {4} naturally occurs in the environment of {7}, {6}, {5}"
IN=$T1_3
RES_PREFIX_THINKING="$IN-$T1_CHUNK-$T1_CHUNK_SIZE-thinking"
QA_ARGS="--max-tokens 600 --timeout 60 --num-responses 1 --escape-responses --combine-responses"

./batch.sh processed/$IN.tsv $T1_CHUNK $T1_CHUNK_SIZE \
| python3 ~/biodiversity-llms/scripts/nlp/qa.py "$PROMPT_THINKING" $QA_ARGS > results/$RES_PREFIX_THINKING.tsv
```

```bash
PROMPT_ANSWER=$(printf "{8}\n\nDoes {3} {4} naturally occur in {7}, {6}, {5}? Only respond yes or no.")
RES_PREFIX_ANSWER="$IN-$T1_CHUNK-$T1_CHUNK_SIZE-answer"
QA_ARGS="--max-tokens 1 --timeout 10 --num-responses 10 --combine-responses"

./batch.sh results/$RES_PREFIX_THINKING.tsv $T1_CHUNK $T1_CHUNK_SIZE \
| mlr --tsvlite cut -f kingdom,phylum,family,genus,specificepithet,country,stateprovince,county,responses \
| mlr --tsvlite rename responses,context \
| python3 ~/biodiversity-llms/scripts/nlp/qa.py "$PROMPT_ANSWER" $QA_ARGS > results/$RES_PREFIX_ANSWER.tsv
```

Now do pseudo-absences

```bash
T1_3_ABS="t1-3-absence"
cat processed/$T1_2_ABS.tsv \
> processed/$T1_3_ABS.tsv
```

```bash
IN=$T1_3_ABS
RES_PREFIX_THINKING="$IN-$T1_CHUNK-$T1_CHUNK_SIZE-thinking"
QA_ARGS="--max-tokens 600 --timeout 60 --num-responses 1 --escape-responses"

./batch.sh processed/$IN.tsv $T1_CHUNK $T1_CHUNK_SIZE \
| python3 ~/biodiversity-llms/scripts/nlp/qa.py "$PROMPT_THINKING" $QA_ARGS > results/$RES_PREFIX_THINKING.tsv
```

```bash
# PROMPT_ANSWER=$(printf "{8}\n\nDoes {3} {4} naturally occur in {7}, {6}, {5}? Only respond yes or no.")
PROMPT_ANSWER=$(printf "{8}\n\nCan {3} {4} be found in {7}, {6}, {5}? Only respond yes or no.")
RES_PREFIX_ANSWER="$IN-$T1_CHUNK-$T1_CHUNK_SIZE-answer"
QA_ARGS="--max-tokens 1 --timeout 10 --num-responses 10 --combine-responses"

cat results/$RES_PREFIX_THINKING.tsv \
| mlr --tsvlite cut -f kingdom,phylum,family,genus,specificepithet,country,stateprovince,county,responses \
| mlr --tsvlite rename responses,context \
| python3 ~/biodiversity-llms/scripts/nlp/qa.py "$PROMPT_ANSWER" $QA_ARGS > results/$RES_PREFIX_ANSWER.tsv
```
