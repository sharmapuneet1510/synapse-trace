<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template name="SettlementOutput" match="Settlement">
    <SettlementMessage>
      <N_SETTLEMENT_DATE>
        <xsl:value-of select="settlementDate"/>
      </N_SETTLEMENT_DATE>
      <N_CURRENCY>
        <xsl:value-of select="currency"/>
      </N_CURRENCY>
    </SettlementMessage>
  </xsl:template>

</xsl:stylesheet>
