export interface IFormError {
  message: string;
  field?: string;
}

export interface IProps {
  errors?: IFormError[];
}
