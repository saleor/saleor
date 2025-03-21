ADDRESS_FRAGMENT = """
  fragment Address on Address {
    id
    firstName
    lastName
    companyName
    streetAddress1
    streetAddress2
    city
    cityArea
    postalCode
    countryArea
    phone
    country {
        code
    }
  }
"""
