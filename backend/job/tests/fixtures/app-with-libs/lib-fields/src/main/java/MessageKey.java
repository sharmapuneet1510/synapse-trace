package com.acme.fields;

/**
 * Shared field constants — this lives in a separate library jar.
 * The main app references these via MessageKey.N_TRADE_ID etc.
 */
public class MessageKey {
    public static final String N_TRADE_ID = "N_TRADE_ID";
    public static final String N_EFFECTIVE_DATE = "N_EFFECTIVE_DATE";
    public static final String N_COUNTERPARTY = "N_COUNTERPARTY";
    public static final String N_NOTIONAL = "N_NOTIONAL";
    public static final String N_CURRENCY = "N_CURRENCY";
    public static final String N_SETTLEMENT_DATE = "N_SETTLEMENT_DATE";
}
