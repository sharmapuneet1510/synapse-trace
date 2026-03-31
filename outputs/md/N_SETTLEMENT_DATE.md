# Field Lineage: `N_SETTLEMENT_DATE`

| Property | Value |
|----------|-------|
| Trace ID | `dac55cd3-f085-4e67-b367-0e19d2376570` |
| Origin   | `JAVA` |
| Nodes    | 3 |
| Branches | 2 |
| Has XSLT | No |
| Has Java | Yes |

## Business Explanation

The field 'N_SETTLEMENT_DATE' is derived entirely within Java code. It is computed, enriched, or assigned during the Java processing pipeline. The field passes through 3 Java method(s): process, setNCleared, setNSettlementDate. The field value depends on 2 conditional outcome(s). Different business conditions may result in different values being assigned.   • When [ternary] report.setNCleared(trade.isCleared() == TRUE: value is set to '"Y"'.   • When [ternary] report.setNCleared(trade.isCleared() == FALSE: value is set to '"N")'.

## Technical Explanation

```
=== Technical Lineage Trace ===


[ Java Phase ]
  1. ClearingService.process() [/var/folders/c3/h4gsm_456jl_7887z1q79n1h0000gn/T/dl_test_egfy74z1/src/main/java/com/xxx/clearing/ClearingService.java:4]
     Type: PASS_THROUGH
     Conditions: report.setNCleared(trade.isCleared()
  2. ClearingReport.setNCleared() [/var/folders/c3/h4gsm_456jl_7887z1q79n1h0000gn/T/dl_test_egfy74z1/src/main/java/com/xxx/model/ClearingReport.java:4]
     Type: PASS_THROUGH
  3. ClearingReport.setNSettlementDate() [/var/folders/c3/h4gsm_456jl_7887z1q79n1h0000gn/T/dl_test_egfy74z1/src/main/java/com/xxx/model/ClearingReport.java:5]
     Type: PASS_THROUGH

[ Branch Analysis – 2 branches ]
  Branch: [ternary] report.setNCleared(trade.isCleared() == TRUE
    Outcome: "Y"
  Branch: [ternary] report.setNCleared(trade.isCleared() == FALSE
    Outcome: "N")
```

## Pipeline Steps

| # | Step | Type | Class / Template | Method | File | Line |
|---|------|------|-----------------|--------|------|------|
| 1 | ClearingService.process() | `PASS_THROUGH` | ClearingService | process | ClearingService.java | 4 |
| 2 | ClearingReport.setNCleared() | `PASS_THROUGH` | ClearingReport | setNCleared | ClearingReport.java | 4 |
| 3 | ClearingReport.setNSettlementDate() | `PASS_THROUGH` | ClearingReport | setNSettlementDate | ClearingReport.java | 5 |

## Branch Conditions

| Branch | Condition | Outcome |
|--------|-----------|---------|
| `25add8d8` | [ternary] report.setNCleared(trade.isCleared() == TRUE | "Y" |
| `6bc68bba` | [ternary] report.setNCleared(trade.isCleared() == FALSE | "N") |

## Ordered Pipeline

1. ClearingService.process()
2. ClearingReport.setNCleared()
3. ClearingReport.setNSettlementDate()
