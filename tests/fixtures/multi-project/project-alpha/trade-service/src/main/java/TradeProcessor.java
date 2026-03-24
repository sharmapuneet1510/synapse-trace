package com.alpha.trade;

import javax.xml.transform.stream.StreamSource;
import com.alpha.common.MessageKey;

public class TradeProcessor {

    public TradeDTO processIncoming(String xmlPayload) {
        // Load XSLT for trade transformation
        StreamSource xsltSource = new StreamSource("trade_transform.xsl");
        transformer.transform(xmlSource, result);

        TradeDTO trade = mapper.readValue(resultXml, TradeDTO.class);

        String tradeId = trade.get(MessageKey.N_TRADE_ID);
        String effectiveDate = trade.get(MessageKey.N_EFFECTIVE_DATE);
        String notional = trade.get(MessageKey.N_NOTIONAL_AMOUNT);

        return trade;
    }
}
