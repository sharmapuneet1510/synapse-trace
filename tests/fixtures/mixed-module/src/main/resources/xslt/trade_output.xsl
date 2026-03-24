<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template name="TradeOutput" match="TradeDTO">
    <TradeMessage>
      <N_EFFECTIVE_DATE>
        <xsl:value-of select="effectiveDate"/>
      </N_EFFECTIVE_DATE>
      <N_COUNTERPARTY_2>
        <xsl:value-of select="counterpartyName"/>
      </N_COUNTERPARTY_2>
      <N_TRADE_AMOUNT>
        <xsl:value-of select="tradeAmount"/>
      </N_TRADE_AMOUNT>
    </TradeMessage>
  </xsl:template>

</xsl:stylesheet>
