package com.acme.app.trade;

import javax.xml.transform.stream.StreamSource;
import com.acme.fields.MessageKey;
import com.acme.transform.TransformHelper;

/**
 * Main trade processing service. Uses:
 *   - MessageKey from lib-fields (external jar)
 *   - TransformHelper from lib-transform (external jar)
 *   - trade_mapping.xsl for XML transformation
 */
public class TradeService {

    public TradeDTO processIncoming(String xmlPayload) {
        // XSLT transformation
        StreamSource xsltSource = new StreamSource("trade_mapping.xsl");
        transformer.transform(xmlSource, result);

        // Unmarshal
        TradeDTO trade = mapper.readValue(resultXml, TradeDTO.class);

        // Field access via library constants
        String tradeId = trade.get(MessageKey.N_TRADE_ID);
        String effectiveDate = trade.get(MessageKey.N_EFFECTIVE_DATE);
        String counterparty = trade.get(MessageKey.N_COUNTERPARTY);
        String notional = trade.get(MessageKey.N_NOTIONAL);

        // Use library helper for transformation
        String formattedId = TransformHelper.mapTradeField(tradeId, "N_TRADE_ID");
        String formattedDate = TransformHelper.formatDate(effectiveDate);

        return trade;
    }
}
