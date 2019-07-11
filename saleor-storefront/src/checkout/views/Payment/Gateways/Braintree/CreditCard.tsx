import React from "react";

import { CreditCardForm } from "@components/organisms";
import { GatewaysEnum } from "../../../../../../types/globalTypes";

import {
  braintreePayment,
  ErrorData,
  IPaymentCardError,
  PaymentData
} from "../../../../../core/payments/braintree";
import { maybe, removeEmptySpaces } from "../../../../../core/utils";
import { ProviderProps } from "../../View";

const INITIAL_CARD_ERROR_STATE = {
  fieldErrors: {
    cvv: null,
    expirationMonth: null,
    expirationYear: null,
    number: null,
  },
  nonFieldError: "",
};

const CreditCard = ({
  checkout: {
    update,
    checkout: {
      billingAddress: { postalCode },
    },
  },
  formRef,
  loading,
  setLoadingState,
  paymentClientToken,
  processPayment,
}: ProviderProps) => {
  {
    const [cardErrors, setCardErrors] = React.useState<ErrorData>(
      INITIAL_CARD_ERROR_STATE
    );

    const setCardErrorsHelper = (errors: IPaymentCardError[]) =>
      errors.map(({ field, message }: IPaymentCardError) =>
        setCardErrors(({ fieldErrors }) => ({
          fieldErrors: {
            ...fieldErrors,
            [field]: { field, message },
          },
        }))
      );

    const tokenizeCcCard = async creditCard => {
      setCardErrors(INITIAL_CARD_ERROR_STATE);
      try {
        const cardData = (await braintreePayment(
          paymentClientToken,
          creditCard
        )) as PaymentData;
        await update({ cardData });
        return cardData.token;
      } catch (errors) {
        setCardErrorsHelper(errors);
        return null;
      }
    };

    const handleSubmit = async formData => {
      setLoadingState(true);
      const creditCard = {
        billingAddress: { postalCode },
        cvv: removeEmptySpaces(maybe(() => formData.ccCsc, "")),
        expirationDate: removeEmptySpaces(maybe(() => formData.ccExp, "")),
        number: removeEmptySpaces(maybe(() => formData.ccNumber, "")),
      };
      const token = await tokenizeCcCard(creditCard);
      processPayment(token, GatewaysEnum.BRAINTREE);
      setLoadingState(false);
    };

    return (
      <CreditCardForm
        formRef={formRef}
        cardErrors={cardErrors.fieldErrors}
        labelsText={{
          ccCsc: "CVC",
          ccExp: "ExpiryDate",
          ccNumber: "Number",
        }}
        disabled={loading}
        handleSubmit={handleSubmit}
      />
    );
  }
};

export default CreditCard;
