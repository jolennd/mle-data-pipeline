# ADR 1: Revenue is total_amount, summed as is
Status: accepted
Context: The brief says daily revenue but not which column. Raw trips contain negative total_amount values (refunds and voids).
Decision: Revenue is total_amount. Negative values are summed as they are, not filtered or absolute-valued.
Consequences: Daily revenue is net of refunds and voids. The reconciliation check A2 uses the same column and the same sign handling.
Payment types 3 (no charge) and 4 (dispute) are kept in revenue. In January they are 430 trips and 1,724.45 of 1,093,822.36, about 0.16% of revenue.
