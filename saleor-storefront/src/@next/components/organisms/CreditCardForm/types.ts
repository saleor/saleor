import { Omit } from "@utils/tsUtils";
import {
  CardError,
  ICardErrors,
  ICardInputs
} from "src/core/payments/braintree";

interface ILabelsText {
  ccCsc: string;
  ccExp: string;
  ccNumber: string;
}
export interface IFormikProps {
  handleChange: (e: React.ChangeEvent) => void;
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
}
export interface IProps {
  formRef?: React.RefObject<HTMLFormElement>;
  cardErrors: ICardErrors;
  labelsText: ILabelsText;
  handleSubmit: (formData: ICardInputs) => void;
  disabled: boolean;
}

export type CardErrors = CardError[] | null[];

export interface ICustomInputProps {
  errors: CardErrors;
  label: string;
}

export type PropsWithFormik = Omit<IProps, "handleSubmit"> & IFormikProps;
