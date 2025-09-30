<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" 
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:ltx="http://dlmf.nist.gov/LaTeXML"
                xmlns:m="http://www.w3.org/1998/Math/MathML"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="ltx m">

  <xsl:output method="xml" encoding="UTF-8" indent="yes" 
              doctype-public="-//W3C//DTD XHTML 1.1//EN"
              doctype-system="http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd"/>

  <!-- Root template -->
  <xsl:template match="/">
    <html xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <title>
          <xsl:choose>
            <xsl:when test="//ltx:title[1]">
              <xsl:value-of select="//ltx:title[1]"/>
            </xsl:when>
            <xsl:otherwise>Academic Paper</xsl:otherwise>
          </xsl:choose>
        </title>
        <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=utf-8"/>
        <style type="text/css">
          body { 
            font-family: "Times New Roman", serif; 
            line-height: 1.6; 
            margin: 2em; 
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 2em;
          }
          
          h1, h2, h3 { 
            color: #333; 
            margin-top: 2em; 
            margin-bottom: 0.5em;
            font-weight: bold;
          }
          
          h1 { font-size: 1.8em; text-align: center; margin-bottom: 1em; }
          h2 { font-size: 1.4em; border-bottom: 2px solid #333; padding-bottom: 0.3em; }
          h3 { font-size: 1.2em; }
          
          .section-title { 
            font-size: 1.3em; 
            font-weight: bold; 
            margin: 2em 0 1em 0; 
            color: #2c3e50;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 0.3em;
          }
          
          .subsection-title { 
            font-size: 1.1em; 
            font-weight: bold; 
            margin: 1.5em 0 0.8em 0; 
            color: #34495e;
          }
          
          p { 
            margin: 1em 0; 
            text-align: justify; 
            text-indent: 1.5em;
          }
          
          p:first-child { text-indent: 0; }
          
          .equation { 
            margin: 1.5em 0; 
            text-align: center; 
            border: 1px solid #bdc3c7; 
            padding: 1.2em; 
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          }
          
          .equation-content { 
            font-size: 1.3em; 
            margin-bottom: 0.8em; 
            font-family: "Times New Roman", serif;
            font-style: italic;
          }
          
          .equation-number { 
            text-align: right; 
            font-weight: bold; 
            color: #495057; 
            margin-top: 0.5em;
            font-size: 0.9em;
          }
          
          .table-container {
            margin: 1.5em 0;
            page-break-inside: avoid;
            break-inside: avoid;
          }
          
          .table-caption {
            font-weight: bold;
            margin-bottom: 0.8em;
            text-align: center;
            color: #2c3e50;
          }
          
          .table { 
            margin: 0 auto; 
            border-collapse: collapse; 
            width: 95%; 
            max-width: 95%;
            background: white;
            font-size: 0.85em;
            page-break-inside: avoid;
            break-inside: avoid;
          }
          
          .table th, .table td { 
            border: 1px solid #ccc; 
            padding: 0.4em 0.6em; 
            text-align: left; 
            vertical-align: top;
            word-wrap: break-word;
            overflow-wrap: break-word;
          }
          
          .table th { 
            background-color: #f5f5f5; 
            color: #333;
            font-weight: bold; 
            text-align: center;
          }
          
          .table tr:nth-child(even) {
            background-color: #fafafa;
          }
          
          .figure { 
            margin: 1.5em 0; 
            text-align: center; 
            border: 1px solid #bdc3c7; 
            padding: 1.2em;
            background: #f8f9fa;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          }
          
          .figure-caption { 
            font-style: italic; 
            margin-top: 1em; 
            color: #495057;
            font-weight: bold;
          }
          
          .graphics-placeholder {
            background: #e9ecef;
            border: 2px dashed #adb5bd;
            padding: 2em;
            border-radius: 4px;
            color: #6c757d;
            font-style: italic;
          }
          
          .math { 
            font-style: italic; 
            font-family: "Times New Roman", serif;
          }
          
          .section, .subsection {
            margin-bottom: 2em;
          }
          
          .para {
            margin-bottom: 1em;
          }
        </style>
      </head>
      <body>
        <xsl:apply-templates select="//ltx:document"/>
      </body>
    </html>
  </xsl:template>

  <!-- Document -->
  <xsl:template match="ltx:document">
    <xsl:apply-templates select="ltx:section | ltx:subsection"/>
  </xsl:template>

  <!-- Sections -->
  <xsl:template match="ltx:section">
    <div class="section">
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="ltx:title">
        <h2 class="section-title">
          <xsl:apply-templates select="ltx:title"/>
        </h2>
      </xsl:if>
      <div class="section-content">
        <xsl:apply-templates select="ltx:para | ltx:subsection | ltx:equation | ltx:figure | ltx:table"/>
      </div>
    </div>
  </xsl:template>

  <!-- Subsections -->
  <xsl:template match="ltx:subsection">
    <div class="subsection">
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="ltx:title">
        <h3 class="subsection-title">
          <xsl:apply-templates select="ltx:title"/>
        </h3>
      </xsl:if>
      <div class="subsection-content">
        <xsl:apply-templates select="ltx:para | ltx:equation | ltx:figure | ltx:table"/>
      </div>
    </div>
  </xsl:template>

  <!-- Paragraphs -->
  <xsl:template match="ltx:para">
    <div class="para">
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <!-- Paragraph content (p elements) -->
  <xsl:template match="ltx:p">
    <p><xsl:apply-templates/></p>
  </xsl:template>

  <!-- Equations -->
  <xsl:template match="ltx:equation">
    <div class="equation">
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      
      <div class="equation-content">
        <xsl:choose>
          <xsl:when test="ltx:Math/m:math">
            <xsl:copy-of select="ltx:Math/m:math"/>
          </xsl:when>
          <xsl:when test="ltx:Math/@tex">
            <span class="math"><xsl:value-of select="ltx:Math/@tex"/></span>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates select="ltx:Math"/>
          </xsl:otherwise>
        </xsl:choose>
      </div>
      
      <xsl:if test="ltx:tags/ltx:tag[1]">
        <div class="equation-number">
          (<xsl:value-of select="ltx:tags/ltx:tag[1]"/>)
        </div>
      </xsl:if>
    </div>
  </xsl:template>

  <!-- Figures -->
  <xsl:template match="ltx:figure">
    <div class="figure">
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      
      <div class="figure-content">
        <xsl:choose>
          <xsl:when test="ltx:graphics">
            <xsl:apply-templates select="ltx:graphics"/>
          </xsl:when>
          <xsl:otherwise>
            <div class="graphics-placeholder">
              [Figure content not available]
            </div>
          </xsl:otherwise>
        </xsl:choose>
      </div>
      
      <xsl:if test="ltx:caption">
        <div class="figure-caption">
          <xsl:apply-templates select="ltx:caption"/>
        </div>
      </xsl:if>
    </div>
  </xsl:template>

  <!-- Tables - CORRECTED with proper ltx: namespace -->
  <xsl:template match="ltx:table">
    <div class="table-container">
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      
      <xsl:if test="ltx:caption">
        <h4 class="table-caption">
          <xsl:apply-templates select="ltx:caption"/>
        </h4>
      </xsl:if>
      
      <xsl:apply-templates select=".//ltx:tabular"/>
    </div>
  </xsl:template>

  <!-- Tabular - CORRECTED: all elements are in ltx namespace -->
  <xsl:template match="ltx:tabular">
    <table class="table">
      <xsl:apply-templates select="ltx:tbody | ltx:thead | ltx:tr"/>
    </table>
  </xsl:template>

  <!-- Table structure elements - CORRECTED with ltx: namespace -->
  <xsl:template match="ltx:thead">
    <thead><xsl:apply-templates select="ltx:tr"/></thead>
  </xsl:template>

  <xsl:template match="ltx:tbody">
    <tbody><xsl:apply-templates select="ltx:tr"/></tbody>
  </xsl:template>

  <!-- Table rows - CORRECTED with ltx: namespace -->
  <xsl:template match="ltx:tr">
    <tr>
      <xsl:apply-templates select="ltx:td | ltx:th"/>
    </tr>
  </xsl:template>

  <!-- Table cells - CORRECTED with ltx: namespace -->
  <xsl:template match="ltx:td">
    <td>
      <xsl:if test="@colspan">
        <xsl:attribute name="colspan"><xsl:value-of select="@colspan"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="@align">
        <xsl:attribute name="style">text-align: <xsl:value-of select="@align"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </td>
  </xsl:template>

  <xsl:template match="ltx:th">
    <th>
      <xsl:if test="@colspan">
        <xsl:attribute name="colspan"><xsl:value-of select="@colspan"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="@align">
        <xsl:attribute name="style">text-align: <xsl:value-of select="@align"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </th>
  </xsl:template>

  <!-- Titles -->
  <xsl:template match="ltx:title">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- Captions -->
  <xsl:template match="ltx:caption">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- Math elements -->
  <xsl:template match="ltx:Math">
    <xsl:choose>
      <xsl:when test="m:math">
        <xsl:copy-of select="m:math"/>
      </xsl:when>
      <xsl:when test="@tex">
        <span class="math"><xsl:value-of select="@tex"/></span>
      </xsl:when>
      <xsl:otherwise>
        <span class="math"><xsl:apply-templates/></span>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Graphics -->
  <xsl:template match="ltx:graphics">
    <div class="graphics-placeholder">
      [Figure: <xsl:value-of select="@graphic"/>]
    </div>
  </xsl:template>

  <!-- Cross-references -->
  <xsl:template match="ltx:ref">
    <span class="ref">[<xsl:value-of select="@labelref"/>]</span>
  </xsl:template>

  <!-- Citations -->
  <xsl:template match="ltx:cite">
    <span class="citation">[<xsl:apply-templates/>]</span>
  </xsl:template>

  <!-- LaTeXML tag elements -->
  <xsl:template match="ltx:tag">
    <strong><xsl:apply-templates/><xsl:value-of select="@close"/></strong>
  </xsl:template>

  <!-- LaTeXML text elements with formatting -->
  <xsl:template match="ltx:text">
    <xsl:choose>
      <xsl:when test="@font='italic'">
        <em><xsl:apply-templates/></em>
      </xsl:when>
      <xsl:when test="@font='bold'">
        <strong><xsl:apply-templates/></strong>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Tags (ignore in content, handled specifically where needed) -->
  <xsl:template match="ltx:tags"/>

  <!-- Default text processing -->
  <xsl:template match="text()">
    <xsl:value-of select="."/>
  </xsl:template>

  <!-- Default element processing -->
  <xsl:template match="*">
    <xsl:apply-templates/>
  </xsl:template>

</xsl:stylesheet>
