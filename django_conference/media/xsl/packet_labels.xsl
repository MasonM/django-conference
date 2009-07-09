<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
      xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
      xmlns:fo="http://www.w3.org/1999/XSL/Format">
    <xsl:output method="xml" indent="yes"/>
    <xsl:template match="/">
        <fo:root>
            <fo:layout-master-set>
                <fo:simple-page-master master-name="packet-labels"
                    page-height="11in" page-width="8.5in"
                    margin-left="1.3cm" margin-right="1.3cm"
                    margin-top="0.5cm" margin-bottom="0.5cm">
                    <fo:region-body/>
                </fo:simple-page-master>
            </fo:layout-master-set>
            <fo:page-sequence master-reference="packet-labels">
                <fo:flow flow-name="xsl-region-body"  background-color="white"
                    font-family="Verdana" font-size="10pt" text-align="left">
                    <fo:table>
                        <fo:table-body>
                            <!-- 
                            wraps table after two columns
                            got this code from http://forums.mozillazine.org/viewtopic.php?f=5&t=136981
                            -->
                            <xsl:for-each select="registrations/registration[((position() - 1) mod 3) = 0]">>
                                <fo:table-row>
                                    <xsl:for-each select=". | following-sibling::*[position() &lt; 3]">
                                        <fo:table-cell width="2.63in" height="1in" overflow="hidden" 
                                            page-break-inside="avoid">
                                            <xsl:if test="@food_type != 'N'">
                                                <fo:block text-align="right">
                                                    <xsl:value-of select="@food_type"/>
                                                </fo:block>
                                            </xsl:if>
                                            <fo:block>
                                                <xsl:value-of select="@name"/>
                                            </fo:block>
                                            <fo:block>
                                                <xsl:value-of select="@institution"/>
                                            </fo:block>
                                            <fo:block>
                                                Type: <xsl:value-of select="@type"/>
                                            </fo:block>
                                            <xsl:if test="extra[@name = 'HSS Abstracts']">
                                            <fo:block>
                                                Abstracts: <xsl:value-of select="extra[@name = 'HSS Abstracts']/@quantity"/>
                                            </fo:block>
                                            </xsl:if>
                                        </fo:table-cell>
                                    </xsl:for-each>
                                </fo:table-row>
                            </xsl:for-each>
                        </fo:table-body>
                    </fo:table>
                </fo:flow>
            </fo:page-sequence>
        </fo:root>
    </xsl:template>
</xsl:stylesheet>
