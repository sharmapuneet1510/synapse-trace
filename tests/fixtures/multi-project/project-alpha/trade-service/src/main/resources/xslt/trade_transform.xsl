<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template name="TradeTransform" match="TradeDTO">
    <TradeMessage>
      <N_TRADE_ID>
        <xsl:value-of select="tradeId"/>
      </N_TRADE_ID>
      <N_EFFECTIVE_DATE>
        <xsl:value-of select="effectiveDate"/>
      </N_EFFECTIVE_DATE>
      <N_NOTIONAL_AMOUNT>
        <xsl:value-of select="notionalAmount"/>
      </N_NOTIONAL_AMOUNT>
    </TradeMessage>
  </xsl:template>

</xsl:stylesheet>
