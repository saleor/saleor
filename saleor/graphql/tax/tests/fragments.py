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


TAX_CLASS_FRAGMENT = """
  fragment TaxClass on TaxClass {
    id
    name
    isDefault
    countries {
      id
      country {
        code
        country
      }
      rate
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

TAX_COUNTRY_CONFIGURATION_FRAGMENT = """
  fragment TaxCountryConfiguration on TaxCountryConfiguration {
    country {
      code
    }
    taxClassCountryRates {
      rate
      taxClass {
        id
        name
      }
    }
  }
"""
