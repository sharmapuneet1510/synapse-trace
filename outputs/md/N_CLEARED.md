# Field Lineage: `N_CLEARED`

| Property | Value |
|----------|-------|
| Trace ID | `c2c78c59-de2e-4c2f-85fe-8c35126cd4e4` |
| Origin   | `XSLT_THEN_JAVA` |
| Nodes    | 5 |
| Branches | 6 |
| Has XSLT | Yes |
| Has Java | Yes |

## Business Explanation

The field 'N_CLEARED' starts its journey in an XSLT stylesheet where it is initially extracted or mapped. It then flows into the Java layer where it may be further enriched, overridden, or finalised before appearing in the report. The field passes through 2 Java method(s): setNCleared, process. The field value depends on 4 conditional outcome(s). Different business conditions may result in different values being assigned.   • When [if] unknown condition == TRUE: value is set to 'Y'.   • When [if] unknown condition == FALSE: value is set to 'N'.   • When [ternary] report.setNCleared(trade.isCleared() == TRUE: value is set to '"Y"'.

## Technical Explanation

```
=== Technical Lineage Trace ===

[ XSLT Phase ]
  1. XSLT: buildClearingReport
     Location: /var/folders/c3/h4gsm_456jl_7887z1q79n1h0000gn/T/dl_test__5iwfq0c/xslt-module/src/main/resources/xslt/clearing.xsl:None
     Type: PASS_THROUGH
  2. XSLT: setClearedField
     Location: /var/folders/c3/h4gsm_456jl_7887z1q79n1h0000gn/T/dl_test__5iwfq0c/xslt-module/src/main/resources/xslt/clearing.xsl:None
     Type: PASS_THROUGH
     Conditions: 

[ Java Phase ]
  1. ClearingReport.setNCleared() [/var/folders/c3/h4gsm_456jl_7887z1q79n1h0000gn/T/dl_test__5iwfq0c/model-module/src/main/java/com/xxx/model/ClearingReport.java:4]
     Type: PASS_THROUGH
  2. ClearingService.process() [/var/folders/c3/h4gsm_456jl_7887z1q79n1h0000gn/T/dl_test__5iwfq0c/service-module/src/main/java/com/xxx/clearing/ClearingService.java:4]
     Type: PASS_THROUGH
     Conditions: report.setNCleared(trade.isCleared()

[ Branch Analysis – 4 branches ]
  Branch: [if] unknown condition == TRUE
    Outcome: Y
  Branch: [if] unknown condition == FALSE
    Outcome: N
  Branch: [ternary] report.setNCleared(trade.isCleared() == TRUE
    Outcome: "Y"
  Branch: [ternary] report.setNCleared(trade.isCleared() == FALSE
    Outcome: "N")
```

## Pipeline Steps

| # | Step | Type | Class / Template | Method | File | Line |
|---|------|------|-----------------|--------|------|------|
| 1 | XSLT: buildClearingReport | `PASS_THROUGH` | buildClearingReport | buildClearingReport | clearing.xsl | — |
| 2 | XSLT: setClearedField | `PASS_THROUGH` | setClearedField | setClearedField | clearing.xsl | — |
| 3 | ClearingReport.setNCleared() | `PASS_THROUGH` | ClearingReport | setNCleared | ClearingReport.java | 4 |
| 4 | ClearingService.process() | `PASS_THROUGH` | ClearingService | process | ClearingService.java | 4 |
| 5 | ClearingReport.setNSettlementDate() | `PASS_THROUGH` | ClearingReport | setNSettlementDate | ClearingReport.java | 5 |

## Branch Conditions

| Branch | Condition | Outcome |
|--------|-----------|---------|
| `b11f11bb` | [if] unknown condition == TRUE | Y |
| `4dc0b57c` | [if] unknown condition == FALSE | N |
| `747fc51e` | [ternary] report.setNCleared(trade.isCleared() == TRUE | "Y" |
| `70208b41` | [ternary] report.setNCleared(trade.isCleared() == FALSE | "N") |
| `510db825` | [ternary] report.setNCleared(trade.isCleared() == TRUE | "Y" |
| `8baf9f91` | [ternary] report.setNCleared(trade.isCleared() == FALSE | "N") |

## Ordered Pipeline

1. XSLT: buildClearingReport
2. XSLT: setClearedField
3. ClearingReport.setNCleared()
4. ClearingService.process()
