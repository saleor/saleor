import { CCProviders } from "@components/atoms";

export interface IProps {
  nameOnCard: string;
  expirationDate: string;
  last4Digits: number;
  provider: CCProviders;
  onRemove: () => void;
  onEdit: () => void;
}
