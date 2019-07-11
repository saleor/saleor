import { shallow } from "enzyme";
import "jest-styled-components";
import React from "react";
import NumberFormat, { NumberFormatProps } from "react-number-format";

import { TextField } from "@components/molecules";
import { CreditCardFormContent as CreditCardForm } from "./CreditCardFormContent";
import * as S from "./styles";
import { ICustomInputProps, PropsWithFormik } from "./types";

describe("<CreditCardForm />", () => {
  const CARD_TEXT = {
    ccCsc: "CVC",
    ccExp: "Expiry Date",
    ccNumber: "Number",
  };

  const DEFAULT_PROPS = {
    cardErrors: {
      cvv: null,
      expirationMonth: null,
      expirationYear: null,
      number: null,
    },
    disabled: false,
    handleChange: jest.fn(),
    handleSubmit: jest.fn(),
    labelsText: CARD_TEXT,
  };

  const renderCreditCardForm = (props: PropsWithFormik) =>
    shallow(<CreditCardForm {...props} />);

  it("exists", () => {
    const creditCardForm = renderCreditCardForm(DEFAULT_PROPS);

    expect(creditCardForm.exists()).toEqual(true);
  });

  it("should render <S.PaymentForm /> with `onSubmit` prop", () => {
    const form = renderCreditCardForm(DEFAULT_PROPS).find(S.PaymentForm);

    expect(form.exists()).toEqual(true);
    expect(form.prop("onSubmit")).toEqual(DEFAULT_PROPS.handleSubmit);
  });

  describe("<S.PaymentInput /> ", () => {
    it("should render", () => {
      const inputs = renderCreditCardForm(DEFAULT_PROPS).find(S.PaymentInput);

      expect(inputs).toHaveLength(3);
    });
  });

  describe("<NumberFormat /> ", () => {
    it("should pass [disabled, customInput, handleChange, label, onChange] props", () => {
      const numberInputProps = renderCreditCardForm(DEFAULT_PROPS)
        .find(NumberFormat)
        .at(0)
        .props() as ICustomInputProps & NumberFormatProps;

      expect(numberInputProps.disabled).toEqual(DEFAULT_PROPS.disabled);
      expect(numberInputProps.customInput).toEqual(TextField);
      expect(numberInputProps.label).toEqual(CARD_TEXT.ccNumber);
      expect(numberInputProps.onChange).toEqual(DEFAULT_PROPS.handleChange);
    });

    it("should pass `errors` list props if error occurs", () => {
      const CARD_ERRORS = {
        cvv: null,
        expirationMonth: null,
        expirationYear: {
          field: "expirationYear",
          message: "Expiration year is invalid",
        },
        number: { field: "number", message: "Wrong number" },
      };

      const inputs = renderCreditCardForm({
        ...DEFAULT_PROPS,
        cardErrors: CARD_ERRORS,
      }).find(NumberFormat);

      expect(inputs.at(1).prop("errors")).toEqual([]);
      expect(inputs.at(0).prop("errors")).toEqual([CARD_ERRORS.number]);
      expect(inputs.at(2).prop("errors")).toEqual([CARD_ERRORS.expirationYear]);
    });
  });
});
