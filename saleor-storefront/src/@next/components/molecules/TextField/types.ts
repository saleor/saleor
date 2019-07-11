interface IFormError {
  message: string;
  field?: string;
}

export interface IProps extends React.InputHTMLAttributes<HTMLInputElement> {
  errors?: IFormError[];
  helpText?: string;
  label?: string;
  contentLeft?: React.ReactNode;
  contentRight?: React.ReactNode;
  value: string | number;
}
