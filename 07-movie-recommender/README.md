# Content-Based Movie Recommender

A recommender system that suggests similar films from genre composition alone, using TF-IDF
vectorization and cosine similarity across the full MovieLens catalog — with fuzzy title matching so
users don't have to type a title exactly.

## Problem

Recommenders generally come in two flavors. Collaborative filtering learns from user behavior and
works well — until a new item arrives with no ratings, at which point it has nothing to work with.
Content-based filtering compares items by their own attributes and sidesteps that cold start
entirely. This project builds the content-based approach on movie genres, which are available for
every title the moment it enters the catalog.

## Data

**MovieLens 32M** — the movie metadata file, covering roughly 87,000 titles with `movieId`, `title`,
and a pipe-delimited `genres` field.

| File | Description |
|---|---|
| `data/movies.csv` | Movie catalog with titles and genre tags |
| `data/movielens_dataset_notes.txt` | Official dataset README and usage terms |

> The 32M ratings file (~877 MB) is not committed and is not needed — this approach is
> content-based, so it never touches user ratings. That is the point of it.

## Approach

1. **Vectorize genres with TF-IDF.** The key detail is the tokenizer: genres arrive as
   pipe-delimited strings (`Adventure|Children|Fantasy`), so a custom `token_pattern` of `[^|]+`
   splits on the pipe and treats each genre as a single token. The default word tokenizer would
   shred multi-word genres into meaningless fragments.

   TF-IDF rather than raw counts also means a rare genre like *Film-Noir* carries more signal than a
   near-universal one like *Drama* — which is exactly the weighting a recommender wants.

2. **Cosine similarity** between the query film's genre vector and every other film in the catalog,
   ranked to produce the top matches.

3. **Fuzzy title matching with `rapidfuzz`**, so a user typing an approximate or misspelled title
   still resolves to the right film. The system echoes back which title it matched before returning
   results — a small interface decision that prevents silent wrong answers.

## Key findings

- Genre-only similarity produces **coherent, defensible recommendations**. Querying *Jumanji (1995)*
  returns titles sharing its `Adventure|Children|Fantasy` profile — *Pete's Dragon (2016)* and
  similar family adventure films.
- The approach **has no cold-start problem**: a film released today can be recommended immediately,
  because its genres are known at catalog entry.
- Fuzzy matching materially changes usability. Exact-match lookup fails on any typo or partial
  title, which in a real interface means most queries.

## What's in this folder

```
code/          Recommender notebook (TF-IDF → cosine similarity → fuzzy lookup)
data/          MovieLens movie catalog and dataset notes
deliverables/  Exported notebook PDF
```

## Tools

Python · scikit-learn (TfidfVectorizer, cosine_similarity) · rapidfuzz · pandas

## Notes and limitations

- **Genre is a coarse signal.** Two films sharing three genre tags can be nothing alike in tone,
  era, or quality. Adding cast, director, plot summary embeddings, or release year would sharpen
  results considerably.
- **No personalization.** The system recommends items similar to one item; it knows nothing about
  the user. A production system would blend this with collaborative filtering — content-based for
  cold start, collaborative once behavior data exists.
- No quantitative evaluation. Content-based recommenders are hard to score without user feedback,
  and no offline metric was computed here — the assessment is qualitative inspection of results.
