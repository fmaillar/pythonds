<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:import href="./core/pretext-latex.xsl"/>
  <xsl:param name="latex.preamble.late">
    <xsl:text>&#10;% RM2 table padding&#10;</xsl:text>
    <xsl:text>\setlength{\tabcolsep}{2pt}&#10;</xsl:text>
  </xsl:param>
</xsl:stylesheet>
