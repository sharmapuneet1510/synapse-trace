package com.acme.app.settlement;

import javax.xml.transform.stream.StreamSource;
import com.acme.fields.MessageKey;

public class SettlementProcessor {

    public void settle(TradeDTO trade) {
        StreamSource xsltSource = new StreamSource("settlement_output.xsl");
        transformer.transform(tradeSource, settlementResult);

        settlement.setSettlementDate(trade.getSettlementDate());
        settlement.setTradeAmount(trade.getTradeAmount());
        settlement.setCurrency(trade.getCurrency());

        String settlDate = trade.get(MessageKey.N_SETTLEMENT_DATE);
        String currency = trade.get(MessageKey.N_CURRENCY);
    }
}
