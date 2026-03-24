package com.beta.settlement;

import javax.xml.transform.stream.StreamSource;

public class SettlementService {

    public void processSettlement(TradeDTO trade) {
        // Load settlement XSLT
        StreamSource xsltSource = new StreamSource("settlement_output.xsl");
        transformer.transform(tradeSource, settlementResult);

        settlement.setSettlementDate(trade.getSettlementDate());
        settlement.setTradeAmount(trade.getTradeAmount());

        // Cross-project field reference
        String tradeId = trade.get("N_TRADE_ID");
    }
}
