
"""
<script type="application/ld+json">
{
  "@context": "http://schema.org",
  "@type": "WebSite",
  "url": "http://www.example.com/",
  "name": "Generally the title",
   "author": {
      "@type": "Person",
      "name": "Jane Doe"
    },
  "description": "Any sort of description, I'd keep it short",
  "publisher": "publisher name",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "http://www.example.com/?s={search_term}",
    "query-input": "required name=search_term" }
    }
</script>
"""

def web_page_schema():
    data = {"@context": "http://schema.org",
            "@type": "WebSite",
            "url": "http://www.example.com/",
            "name": "Generally the title",
            "author": {"@type": "Person",
                       "name": "Jane Doe"},
            "description": "Any sort of description, I'd keep it short",
            "publisher": "publisher name",
            "potentialAction": {
                "@type": "SearchAction",
                "target": "http://www.example.com/?s={search_term}",
                "query-input": "required name=search_term" }
            }

    pass
