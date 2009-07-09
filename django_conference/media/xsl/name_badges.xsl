<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
      xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
      xmlns:fo="http://www.w3.org/1999/XSL/Format">
    <xsl:output method="xml" indent="yes"/>
    <xsl:template match="/">
        <fo:root>
            <fo:layout-master-set>
                <fo:simple-page-master master-name="badges"
                    page-height="11in" page-width="8.5in"
                    margin-left="0.25in" margin-right="0.25in"
                    margin-top="0.5cm" margin-bottom="0.5cm">
                    <fo:region-body/>
                </fo:simple-page-master>
            </fo:layout-master-set>
            <fo:page-sequence master-reference="badges">
                <fo:flow flow-name="xsl-region-body"  background-color="white"
                    font-family="Arial" font-size="12pt">
                    <fo:table>
                        <fo:table-body>
                            <!-- 
                            wraps table after two columns
                            got this code from http://forums.mozillazine.org/viewtopic.php?f=5&t=136981
                            -->
                            <xsl:for-each select="meeting/registrant[((position() - 1) mod 2) = 0]">>
                                <fo:table-row>
                                    <xsl:for-each select=". | following-sibling::*[position() &lt; 2]">
                                        <fo:table-cell width="4in" height="3in">
                                            <xsl:if test="@food_type != 'N'">
                                                <fo:block text-align="right">
                                                    <xsl:value-of select="@food_type"/>
                                                </fo:block>
                                            </xsl:if>
                                            <fo:block text-align="center" font-size="16pt">
                                                <xsl:value-of select="@name"/>
                                            </fo:block>
                                            <fo:block text-align="center">
                                                <xsl:value-of select="@institution"/>
                                            </fo:block>
                                            <fo:table>
                                                <fo:table-body>
                                                    <fo:table-row>
                                                        <fo:table-cell left="0" width="0.68in">
                                                            <fo:block>
                                                                <fo:external-graphic src="url('/media/HSSLogo.gif')"
                                                                    content-height="1.7in" content-width="0.68in"/>
                                                            </fo:block>
                                                        </fo:table-cell>
                                                        <fo:table-cell text-align="center"
                                                            margin-right="0.68in" padding-top="0.5in">
                                                            <fo:block left="50%">
                                                                <xsl:value-of select="@institution"/>
                                                            </fo:block>
                                                            <fo:block>
                                                                <xsl:value-of select="/meeting/@location"/> Meeting
                                                            </fo:block>
                                                            <fo:block>
                                                                <xsl:value-of select="/meeting/@year"/>
                                                            </fo:block>
                                                        </fo:table-cell>
                                                    </fo:table-row>
                                                </fo:table-body>
                                            </fo:table>
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
