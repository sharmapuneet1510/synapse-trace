package com.bank.trade.transform;

import javax.xml.transform.TransformerFactory;
import javax.xml.transform.stream.StreamSource;
import com.bank.trade.dto.TradeDTO;
import com.bank.common.MessageKey;

/**
 * Service that loads XSLT files, transforms XML, and maps to DTOs.
 * This is a typical enterprise pattern where Java and XSLT work together.
 */
public class TradeTransformService {

    private static final String TRADE_XSL = "trade_output.xsl";
    private static final String SETTLEMENT_XSL = "settlement_mapping.xsl";

    public TradeDTO transformIncoming(String xmlPayload) {
        // Load and apply XSLT transformation
        StreamSource xsltSource = new StreamSource("trade_output.xsl");
        Transformer transformer = factory.newTransformer(xsltSource);
        transformer.transform(xmlSource, result);

        // Unmarshal the transformed result to DTO
        TradeDTO trade = mapper.readValue(resultXml, TradeDTO.class);

        // Map fields using constants from the shared library
        String effectiveDate = trade.get(MessageKey.N_EFFECTIVE_DATE);
        String counterparty = trade.get(MessageKey.N_COUNTERPARTY_2);

        return trade;
    }

    public void processSettlement(TradeDTO trade) {
        // Load a second XSLT for settlement processing
        StreamSource settlementXsl = new StreamSource("settlement_mapping.xsl");
        Transformer stlTransformer = factory.newTransformer(settlementXsl);

        // Field mappings
        settlement.setSettlementDate(trade.getSettlementDate());
        settlement.setTradeAmount(trade.getTradeAmount());
        settlement.setCounterpartyId(trade.getCounterpartyId());

        stlTransformer.transform(tradeSource, settlementResult);
    }
}
