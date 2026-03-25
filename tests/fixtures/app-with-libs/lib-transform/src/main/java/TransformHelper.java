package com.acme.transform;

/**
 * Utility class in a separate library jar that provides
 * field mapping helper methods. The main app calls these.
 */
public class TransformHelper {

    public static String mapTradeField(String rawValue, String fieldKey) {
        // Internal mapping logic abstracted in the library
        if ("N_TRADE_ID".equals(fieldKey)) {
            return formatTradeId(rawValue);
        }
        return rawValue;
    }

    public static String formatTradeId(String raw) {
        return "TRD-" + raw;
    }

    public static String formatDate(String raw) {
        return raw;
    }
}
