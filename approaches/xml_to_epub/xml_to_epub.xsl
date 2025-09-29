<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" 
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:ap="http://example.com/academic-paper"
                xmlns:xhtml="http://www.w3.org/1999/xhtml"
                xmlns:mathml="http://www.w3.org/1998/Math/MathML"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="ap">

  <xsl:output method="xml" 
              doctype-public="-//W3C//DTD XHTML 1.1//EN"
              doctype-system="http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd"
              encoding="UTF-8" 
              indent="yes"/>

  <!-- Root template -->
  <xsl:template match="/ap:paper">
    <html xmlns="http://www.w3.org/1999/xhtml" lang="en">
      <head>
        <meta charset="utf-8"/>
        <title><xsl:value-of select="ap:metadata/ap:title"/></title>
        <link rel="stylesheet" type="text/css" href="styles.css"/>
      </head>
      <body>
        
        <!-- Table of Contents -->
        <xsl:call-template name="generate-toc"/>
        
        <!-- Title Page -->
        <div class="title-page">
          <h1 class="title"><xsl:value-of select="ap:metadata/ap:title"/></h1>
          <xsl:call-template name="generate-authors"/>
          <xsl:call-template name="generate-publication-info"/>
        </div>

        <!-- Abstract -->
        <div class="abstract">
          <h2>Abstract</h2>
          <xsl:apply-templates select="ap:metadata/ap:abstract"/>
        </div>

        <!-- Sections -->
        <xsl:apply-templates select="ap:sections/ap:section"/>

        <!-- Tables -->
        <xsl:if test="ap:tables/ap:table">
          <div class="tables">
            <h2>Tables</h2>
            <xsl:apply-templates select="ap:tables/ap:table"/>
          </div>
        </xsl:if>

        <!-- Figures -->
        <xsl:if test="ap:figures/ap:figure">
          <div class="figures">
            <h2>Figures</h2>
            <xsl:apply-templates select="ap:figures/ap:figure"/>
          </div>
        </xsl:if>

        <!-- References -->
        <xsl:if test="ap:references/ap:reference">
          <div class="references">
            <h2 id="references">References</h2>
            <ol class="reference-list">
              <xsl:apply-templates select="ap:references/ap:reference"/>
            </ol>
          </div>
        </xsl:if>

      </body>
    </html>
  </xsl:template>

  <!-- Table of Contents -->
  <xsl:template name="generate-toc">
    <div class="toc">
      <h2>Table of Contents</h2>
      <ul>
        <xsl:for-each select="ap:sections/ap:section">
          <li><a href="#{@id}"><xsl:value-of select="ap:title"/></a></li>
          <xsl:for-each select="ap:subsections/ap:subsection">
            <li class="subsection"><a href="#{@id}"><xsl:value-of select="ap:title"/></a></li>
          </xsl:for-each>
        </xsl:for-each>
      </ul>
    </div>
  </xsl:template>

  <!-- Authors -->
  <xsl:template name="generate-authors">
    <div class="authors">
      <p class="author-names">
        <xsl:for-each select="ap:metadata/ap:authors/ap:author">
          <xsl:value-of select="ap:name"/>
          <xsl:if test="position() != last()">, </xsl:if>
        </xsl:for-each>
      </p>
      <xsl:for-each select="ap:metadata/ap:authors/ap:author">
        <p class="affiliation">
          <xsl:value-of select="ap:affiliation"/>
          <xsl:if test="ap:email"> (<xsl:value-of select="ap:email"/>)</xsl:if>
        </p>
      </xsl:for-each>
    </div>
  </xsl:template>

  <!-- Publication Info -->
  <xsl:template name="generate-publication-info">
    <xsl:if test="ap:metadata/ap:publication_info">
      <div class="publication-info">
        <xsl:if test="ap:metadata/ap:publication_info/ap:venue">
          <p class="venue"><xsl:value-of select="ap:metadata/ap:publication_info/ap:venue"/></p>
        </xsl:if>
        <xsl:if test="ap:metadata/ap:publication_info/ap:date">
          <p class="date"><xsl:value-of select="ap:metadata/ap:publication_info/ap:date"/></p>
        </xsl:if>
        <xsl:if test="ap:metadata/ap:publication_info/ap:arxiv_id">
          <p class="arxiv">arXiv:<xsl:value-of select="ap:metadata/ap:publication_info/ap:arxiv_id"/></p>
        </xsl:if>
      </div>
    </xsl:if>
  </xsl:template>

  <!-- Sections -->
  <xsl:template match="ap:section">
    <div class="section" id="{@id}">
      <xsl:element name="h{@level}">
        <xsl:attribute name="class">section-title</xsl:attribute>
        <xsl:value-of select="ap:title"/>
      </xsl:element>
      
      <xsl:if test="ap:content">
        <div class="section-content">
          <xsl:apply-templates select="ap:content"/>
        </div>
      </xsl:if>

      <!-- Subsections -->
      <xsl:apply-templates select="ap:subsections/ap:subsection"/>
    </div>
  </xsl:template>

  <!-- Subsections -->
  <xsl:template match="ap:subsection">
    <div class="subsection" id="{@id}">
      <xsl:element name="h{@level}">
        <xsl:attribute name="class">subsection-title</xsl:attribute>
        <xsl:value-of select="ap:title"/>
      </xsl:element>
      
      <xsl:if test="ap:content">
        <div class="subsection-content">
          <xsl:apply-templates select="ap:content"/>
        </div>
      </xsl:if>
    </div>
  </xsl:template>

  <!-- Rich Content (XHTML + MathML) -->
  <xsl:template match="ap:content | ap:abstract">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- XHTML Elements - Copy through with namespace conversion -->
  <xsl:template match="xhtml:p">
    <p><xsl:apply-templates/></p>
  </xsl:template>

  <xsl:template match="xhtml:em">
    <em><xsl:apply-templates/></em>
  </xsl:template>

  <xsl:template match="xhtml:strong">
    <strong><xsl:apply-templates/></strong>
  </xsl:template>

  <!-- MathML Elements - Convert to readable HTML -->
  <xsl:template match="mathml:math">
    <span class="math">
      <xsl:if test="@display='block'">
        <xsl:attribute name="class">math math-display</xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- MathML in default namespace (from inline content) -->
  <xsl:template match="*[local-name()='math' and namespace-uri()='http://www.w3.org/1998/Math/MathML']">
    <xsl:copy-of select="."/>
  </xsl:template>

  <xsl:template match="mathml:mi">
    <em><xsl:value-of select="."/></em>
  </xsl:template>

  <xsl:template match="mathml:mo">
    <xsl:value-of select="."/>
  </xsl:template>

  <xsl:template match="mathml:mtext">
    <xsl:value-of select="."/>
  </xsl:template>


  <!-- Citations -->
  <xsl:template match="ap:citation">
    <span class="citation">[<xsl:value-of select="."/>]</span>
  </xsl:template>


  <!-- Tables -->
  <xsl:template match="ap:table">
    <div class="table" id="{@id}">
      <h4 class="table-title">
        <strong>Table <xsl:value-of select="ap:number"/></strong>
      </h4>
      <p class="table-caption" style="font-style: italic;">
        <xsl:value-of select="ap:caption"/>
      </p>
      <table>
        <thead>
          <tr>
            <xsl:for-each select="ap:headers/ap:header">
              <th>
                <xsl:if test="@colspan">
                  <xsl:attribute name="colspan"><xsl:value-of select="@colspan"/></xsl:attribute>
                </xsl:if>
                <xsl:value-of select="."/>
              </th>
            </xsl:for-each>
          </tr>
        </thead>
        <tbody>
          <xsl:for-each select="ap:rows/ap:row">
            <tr>
              <xsl:for-each select="ap:cell">
                <td>
                  <xsl:if test="@colspan">
                    <xsl:attribute name="colspan"><xsl:value-of select="@colspan"/></xsl:attribute>
                  </xsl:if>
                  <xsl:value-of select="."/>
                </td>
              </xsl:for-each>
            </tr>
          </xsl:for-each>
        </tbody>
      </table>
    </div>
  </xsl:template>

  <!-- Figures -->
  <xsl:template match="ap:figure">
    <div class="figure" id="{@id}">
      <figure>
        <xsl:if test="ap:source_reference">
          <img src="{ap:source_reference}.png" alt="{ap:alt_text}" class="figure-image"/>
        </xsl:if>
        <xsl:if test="not(ap:source_reference)">
          <div class="figure-placeholder">
            <p class="figure-description"><xsl:value-of select="ap:description"/></p>
          </div>
        </xsl:if>
        <figcaption><xsl:value-of select="ap:caption"/></figcaption>
      </figure>
    </div>
  </xsl:template>

  <!-- Equations -->
  <xsl:template match="ap:equation">
    <div class="equation" id="{@id}">
      <div class="equation-content">
        <xsl:apply-templates select="ap:content"/>
      </div>
      <xsl:if test="ap:description">
        <div class="equation-description">
          <xsl:value-of select="ap:description"/>
        </div>
      </xsl:if>
    </div>
  </xsl:template>

  <!-- References -->
  <xsl:template match="ap:reference">
    <li id="{@id}" class="reference-item">
      <xsl:if test="ap:authors">
        <span class="ref-authors">
          <xsl:for-each select="ap:authors/ap:author">
            <xsl:value-of select="."/>
            <xsl:if test="position() != last()">, </xsl:if>
          </xsl:for-each>
        </span>. 
      </xsl:if>
      
      <xsl:if test="ap:title">
        <span class="ref-title">"<xsl:value-of select="ap:title"/>"</span>. 
      </xsl:if>
      
      <xsl:if test="ap:venue">
        <span class="ref-venue"><xsl:value-of select="ap:venue"/></span>, 
      </xsl:if>
      
      <xsl:if test="ap:year">
        <span class="ref-year"><xsl:value-of select="ap:year"/></span>.
      </xsl:if>
    </li>
  </xsl:template>

  <!-- Default text handling -->
  <xsl:template match="text()">
    <xsl:value-of select="."/>
  </xsl:template>

</xsl:stylesheet>
