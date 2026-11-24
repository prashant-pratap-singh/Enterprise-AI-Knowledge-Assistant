# Evaluation Framework

This directory houses the evaluation benchmarks and synthetic ground-truth datasets for the Enterprise AI Knowledge Assistant.

## Metrics Evaluated
1. **Retrieval Performance:**
   - Recall@K
   - Precision@K
   - Mean Reciprocal Rank (MRR)
   - Context Precision & Recall
2. **Generation Quality:**
   - Faithfulness (claim groundedness)
   - Answer Relevance
   - Citation Correctness (pointing to real retrieved chunks & pages)
3. **Operational Metrics:**
   - End-to-end Latency (ms)
   - Token Consumption
   - Estimated API Cost

## Running Benchmarks
Automated evaluation scripts will be executed in Phase 12 against standard test datasets located in `datasets/`.
