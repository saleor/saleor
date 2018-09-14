export interface AddressTypeInput {
  city: string;
  cityArea?: string;
  companyName?: string;
  country: string;
  countryArea?: string;
  firstName: string;
  lastName: string;
  phone: string;
  postalCode: string;
  streetAddress1: string;
  streetAddress2?: string;
}
export interface AddressType extends AddressTypeInput {
  id: string;
}
