import { CountryList_shop_countries } from "../../../taxes/types/CountryList";

type CountryList = CountryList_shop_countries[];

export const countries: CountryList = [
  {
    __typename: "CountryDisplay",
    code: "AT",
    country: "Austria",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "passenger transport"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "pharmaceuticals"
        }
      ],
      standardRate: 20
    }
  },
  {
    __typename: "CountryDisplay",
    code: "BE",
    country: "Belgia",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 12,
          rateType: "restaurants"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "water"
        }
      ],
      standardRate: 21
    }
  },
  {
    __typename: "CountryDisplay",
    code: "BG",
    country: "Bułgaria",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "hotels"
        }
      ],
      standardRate: 20
    }
  },
  {
    __typename: "CountryDisplay",
    code: "CY",
    country: "Cypr",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "admission to sporting events"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "passenger transport"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "restaurants"
        }
      ],
      standardRate: 19
    }
  },
  {
    __typename: "CountryDisplay",
    code: "CZ",
    country: "Czechy",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "baby foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "admission to sporting events"
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "passenger transport"
        }
      ],
      standardRate: 21
    }
  },
  {
    __typename: "CountryDisplay",
    code: "DE",
    country: "Niemcy",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "passenger transport"
        }
      ],
      standardRate: 19
    }
  },
  {
    __typename: "CountryDisplay",
    code: "DK",
    country: "Dania",
    vat: {
      __typename: "VAT",
      reducedRates: [],
      standardRate: 25
    }
  },
  {
    __typename: "CountryDisplay",
    code: "EE",
    country: "Estonia",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "pharmaceuticals"
        }
      ],
      standardRate: 20
    }
  },
  {
    __typename: "CountryDisplay",
    code: "ES",
    country: "Hiszpania",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to sporting events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "passenger transport"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 4,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 4,
          rateType: "newspapers"
        }
      ],
      standardRate: 21
    }
  },
  {
    __typename: "CountryDisplay",
    code: "FI",
    country: "Finlandia",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to sporting events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "passenger transport"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 14,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 14,
          rateType: "restaurants"
        }
      ],
      standardRate: 24
    }
  },
  {
    __typename: "CountryDisplay",
    code: "FR",
    country: "Francja",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "accommodation"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to sporting events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "passenger transport"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "restaurants"
        },
        {
          __typename: "ReducedRate",
          rate: 2.1,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 2.1,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 5.5,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 5.5,
          rateType: "e-books"
        },
        {
          __typename: "ReducedRate",
          rate: 5.5,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 5.5,
          rateType: "medical"
        }
      ],
      standardRate: 20
    }
  },
  {
    __typename: "CountryDisplay",
    code: "GB",
    country: "Wielka Brytania",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "childrens clothing"
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "passenger transport"
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "property renovations"
        }
      ],
      standardRate: 20
    }
  },
  {
    __typename: "CountryDisplay",
    code: "GR",
    country: "Grecja",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "admission to sporting events"
        },
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 6.5,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 6.5,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 6.5,
          rateType: "newspapers"
        }
      ],
      standardRate: 24
    }
  },
  {
    __typename: "CountryDisplay",
    code: "HR",
    country: "Chorwacja",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "newspapers"
        }
      ],
      standardRate: 25
    }
  },
  {
    __typename: "CountryDisplay",
    code: "HU",
    country: "Węgry",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 18,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 18,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "pharmaceuticals"
        }
      ],
      standardRate: 27
    }
  },
  {
    __typename: "CountryDisplay",
    code: "IE",
    country: "Irlandia",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "childrens clothing"
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 4.8,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "admission to sporting events"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "restaurants"
        }
      ],
      standardRate: 23
    }
  },
  {
    __typename: "CountryDisplay",
    code: "IT",
    country: "Włochy",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "passenger transport"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "restaurants"
        },
        {
          __typename: "ReducedRate",
          rate: 4,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 4,
          rateType: "e-books"
        },
        {
          __typename: "ReducedRate",
          rate: 4,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 4,
          rateType: "medical"
        }
      ],
      standardRate: 22
    }
  },
  {
    __typename: "CountryDisplay",
    code: "LT",
    country: "Litwa",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "books"
        }
      ],
      standardRate: 21
    }
  },
  {
    __typename: "CountryDisplay",
    code: "LU",
    country: "Luksemburg",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 14,
          rateType: "advertising"
        },
        {
          __typename: "ReducedRate",
          rate: 14,
          rateType: "domestic fuel"
        },
        {
          __typename: "ReducedRate",
          rate: 14,
          rateType: "wine"
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "admission to sporting events"
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "e-books"
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "passenger transport"
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "restaurants"
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "bikes"
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "domestic services"
        }
      ],
      standardRate: 17
    }
  },
  {
    __typename: "CountryDisplay",
    code: "LV",
    country: "Łotwa",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 12,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 12,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 12,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 12,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 12,
          rateType: "pharmaceuticals"
        }
      ],
      standardRate: 21
    }
  },
  {
    __typename: "CountryDisplay",
    code: "MT",
    country: "Malta",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "e-books"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "hotels"
        }
      ],
      standardRate: 18
    }
  },
  {
    __typename: "CountryDisplay",
    code: "NL",
    country: "Holandia",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "accommodation"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "passenger transport"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "pharmaceuticals"
        }
      ],
      standardRate: 21
    }
  },
  {
    __typename: "CountryDisplay",
    code: "PL",
    country: "Polska",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "admission to sporting events"
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "passenger transport"
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "pharmaceuticals"
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "restaurants"
        }
      ],
      standardRate: 23
    }
  },
  {
    __typename: "CountryDisplay",
    code: "PT",
    country: "Portugalia",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "agricultural supplies"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "passenger transport"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "pharmaceuticals"
        }
      ],
      standardRate: 23
    }
  },
  {
    __typename: "CountryDisplay",
    code: "RO",
    country: "Rumunia",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "social housing"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "pharmaceuticals"
        }
      ],
      standardRate: 19
    }
  },
  {
    __typename: "CountryDisplay",
    code: "SE",
    country: "Szwecja",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 12,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "books"
        }
      ],
      standardRate: 25
    }
  },
  {
    __typename: "CountryDisplay",
    code: "SI",
    country: "Słowenia",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "admission to sporting events"
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "hotels"
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "newspapers"
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "pharmaceuticals"
        }
      ],
      standardRate: 22
    }
  },
  {
    __typename: "CountryDisplay",
    code: "SK",
    country: "Słowacja",
    vat: {
      __typename: "VAT",
      reducedRates: [
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to cultural events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "admission to entertainment events"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "books"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "foodstuffs"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "medical"
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "pharmaceuticals"
        }
      ],
      standardRate: 20
    }
  }
];
