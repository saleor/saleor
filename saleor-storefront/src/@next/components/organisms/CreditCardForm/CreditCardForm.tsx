import { Formik } from "formik";
import React from "react";

import { CreditCardFormContent } from "./CreditCardFormContent";
import { IProps } from "./types";

const INITIAL_CARD_VALUES_STATE = {
  ccCsc: "",
  ccExp: "",
  ccNumber: "",
};

export const CreditCardForm: React.FC<IProps> = ({
  handleSubmit,
  ...props
}: IProps) => {
  return (
    <Formik
      initialValues={INITIAL_CARD_VALUES_STATE}
      onSubmit={(values, { setSubmitting }) => {
        handleSubmit(values);
        setSubmitting(false);
      }}
    >
      {({ handleChange, handleSubmit }) => (
        <CreditCardFormContent
          handleChange={handleChange}
          handleSubmit={handleSubmit}
          {...props}
        />
      )}
    </Formik>
  );
};
