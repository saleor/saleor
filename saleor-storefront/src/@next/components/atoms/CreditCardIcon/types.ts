export type CCProviders =
  | "visa"
  | "maestro"
  | "mastercard"
  | "jcb"
  | "discover"
  | "amex";

export interface IProps {
  provider: CCProviders;
}
