export interface AddressTypeInput {
  city: string;
  cityArea?: string;
  companyName?: string;
  country: {
    label: string;
    value: string;
  };
  countryArea?: string;
  firstName: string;
  lastName: string;
  phone: string;
  postalCode: string;
  streetAddress1: string;
  streetAddress2?: string;
}
export interface AddressType {
  id: string;
  city: string;
  cityArea?: string;
  companyName?: string;
  country: {
    code: string;
    country: string;
  };
  countryArea?: string;
  firstName: string;
  lastName: string;
  phone: string;
  postalCode: string;
  streetAddress1: string;
  streetAddress2?: string;
}
