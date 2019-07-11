import * as braintree from "braintree-web";

export interface PaymentData {
  lastDigits: string;
  ccType: string;
  token: string;
}

export interface ICardInputs {
  ccCsc: string | null;
  ccExp: string | null;
  ccNumber: string | null;
}

export type CardError = { field?: string; message: string } | null;

export interface ICardErrors {
  cvv: CardError;
  expirationMonth: CardError;
  expirationYear: CardError;
  number: CardError;
}

export interface ErrorData {
  fieldErrors: ICardErrors;
  nonFieldError?: string;
}
export interface IPaymentCardError {
  code: string;
  field: string;
  message: string;
}

export const braintreePayment = (paymentClientToken: string, creditCard: any) =>
  new Promise<PaymentData | ErrorData[]>((resolve, reject) => {
    braintree.client.create(
      {
        authorization: paymentClientToken,
      },
      (_err, client) => {
        client.request(
          {
            data: { creditCard },
            endpoint: "payment_methods/credit_cards",
            method: "post",
          },
          (error, response) => {
            if (error) {
              if (error.details.originalError.fieldErrors.length > 0) {
                error.details.originalError.fieldErrors.map(error => {
                  if (error.field === "creditCard") {
                    reject(error.fieldErrors);
                  }
                });
              }
            } else {
              const lastDigits = response.creditCards[0].details.lastFour;
              const ccType = response.creditCards[0].details.cardType;
              const token = response.creditCards[0].nonce;
              resolve({ lastDigits, ccType, token });
            }
          }
        );
      }
    );
  });
