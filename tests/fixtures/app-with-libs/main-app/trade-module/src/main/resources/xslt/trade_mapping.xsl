<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template name="TradeMapping" match="TradeDTO">
    <TradeMessage>
      <N_TRADE_ID>
        <xsl:value-of select="tradeId"/>
      </N_TRADE_ID>
      <N_EFFECTIVE_DATE>
        <xsl:value-of select="effectiveDate"/>
      </N_EFFECTIVE_DATE>
      <N_COUNTERPARTY>
        <xsl:value-of select="counterpartyName"/>
      </N_COUNTERPARTY>
      <N_NOTIONAL>
        <xsl:value-of select="notionalAmount"/>
      </N_NOTIONAL>
    </TradeMessage>
  </xsl:template>

</xsl:stylesheet>
