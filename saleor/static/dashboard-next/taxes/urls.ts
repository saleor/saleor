import * as urlJoin from "url-join";

export const taxSection = "/taxes/";

export const countryListPath = taxSection;
export const countryListUrl = taxSection;

export const countryTaxRatesPath = (code: string) => urlJoin(taxSection, code);
export const countryTaxRatesUrl = countryTaxRatesPath;
