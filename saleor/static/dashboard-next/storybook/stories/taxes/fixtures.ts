import { CountryList_shop_countries } from "../../../taxes/types/CountryList";
import { TaxRateType } from "../../../types/globalTypes";

type CountryList = CountryList_shop_countries[];

export const countries: CountryList = [
  {
    __typename: "CountryDisplay",
    code: "AD",
    country: "Andora",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AE",
    country: "Zjednoczone Emiraty Arabskie",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AF",
    country: "Afganistan",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AG",
    country: "Antigua i Barbuda",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AI",
    country: "Anguilla",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AL",
    country: "Albania",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AM",
    country: "Armenia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AO",
    country: "Angola",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AQ",
    country: "Antarktyda",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AR",
    country: "Argentyna",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AS",
    country: "Samoa Amerykańskie",
    vat: null
  },
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
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "PHARMACEUTICALS" as TaxRateType
        }
      ],
      standardRate: 20
    }
  },
  {
    __typename: "CountryDisplay",
    code: "AU",
    country: "Australia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AW",
    country: "Aruba",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AX",
    country: "Wyspy Alandzkie",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "AZ",
    country: "Azerbejdżan",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BA",
    country: "Bośnia i Hercegowina",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BB",
    country: "Barbados",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BD",
    country: "Bangladesz",
    vat: null
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
          rateType: "RESTAURANTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "WATER" as TaxRateType
        }
      ],
      standardRate: 21
    }
  },
  {
    __typename: "CountryDisplay",
    code: "BF",
    country: "Burkina Faso",
    vat: null
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
          rateType: "HOTELS" as TaxRateType
        }
      ],
      standardRate: 20
    }
  },
  {
    __typename: "CountryDisplay",
    code: "BH",
    country: "Bahrajn",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BI",
    country: "Burundi",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BJ",
    country: "Benin",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BL",
    country: "Saint-Barthélemy",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BM",
    country: "Bermudy",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BN",
    country: "Brunei",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BO",
    country: "Boliwia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BQ",
    country: "Bonaire, Sint Eustatius i Saba",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BR",
    country: "Brazylia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BS",
    country: "Bahamy",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BT",
    country: "Bhutan",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BV",
    country: "Wyspa Bouveta",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BW",
    country: "Botswana",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BY",
    country: "Białoruś",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "BZ",
    country: "Belize",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CA",
    country: "Kanada",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CC",
    country: "Wyspy Kokosowe",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CD",
    country: "Kongo",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CF",
    country: "Republika Środkowoafrykańska",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CG",
    country: "Kongo",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CH",
    country: "Szwajcaria",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CI",
    country: "Wybrzeże Kości Słoniowej",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CK",
    country: "Wyspy Cooka",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CL",
    country: "Chile",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CM",
    country: "Kamerun",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CN",
    country: "Chiny",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CO",
    country: "Kolumbia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CR",
    country: "Kostaryka",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CU",
    country: "Kuba",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CV",
    country: "Republika Zielonego Przylądka",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CW",
    country: "Curaçao",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "CX",
    country: "Wyspa Bożego Narodzenia",
    vat: null
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
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "ADMISSION_TO_SPORTING_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "RESTAURANTS" as TaxRateType
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
          rateType: "BABY_FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "ADMISSION_TO_SPORTING_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 15,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
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
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
        }
      ],
      standardRate: 19
    }
  },
  {
    __typename: "CountryDisplay",
    code: "DJ",
    country: "Dżibuti",
    vat: null
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
    code: "DM",
    country: "Dominika",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "DO",
    country: "Dominikana",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "DZ",
    country: "Algeria",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "EC",
    country: "Ekwador",
    vat: null
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
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "PHARMACEUTICALS" as TaxRateType
        }
      ],
      standardRate: 20
    }
  },
  {
    __typename: "CountryDisplay",
    code: "EG",
    country: "Egipt",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "EH",
    country: "Sahara Zachodnia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "ER",
    country: "Erytrea",
    vat: null
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
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "ADMISSION_TO_SPORTING_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 4,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 4,
          rateType: "NEWSPAPERS" as TaxRateType
        }
      ],
      standardRate: 21
    }
  },
  {
    __typename: "CountryDisplay",
    code: "ET",
    country: "Etiopia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "EU",
    country: "Unia Europejska",
    vat: null
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
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "ADMISSION_TO_SPORTING_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 14,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 14,
          rateType: "RESTAURANTS" as TaxRateType
        }
      ],
      standardRate: 24
    }
  },
  {
    __typename: "CountryDisplay",
    code: "FJ",
    country: "Fidżi",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "FK",
    country: "Falklandy",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "FM",
    country: "Mikronezja",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "FO",
    country: "Wyspy Owcze",
    vat: null
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
          rateType: "ACCOMMODATION" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "ADMISSION_TO_SPORTING_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "RESTAURANTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 2.1,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 2.1,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5.5,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5.5,
          rateType: "E_BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5.5,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5.5,
          rateType: "MEDICAL" as TaxRateType
        }
      ],
      standardRate: 20
    }
  },
  {
    __typename: "CountryDisplay",
    code: "GA",
    country: "Gabon",
    vat: null
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
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "CHILDRENS_CLOTHING" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "PROPERTY_RENOVATIONS" as TaxRateType
        }
      ],
      standardRate: 20
    }
  },
  {
    __typename: "CountryDisplay",
    code: "GD",
    country: "Grenada",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GE",
    country: "Gruzja",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GF",
    country: "Gujana Francuska",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GG",
    country: "Guernsey",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GH",
    country: "Ghana",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GI",
    country: "Gibraltar",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GL",
    country: "Grenlandia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GM",
    country: "Gambia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GN",
    country: "Gwinea",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GP",
    country: "Gwadelupa",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GQ",
    country: "Gwinea Równikowa",
    vat: null
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
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "ADMISSION_TO_SPORTING_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6.5,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6.5,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6.5,
          rateType: "NEWSPAPERS" as TaxRateType
        }
      ],
      standardRate: 24
    }
  },
  {
    __typename: "CountryDisplay",
    code: "GS",
    country: "Georgia Południowa i Sandwich Południowy",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GT",
    country: "Gwatemala",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GU",
    country: "Guam",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GW",
    country: "Gwinea Bissau",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "GY",
    country: "Gujana",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "HK",
    country: "Hongkong",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "HM",
    country: "Wyspy Heard i McDonalda",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "HN",
    country: "Honduras",
    vat: null
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
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 13,
          rateType: "NEWSPAPERS" as TaxRateType
        }
      ],
      standardRate: 25
    }
  },
  {
    __typename: "CountryDisplay",
    code: "HT",
    country: "Haiti",
    vat: null
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
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 18,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "PHARMACEUTICALS" as TaxRateType
        }
      ],
      standardRate: 27
    }
  },
  {
    __typename: "CountryDisplay",
    code: "ID",
    country: "Indonezja",
    vat: null
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
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "CHILDRENS_CLOTHING" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 4.8,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "ADMISSION_TO_SPORTING_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "RESTAURANTS" as TaxRateType
        }
      ],
      standardRate: 23
    }
  },
  {
    __typename: "CountryDisplay",
    code: "IL",
    country: "Izrael",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "IM",
    country: "Wyspa Man",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "IN",
    country: "Indie",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "IO",
    country: "Brytyjskie Terytorium Oceanu Indyjskiego",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "IQ",
    country: "Irak",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "IR",
    country: "Iran",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "IS",
    country: "Islandia",
    vat: null
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
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "RESTAURANTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 4,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 4,
          rateType: "E_BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 4,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 4,
          rateType: "MEDICAL" as TaxRateType
        }
      ],
      standardRate: 22
    }
  },
  {
    __typename: "CountryDisplay",
    code: "JE",
    country: "Jersey",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "JM",
    country: "Jamajka",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "JO",
    country: "Jordania",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "JP",
    country: "Japonia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "KE",
    country: "Kenia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "KG",
    country: "Kirgistan",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "KH",
    country: "Kambodża",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "KI",
    country: "Kiribati",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "KM",
    country: "Komory",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "KN",
    country: "Saint Kitts i Nevis",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "KP",
    country: "Korea Północna",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "KR",
    country: "Korea Południowa",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "KW",
    country: "Kuwejt",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "KY",
    country: "Kajmany",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "KZ",
    country: "Kazachstan",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "LA",
    country: "Laos",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "LB",
    country: "Liban",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "LC",
    country: "Saint Lucia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "LI",
    country: "Liechtenstein",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "LK",
    country: "Sri Lanka",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "LR",
    country: "Liberia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "LS",
    country: "Lesotho",
    vat: null
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
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "BOOKS" as TaxRateType
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
          rateType: "ADVERTISING" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 14,
          rateType: "DOMESTIC_FUEL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 14,
          rateType: "WINE" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "ADMISSION_TO_SPORTING_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "E_BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 3,
          rateType: "RESTAURANTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "BIKES" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "DOMESTIC_SERVICES" as TaxRateType
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
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 12,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 12,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 12,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 12,
          rateType: "PHARMACEUTICALS" as TaxRateType
        }
      ],
      standardRate: 21
    }
  },
  {
    __typename: "CountryDisplay",
    code: "LY",
    country: "Libia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MA",
    country: "Maroko",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MC",
    country: "Monako",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MD",
    country: "Mołdawia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "ME",
    country: "Czarnogóra",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MF",
    country: "Saint-Martin",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MG",
    country: "Madagaskar",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MH",
    country: "Wyspy Marshalla",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MK",
    country: "Macedonia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "ML",
    country: "Mali",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MM",
    country: "Mjanma",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MN",
    country: "Mongolia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MO",
    country: "Makau",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MP",
    country: "Mariany Północne",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MQ",
    country: "Martynika",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MR",
    country: "Mauretania",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MS",
    country: "Montserrat",
    vat: null
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
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 0,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "E_BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 5,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 7,
          rateType: "HOTELS" as TaxRateType
        }
      ],
      standardRate: 18
    }
  },
  {
    __typename: "CountryDisplay",
    code: "MU",
    country: "Mauritius",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MV",
    country: "Malediwy",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MW",
    country: "Malawi",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MX",
    country: "Meksyk",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MY",
    country: "Malezja",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "MZ",
    country: "Mozambik",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "NA",
    country: "Namibia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "NC",
    country: "Nowa Kaledonia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "NE",
    country: "Niger",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "NF",
    country: "Norfolk",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "NG",
    country: "Nigeria",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "NI",
    country: "Nikaragua",
    vat: null
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
          rateType: "ACCOMMODATION" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "PHARMACEUTICALS" as TaxRateType
        }
      ],
      standardRate: 21
    }
  },
  {
    __typename: "CountryDisplay",
    code: "NO",
    country: "Norwegia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "NP",
    country: "Nepal",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "NR",
    country: "Nauru",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "NU",
    country: "Niue",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "NZ",
    country: "Nowa Zelandia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "OM",
    country: "Oman",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "PA",
    country: "Panama",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "PE",
    country: "Peru",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "PF",
    country: "Polinezja Francuska",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "PG",
    country: "Papua-Nowa Gwinea",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "PH",
    country: "Filipiny",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "PK",
    country: "Pakistan",
    vat: null
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
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "ADMISSION_TO_SPORTING_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "PHARMACEUTICALS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 8,
          rateType: "RESTAURANTS" as TaxRateType
        }
      ],
      standardRate: 23
    }
  },
  {
    __typename: "CountryDisplay",
    code: "PM",
    country: "Saint-Pierre i Miquelon",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "PN",
    country: "Pitcairn",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "PR",
    country: "Portoryko",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "PS",
    country: "Palestyna",
    vat: null
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
          rateType: "AGRICULTURAL_SUPPLIES" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "PASSENGER_TRANSPORT" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "PHARMACEUTICALS" as TaxRateType
        }
      ],
      standardRate: 23
    }
  },
  {
    __typename: "CountryDisplay",
    code: "PW",
    country: "Palau",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "PY",
    country: "Paragwaj",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "QA",
    country: "Katar",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "RE",
    country: "Reunion",
    vat: null
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
          rateType: "SOCIAL_HOUSING" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9,
          rateType: "PHARMACEUTICALS" as TaxRateType
        }
      ],
      standardRate: 19
    }
  },
  {
    __typename: "CountryDisplay",
    code: "RS",
    country: "Serbia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "RU",
    country: "Rosja",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "RW",
    country: "Rwanda",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SA",
    country: "Arabia Saudyjska",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SB",
    country: "Wyspy Salomona",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SC",
    country: "Seszele",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SD",
    country: "Sudan",
    vat: null
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
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 6,
          rateType: "BOOKS" as TaxRateType
        }
      ],
      standardRate: 25
    }
  },
  {
    __typename: "CountryDisplay",
    code: "SG",
    country: "Singapur",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SH",
    country: "Wyspa Świętej Heleny, Wyspa Wniebowstąpienia i Tristan da Cunha",
    vat: null
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
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "ADMISSION_TO_SPORTING_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "HOTELS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "NEWSPAPERS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 9.5,
          rateType: "PHARMACEUTICALS" as TaxRateType
        }
      ],
      standardRate: 22
    }
  },
  {
    __typename: "CountryDisplay",
    code: "SJ",
    country: "Svalbard i Jan Mayen",
    vat: null
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
          rateType: "ADMISSION_TO_CULTURAL_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "ADMISSION_TO_ENTERTAINMENT_EVENTS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "BOOKS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "FOODSTUFFS" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "MEDICAL" as TaxRateType
        },
        {
          __typename: "ReducedRate",
          rate: 10,
          rateType: "PHARMACEUTICALS" as TaxRateType
        }
      ],
      standardRate: 20
    }
  },
  {
    __typename: "CountryDisplay",
    code: "SL",
    country: "Sierra Leone",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SM",
    country: "San Marino",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SN",
    country: "Senegal",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SO",
    country: "Somalia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SR",
    country: "Surinam",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SS",
    country: "Sudan Południowy",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "ST",
    country: "Wyspy Świętego Tomasza i Książęca",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SV",
    country: "Salwador",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SX",
    country: "Sint Maarten",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SY",
    country: "Syria",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "SZ",
    country: "Suazi",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TC",
    country: "Turks i Caicos",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TD",
    country: "Czad",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TF",
    country: "Francuskie Terytoria Południowe i Antarktyczne",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TG",
    country: "Togo",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TH",
    country: "Tajlandia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TJ",
    country: "Tadżykistan",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TK",
    country: "Tokelau",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TL",
    country: "Timor Wschodni",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TM",
    country: "Turkmenistan",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TN",
    country: "Tunezja",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TO",
    country: "Tonga",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TR",
    country: "Turcja",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TT",
    country: "Trynidad i Tobago",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TV",
    country: "Tuvalu",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TW",
    country: "Tajwan",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "TZ",
    country: "Tanzania",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "UA",
    country: "Ukraina",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "UG",
    country: "Uganda",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "UM",
    country: "Dalekie Wyspy Mniejsze Stanów Zjednoczonych",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "US",
    country: "Stany Zjednoczone Ameryki",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "UY",
    country: "Urugwaj",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "UZ",
    country: "Uzbekistan",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "VA",
    country: "Watykan",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "VC",
    country: "Saint Vincent i Grenadyny",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "VE",
    country: "Wenezuela",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "VG",
    country: "Brytyjskie Wyspy Dziewicze",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "VI",
    country: "Wyspy Dziewicze Stanów Zjednoczonych",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "VN",
    country: "Wietnam",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "VU",
    country: "Vanuatu",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "WF",
    country: "Wallis i Futuna",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "WS",
    country: "Samoa",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "YE",
    country: "Jemen",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "YT",
    country: "Majotta",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "ZA",
    country: "Republika Południowej Afryki",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "ZM",
    country: "Zambia",
    vat: null
  },
  {
    __typename: "CountryDisplay",
    code: "ZW",
    country: "Zimbabwe",
    vat: null
  }
].filter(country => country.vat);
