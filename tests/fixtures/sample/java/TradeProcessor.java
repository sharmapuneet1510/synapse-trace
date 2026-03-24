package com.bank.trade;

import com.bank.dto.TradeDTO;
import com.bank.dto.CounterpartyDTO;

public class TradeProcessor {

    private TradeMapper mapper;
    private CounterpartyService counterpartyService;

    public TradeDTO processIncoming(String xmlPayload) {
        TradeDTO trade = unmarshaller.unmarshal(xmlPayload, TradeDTO.class);
        CounterpartyDTO cp = jsonMapper.readValue(cpJson, CounterpartyDTO.class);

        enrichTrade(trade, cp);
        return trade;
    }

    private void enrichTrade(TradeDTO trade, CounterpartyDTO cp) {
        trade.setCounterpartyName(cp.getCounterpartyName());
        trade.setCounterpartyId(cp.getCounterpartyId());
        trade.setTradeAmount(cp.getNotionalAmount());
        trade.setSettlementDate(cp.getSettlementDate());

        mapper.validate(trade);
        counterpartyService.enrich(cp);
    }
}
