<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template name="SettlementMapping" match="Settlement">
    <SettlementMessage>
      <N_SETTLEMENT_DATE>
        <xsl:value-of select="settlementDate"/>
      </N_SETTLEMENT_DATE>
      <N_TRADE_AMOUNT>
        <xsl:value-of select="tradeAmount"/>
      </N_TRADE_AMOUNT>
      <N_COUNTERPARTY_ID>
        <xsl:value-of select="counterpartyId"/>
      </N_COUNTERPARTY_ID>
    </SettlementMessage>
  </xsl:template>

</xsl:stylesheet>
