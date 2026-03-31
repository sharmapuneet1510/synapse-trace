<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template name="TradeMapping" match="TradeDTO">
    <TradeOutput>
      <N_COUNTERPARTY_2>
        <xsl:value-of select="counterpartyName"/>
      </N_COUNTERPARTY_2>
      <N_COUNTERPARTY_ID>
        <xsl:value-of select="counterpartyId"/>
      </N_COUNTERPARTY_ID>
      <N_TRADE_AMOUNT>
        <xsl:value-of select="tradeAmount"/>
      </N_TRADE_AMOUNT>
      <N_SETTLEMENT_DATE>
        <xsl:value-of select="order/settlementDate"/>
      </N_SETTLEMENT_DATE>
    </TradeOutput>
  </xsl:template>

  <xsl:template name="CounterpartyMapping" match="CounterpartyDTO">
    <CounterpartyOutput>
      <CP_NAME>
        <xsl:value-of select="@name"/>
      </CP_NAME>
      <xsl:call-template name="TradeMapping"/>
    </CounterpartyOutput>
  </xsl:template>

</xsl:stylesheet>
