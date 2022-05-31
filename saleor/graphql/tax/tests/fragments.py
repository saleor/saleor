TAX_CONFIGURATION_FRAGMENT = """
  fragment TaxConfiguration on TaxConfiguration {
    id
    channel {
      id
      name
    }
    chargeTaxes
    displayGrossPrices
    pricesEnteredWithTax
    countries {
      country {
        code
        country
      }
      chargeTaxes
      displayGrossPrices
    }
    metadata {
      key
      value
    }
    privateMetadata {
      key
      value
    }
  }
"""
