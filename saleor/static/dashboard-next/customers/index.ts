export interface AddressTypeInput {
  city: string;
  cityArea?: string;
  companyName?: string;
  country: string;
  countryArea?: string;
  firstName: string;
  lastName: string;
  phone_prefix: string;
  phone_number: string;
  postalCode: string;
  streetAddress_1: string;
  streetAddress_2?: string;
}
export interface AddressType extends AddressTypeInput {
  id: string;
}
