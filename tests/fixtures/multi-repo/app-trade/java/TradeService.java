package com.bank.trade.service;

import com.bank.common.MessageKey;
import com.bank.common.FieldNames;
import com.bank.trade.dto.TradeDTO;

public class TradeService {

    private TradeRepository tradeRepo;

    public TradeDTO processMessage(Map<String, Object> message) {
        // Using library constants from lib-common
        String effectiveDate = (String) message.get(MessageKey.N_EFFECTIVE_DATE);
        String counterparty = (String) message.get(MessageKey.N_COUNTERPARTY_2);
        String amount = (String) message.get(MessageKey.N_TRADE_AMOUNT);
        String currency = (String) message.get(MessageKey.N_CURRENCY_CODE);

        // Also using string literals directly
        String instrument = (String) message.get("N_INSTRUMENT_ID");
        String status = (String) message.get("TRADE_STATUS");

        TradeDTO trade = mapper.readValue(payload, TradeDTO.class);

        // Field mappings using setters/getters
        trade.setEffectiveDate(source.getEffectiveDate());
        trade.setCounterpartyName(source.getCounterpartyName());
        trade.setTradeAmount(source.getTradeAmount());

        tradeRepo.save(trade);
        return trade;
    }
}
