package com.bank.common;

/**
 * Shared message field key constants used across all trading applications.
 * This is in a library repo that multiple apps depend on.
 */
public final class MessageKey {
    public static final String N_EFFECTIVE_DATE = "N_EFFECTIVE_DATE";
    public static final String N_COUNTERPARTY_2 = "N_COUNTERPARTY_2";
    public static final String N_TRADE_AMOUNT = "N_TRADE_AMOUNT";
    public static final String N_SETTLEMENT_DATE = "N_SETTLEMENT_DATE";
    public static final String N_CURRENCY_CODE = "N_CURRENCY_CODE";
    public static final String N_INSTRUMENT_ID = "N_INSTRUMENT_ID";

    private MessageKey() {}
}
