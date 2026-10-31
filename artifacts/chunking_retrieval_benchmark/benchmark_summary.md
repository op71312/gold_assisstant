# Chunking retrieval benchmark summary

- Status: `completed_preliminary_candidate_queries`
- Ground Truth test candidates: 39; human-approved: 0; included candidates: 39; evidence-covered: 39; evaluated: 39
- Chunk methods: existing_baseline, recursive_fixed, structure_aware, semantic, adaptive; shared documents: 69

## Evidence-level metrics

```text
           method  query_count  evidence_recall@1  evidence_recall@10  evidence_recall@3  evidence_recall@5  hit_rate@1  hit_rate@10  hit_rate@3  hit_rate@5   mrr@10   ndcg@1  ndcg@10   ndcg@3   ndcg@5  precision@1  precision@10  precision@3  precision@5  source_attribution_accuracy@1  source_attribution_accuracy@10  source_attribution_accuracy@3  source_attribution_accuracy@5
existing_baseline           39           0.487179            0.884615           0.794872           0.794872    0.538462     0.948718    0.846154    0.846154 0.693122 0.538462 0.712977 0.682845 0.682845     0.538462      0.094872     0.282051     0.169231                       0.923077                        0.602564                       0.769231                       0.702564
  recursive_fixed           39           0.564103            0.897436           0.769231           0.794872    0.615385     0.948718    0.820513    0.846154 0.730729 0.615385 0.745342 0.701772 0.711691     0.615385      0.097436     0.273504     0.169231                       0.923077                        0.679487                       0.794872                       0.784615
  structure_aware           39           0.333333            0.858974           0.743590           0.794872    0.384615     0.923077    0.794872    0.846154 0.598789 0.384615 0.636484 0.593710 0.614672     0.384615      0.092308     0.264957     0.169231                       0.923077                        0.666667                       0.820513                       0.784615
         semantic           39           0.243590            0.692308           0.474359           0.576923    0.307692     0.743590    0.538462    0.641026 0.445116 0.307692 0.472500 0.390266 0.433315     0.307692      0.076923     0.179487     0.128205                       0.923077                        0.807692                       0.871795                       0.846154
         adaptive           39           0.230769            0.858974           0.666667           0.743590    0.282051     0.923077    0.717949    0.794872 0.510419 0.282051 0.568764 0.497252 0.529257     0.282051      0.092308     0.239316     0.158974                       0.846154                        0.666667                       0.777778                       0.733333
```

Scores use source-grounded generated candidate labels without human review at user instruction; treat as exploratory, not verified Ground Truth.
The benchmark measures evidence retrieval and does not establish that economic events cause gold-price changes.
