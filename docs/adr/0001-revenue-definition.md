# ADR 1: Revenue is total_amount, summed as is
Status: accepted
Context: The brief says daily revenue but not which column. Raw trips contain negative total_amount values (refunds and voids).
Decision: Revenue is total_amount. Negative values are summed as they are, not filtered or absolute-valued.
Consequences: Daily revenue is net of refunds and voids. The reconciliation check A2 uses the same column and the same sign handling.
